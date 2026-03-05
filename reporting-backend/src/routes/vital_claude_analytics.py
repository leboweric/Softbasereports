"""
VITAL Worklife – Claude AI Analytics Routes
Provides Anthropic Claude-powered analytics endpoints for the VITAL Worklife organisation.

Endpoints
---------
POST /api/vital/claude/analyze-cases
    Analyse aggregated, de-identified case statistics.

POST /api/vital/claude/analyze-sentiment
    Deep-dive sentiment and theme analysis on satisfaction comments.

POST /api/vital/claude/ask
    Free-form analytics prompt (admin only).

GET  /api/vital/claude/health
    Check that the Anthropic API key is configured and reachable.
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging

from src.services.cache_service import cache_service

logger = logging.getLogger(__name__)

vital_claude_bp = Blueprint("vital_claude", __name__)

# Cache TTL for Claude responses (15 minutes – same as other VITAL endpoints)
CACHE_TTL = 900


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_service():
    """Lazy-load the AnthropicService singleton."""
    from src.services.anthropic_service import get_anthropic_service
    return get_anthropic_service()


def _is_vital_user() -> bool:
    """Return True if the authenticated user belongs to the VITAL organisation."""
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
    """Return True if the user is a VITAL admin/owner."""
    try:
        from src.models.user import User, Organization
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user or not user.organization_id:
            return False
        org = Organization.query.get(user.organization_id)
        if not org or "vital" not in org.name.lower():
            return False
        admin_roles = {"admin", "hr_admin", "owner", "super_admin"}
        return bool(user.role and user.role.lower() in admin_roles)
    except Exception as exc:
        logger.error("_is_vital_admin error: %s", exc)
        return False


# ---------------------------------------------------------------------------
# Health check (no auth required – mirrors azure-sql pattern)
# ---------------------------------------------------------------------------

@vital_claude_bp.route("/api/vital/claude/health", methods=["GET"])
def claude_health():
    """Verify the Anthropic API key is configured and the SDK is installed."""
    try:
        import os
        key = os.getenv("ANTHROPIC_API_KEY", "")
        if not key:
            return jsonify({
                "status": "not_configured",
                "error": "ANTHROPIC_API_KEY environment variable is not set."
            }), 503

        # Attempt a minimal SDK import to confirm the package is installed
        import anthropic  # noqa: F401
        return jsonify({
            "status": "healthy",
            "message": "Anthropic Claude integration is configured.",
            "key_suffix": f"...{key[-6:]}"
        })
    except ImportError:
        return jsonify({
            "status": "unhealthy",
            "error": "anthropic package not installed. Add anthropic>=0.25.0 to requirements.txt."
        }), 503
    except Exception as exc:
        return jsonify({"status": "error", "error": str(exc)}), 500


# ---------------------------------------------------------------------------
# POST /api/vital/claude/analyze-cases
# ---------------------------------------------------------------------------

@vital_claude_bp.route("/api/vital/claude/analyze-cases", methods=["POST"])
@jwt_required()
def analyze_cases():
    """
    Analyse aggregated, de-identified VITAL case statistics with Claude.

    Request body (JSON)
    -------------------
    {
        "stats": { ...aggregated metrics dict... },
        "refresh": false   // optional – bypass cache
    }

    The `stats` object should contain only pre-aggregated, de-identified numbers
    (counts, averages, distributions).  Never send raw case records.
    """
    if not _is_vital_user():
        return jsonify({"error": "Access restricted to VITAL Worklife users."}), 403

    body = request.get_json(silent=True) or {}
    stats = body.get("stats")
    refresh = body.get("refresh", False)

    if not stats or not isinstance(stats, dict):
        return jsonify({"error": "'stats' must be a non-empty JSON object."}), 400

    # Simple cache key based on sorted JSON representation
    import hashlib, json
    cache_key = "vital_claude_cases_" + hashlib.md5(
        json.dumps(stats, sort_keys=True, default=str).encode()
    ).hexdigest()

    if not refresh:
        cached = cache_service.get(cache_key)
        if cached:
            return jsonify({**cached, "cached": True})

    try:
        service = _get_service()
        result = service.analyze_case_data(stats)
    except ValueError as exc:
        # API key not configured
        return jsonify({"error": str(exc)}), 503
    except ImportError as exc:
        return jsonify({"error": str(exc)}), 503
    except Exception as exc:
        logger.error("analyze_cases error: %s", exc)
        return jsonify({"error": "Claude analysis failed.", "detail": str(exc)}), 500

    if not result["success"]:
        return jsonify({"error": result.get("error", "Unknown error from Claude.")}), 500

    payload = {
        "insights": result.get("insights", {}),
        "model": result.get("model"),
        "tokens_used": result.get("input_tokens", 0) + result.get("output_tokens", 0),
        "cached": False,
    }
    cache_service.set(cache_key, payload, ttl=CACHE_TTL)
    return jsonify(payload)


# ---------------------------------------------------------------------------
# POST /api/vital/claude/analyze-sentiment
# ---------------------------------------------------------------------------

@vital_claude_bp.route("/api/vital/claude/analyze-sentiment", methods=["POST"])
@jwt_required()
def analyze_sentiment():
    """
    Deep-dive sentiment and theme analysis on de-identified satisfaction comments.

    Request body (JSON)
    -------------------
    {
        "comments": ["comment text 1", "comment text 2", ...],
        "context":  { "period": "Q1 2026", "organisation": "Acme Corp" },  // optional
        "refresh":  false   // optional – bypass cache
    }

    Maximum 200 comments per request (excess are silently truncated).
    """
    if not _is_vital_user():
        return jsonify({"error": "Access restricted to VITAL Worklife users."}), 403

    body = request.get_json(silent=True) or {}
    comments = body.get("comments", [])
    context = body.get("context")
    refresh = body.get("refresh", False)

    if not comments or not isinstance(comments, list):
        return jsonify({"error": "'comments' must be a non-empty list of strings."}), 400

    # Truncate and sanitise
    comments = [str(c) for c in comments[:200] if c]

    import hashlib, json
    cache_key = "vital_claude_sentiment_" + hashlib.md5(
        json.dumps({"comments": comments, "context": context}, sort_keys=True).encode()
    ).hexdigest()

    if not refresh:
        cached = cache_service.get(cache_key)
        if cached:
            return jsonify({**cached, "cached": True})

    try:
        service = _get_service()
        result = service.analyze_satisfaction_comments(comments, context)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 503
    except ImportError as exc:
        return jsonify({"error": str(exc)}), 503
    except Exception as exc:
        logger.error("analyze_sentiment error: %s", exc)
        return jsonify({"error": "Claude sentiment analysis failed.", "detail": str(exc)}), 500

    if not result["success"]:
        return jsonify({"error": result.get("error", "Unknown error from Claude.")}), 500

    payload = {
        "insights": result.get("insights", {}),
        "model": result.get("model"),
        "comments_analyzed": len(comments),
        "tokens_used": result.get("input_tokens", 0) + result.get("output_tokens", 0),
        "cached": False,
    }
    cache_service.set(cache_key, payload, ttl=CACHE_TTL)
    return jsonify(payload)


# ---------------------------------------------------------------------------
# POST /api/vital/claude/ask  (admin only)
# ---------------------------------------------------------------------------

@vital_claude_bp.route("/api/vital/claude/ask", methods=["POST"])
@jwt_required()
def free_form_ask():
    """
    Free-form analytics prompt – VITAL admin only.

    Request body (JSON)
    -------------------
    {
        "prompt": "What are the key drivers of low NPS scores this quarter?",
        "data":   { ...optional supporting data dict... }
    }
    """
    if not _is_vital_admin():
        return jsonify({"error": "Access restricted to VITAL admins."}), 403

    body = request.get_json(silent=True) or {}
    prompt = body.get("prompt", "").strip()
    data = body.get("data")

    if not prompt:
        return jsonify({"error": "'prompt' is required."}), 400

    try:
        service = _get_service()
        result = service.free_form_analytics(prompt, data)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 503
    except ImportError as exc:
        return jsonify({"error": str(exc)}), 503
    except Exception as exc:
        logger.error("free_form_ask error: %s", exc)
        return jsonify({"error": "Claude request failed.", "detail": str(exc)}), 500

    if not result["success"]:
        return jsonify({"error": result.get("error", "Unknown error from Claude.")}), 500

    return jsonify({
        "response": result.get("content", ""),
        "model": result.get("model"),
        "tokens_used": result.get("input_tokens", 0) + result.get("output_tokens", 0),
    })
