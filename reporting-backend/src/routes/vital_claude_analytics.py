"""
VITAL Worklife – Claude Enterprise Analytics Routes
Proxies the Claude.ai Analytics API to expose usage/adoption data
securely (API key stays server-side).

Endpoints
---------
GET  /api/vital/claude-analytics/health
    Check that CLAUDE_ANALYTICS_API_KEY is configured.

GET  /api/vital/claude-analytics/dashboard
    Full adoption dashboard: summaries, top projects, top users, skills.
    Query params:
      days (int, default 30) – how many days of summary history to return
      refresh (bool)         – bypass Redis cache

GET  /api/vital/claude-analytics/summaries
    Raw daily/weekly/monthly active user summaries.
    Query params: starting_date (YYYY-MM-DD), ending_date (YYYY-MM-DD, optional)

GET  /api/vital/claude-analytics/users
    Per-user activity for a single day.
    Query params: date (YYYY-MM-DD)

GET  /api/vital/claude-analytics/projects
    Chat project usage for a single day.
    Query params: date (YYYY-MM-DD)
"""

import os
from datetime import date, timedelta
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging

from src.services.cache_service import cache_service

logger = logging.getLogger(__name__)

vital_claude_analytics_bp = Blueprint("vital_claude_analytics", __name__)

# Cache TTL – 15 minutes (data has a 3-day delay so freshness isn't critical)
CACHE_TTL = 900


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_service():
    from src.services.claude_analytics_service import get_claude_analytics_service
    return get_claude_analytics_service()


def _is_vital_user() -> bool:
    try:
        from src.models.user import User, Organization
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user or not user.organization_id:
            return False
        org = Organization.query.get(user.organization_id)
        return bool(org and org.name and "vital" in org.name.lower())
    except Exception as exc:
        logger.error("_is_vital_user error: %s", exc)
        return False


def _is_vital_admin() -> bool:
    try:
        from src.models.user import User, Organization
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user or not user.organization_id:
            return False
        org = Organization.query.get(user.organization_id)
        if not org or "vital" not in org.name.lower():
            return False
        return bool(user.role and user.role.lower() in {"admin", "hr_admin", "owner", "super_admin"})
    except Exception as exc:
        logger.error("_is_vital_admin error: %s", exc)
        return False


def _safe_date(param: str, fallback_days_ago: int) -> str:
    """Return a validated date string or a safe fallback."""
    if param:
        try:
            date.fromisoformat(param)
            return param
        except ValueError:
            pass
    return (date.today() - timedelta(days=fallback_days_ago)).isoformat()


# ---------------------------------------------------------------------------
# Health check (no auth)
# ---------------------------------------------------------------------------

@vital_claude_analytics_bp.route("/api/vital/claude-analytics/health", methods=["GET"])
def claude_analytics_health():
    key = os.getenv("CLAUDE_ANALYTICS_API_KEY", "")
    if not key:
        return jsonify({
            "status": "not_configured",
            "error": (
                "CLAUDE_ANALYTICS_API_KEY is not set. "
                "Create an Analytics API key at claude.ai/analytics/api-keys "
                "and add it to Railway environment variables."
            )
        }), 503
    return jsonify({
        "status": "healthy",
        "message": "Claude Analytics API key is configured.",
        "key_suffix": f"...{key[-6:]}",
    })


# ---------------------------------------------------------------------------
# Dashboard (full aggregated payload)
# ---------------------------------------------------------------------------

@vital_claude_analytics_bp.route("/api/vital/claude-analytics/dashboard", methods=["GET"])
@jwt_required()
def claude_analytics_dashboard():
    """
    Returns the full adoption dashboard payload.
    Query params: days (int, default 30), refresh (bool)
    """
    if not _is_vital_user():
        return jsonify({"error": "Access restricted to VITAL Worklife users."}), 403

    days = request.args.get("days", 30, type=int)
    refresh = request.args.get("refresh", "false").lower() == "true"

    cache_key = f"vital_claude_analytics_dashboard_{days}"

    if not refresh:
        cached = cache_service.get(cache_key)
        if cached:
            return jsonify({**cached, "cached": True})

    try:
        service = _get_service()
        data = service.get_dashboard_data(days=days)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 503
    except Exception as exc:
        logger.error("claude_analytics_dashboard error: %s", exc)
        return jsonify({"error": "Failed to fetch Claude analytics.", "detail": str(exc)}), 500

    data["cached"] = False
    cache_service.set(cache_key, data, ttl=CACHE_TTL)
    return jsonify(data)


# ---------------------------------------------------------------------------
# Raw summaries
# ---------------------------------------------------------------------------

@vital_claude_analytics_bp.route("/api/vital/claude-analytics/summaries", methods=["GET"])
@jwt_required()
def claude_analytics_summaries():
    """
    Query params: starting_date (YYYY-MM-DD, required), ending_date (YYYY-MM-DD, optional)
    """
    if not _is_vital_user():
        return jsonify({"error": "Access restricted to VITAL Worklife users."}), 403

    starting_date = _safe_date(request.args.get("starting_date"), 34)
    ending_date = request.args.get("ending_date")

    try:
        service = _get_service()
        data = service.get_summaries(starting_date, ending_date)
        return jsonify(data)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 503
    except Exception as exc:
        logger.error("claude_analytics_summaries error: %s", exc)
        return jsonify({"error": str(exc)}), 500


# ---------------------------------------------------------------------------
# Per-user activity
# ---------------------------------------------------------------------------

@vital_claude_analytics_bp.route("/api/vital/claude-analytics/users", methods=["GET"])
@jwt_required()
def claude_analytics_users():
    """
    Query params: date (YYYY-MM-DD, defaults to 4 days ago)
    Admin only – contains email addresses.
    """
    if not _is_vital_admin():
        return jsonify({"error": "Access restricted to VITAL admins."}), 403

    date_str = _safe_date(request.args.get("date"), 4)

    try:
        service = _get_service()
        data = service.get_user_activity(date_str, limit=1000)
        return jsonify(data)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 503
    except Exception as exc:
        logger.error("claude_analytics_users error: %s", exc)
        return jsonify({"error": str(exc)}), 500


# ---------------------------------------------------------------------------
# Chat project usage
# ---------------------------------------------------------------------------

@vital_claude_analytics_bp.route("/api/vital/claude-analytics/projects", methods=["GET"])
@jwt_required()
def claude_analytics_projects():
    """
    Query params: date (YYYY-MM-DD, defaults to 4 days ago)
    """
    if not _is_vital_user():
        return jsonify({"error": "Access restricted to VITAL Worklife users."}), 403

    date_str = _safe_date(request.args.get("date"), 4)

    try:
        service = _get_service()
        data = service.get_project_usage(date_str, limit=50)
        return jsonify(data)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 503
    except Exception as exc:
        logger.error("claude_analytics_projects error: %s", exc)
        return jsonify({"error": str(exc)}), 500
