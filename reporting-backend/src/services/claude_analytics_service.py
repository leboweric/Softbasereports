"""
Claude Enterprise Analytics Service
Fetches usage and adoption metrics from the Claude Enterprise Analytics API.
https://api.anthropic.com/v1/organizations/analytics/

API key is read from CLAUDE_ANALYTICS_API_KEY environment variable.
This is a separate key from ANTHROPIC_API_KEY — it must have the read:analytics scope
and is created at claude.ai/analytics/api-keys.
"""

import os
import logging
import requests
from datetime import datetime, timedelta, date

logger = logging.getLogger(__name__)

BASE_URL = "https://api.anthropic.com/v1/organizations/analytics"


class ClaudeAnalyticsService:
    """
    Thin wrapper around the Claude Enterprise Analytics REST API.
    All methods return parsed JSON dicts or raise on error.
    """

    def __init__(self):
        self.api_key = os.getenv("CLAUDE_ANALYTICS_API_KEY")
        if not self.api_key:
            raise ValueError(
                "CLAUDE_ANALYTICS_API_KEY environment variable is not set. "
                "Create an Analytics API key at claude.ai/analytics/api-keys "
                "and add it to your Railway environment variables."
            )
        self.headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
        }

    def _get(self, path: str, params: dict) -> dict:
        """Make an authenticated GET request and return parsed JSON."""
        url = f"{BASE_URL}{path}"
        resp = requests.get(url, headers=self.headers, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()

    # ------------------------------------------------------------------
    # 1. Activity Summary  (daily/weekly/monthly active users, seat count)
    # ------------------------------------------------------------------

    def get_summaries(self, starting_date: str, ending_date: str = None) -> dict:
        """
        GET /v1/organizations/analytics/summaries

        Returns daily active users, weekly/monthly rolling counts, seat count,
        and pending invites for each day in the date range.

        Parameters
        ----------
        starting_date : str   YYYY-MM-DD  (max 31-day range, 3-day data delay)
        ending_date   : str   YYYY-MM-DD  optional, exclusive
        """
        params = {"starting_date": starting_date}
        if ending_date:
            params["ending_date"] = ending_date
        return self._get("/summaries", params)

    # ------------------------------------------------------------------
    # 2. Per-user activity
    # ------------------------------------------------------------------

    def get_user_activity(self, date_str: str, limit: int = 1000, page: str = None) -> dict:
        """
        GET /v1/organizations/analytics/users

        Returns per-user engagement metrics for a single day.
        """
        params = {"date": date_str, "limit": limit}
        if page:
            params["page"] = page
        return self._get("/users", params)

    def get_all_user_activity(self, date_str: str) -> list:
        """Fetch all pages of user activity for a given date."""
        results = []
        page = None
        while True:
            data = self.get_user_activity(date_str, limit=1000, page=page)
            results.extend(data.get("items", []))
            page = data.get("next_page")
            if not page:
                break
        return results

    # ------------------------------------------------------------------
    # 3. Chat project usage
    # ------------------------------------------------------------------

    def get_project_usage(self, date_str: str, limit: int = 100, page: str = None) -> dict:
        """
        GET /v1/organizations/analytics/apps/chat/projects

        Returns usage data broken down by chat project for a given date.
        """
        params = {"date": date_str, "limit": limit}
        if page:
            params["page"] = page
        return self._get("/apps/chat/projects", params)

    # ------------------------------------------------------------------
    # 4. Skill usage
    # ------------------------------------------------------------------

    def get_skill_usage(self, date_str: str, limit: int = 100, page: str = None) -> dict:
        """
        GET /v1/organizations/analytics/skills
        """
        params = {"date": date_str, "limit": limit}
        if page:
            params["page"] = page
        return self._get("/skills", params)

    # ------------------------------------------------------------------
    # Convenience: build the full dashboard payload
    # ------------------------------------------------------------------

    def get_dashboard_data(self, days: int = 30) -> dict:
        """
        Aggregate all data needed for the adoption dashboard.

        Returns a dict with:
          - summaries: list of daily summary objects (last `days` days)
          - latest_summary: most recent day's summary
          - top_projects: list of top chat projects (most recent available day)
          - top_users: top 20 users by message count (most recent available day)
          - skills: skill usage (most recent available day)
        """
        # Data has a 3-day delay — use 4 days ago as the safe "latest" date
        latest_date = date.today() - timedelta(days=4)
        starting_date = latest_date - timedelta(days=days - 1)

        result = {
            "latest_date": latest_date.isoformat(),
            "summaries": [],
            "latest_summary": None,
            "top_projects": [],
            "top_users": [],
            "skills": [],
            "errors": [],
        }

        # --- Summaries ---
        try:
            summary_data = self.get_summaries(
                starting_date=starting_date.isoformat(),
                ending_date=(latest_date + timedelta(days=1)).isoformat(),
            )
            result["summaries"] = summary_data.get("items", [])
            if result["summaries"]:
                result["latest_summary"] = result["summaries"][-1]
        except Exception as exc:
            logger.error("get_summaries error: %s", exc)
            result["errors"].append(f"summaries: {str(exc)}")

        # --- Top projects (latest day) ---
        try:
            proj_data = self.get_project_usage(latest_date.isoformat(), limit=20)
            result["top_projects"] = proj_data.get("items", [])
        except Exception as exc:
            logger.error("get_project_usage error: %s", exc)
            result["errors"].append(f"projects: {str(exc)}")

        # --- Top users by message count (latest day) ---
        try:
            user_data = self.get_user_activity(latest_date.isoformat(), limit=100)
            users = user_data.get("items", [])
            # Sort by chat message count descending
            users.sort(
                key=lambda u: u.get("chat_metrics", {}).get("message_count", 0),
                reverse=True,
            )
            result["top_users"] = users[:20]
        except Exception as exc:
            logger.error("get_user_activity error: %s", exc)
            result["errors"].append(f"users: {str(exc)}")

        # --- Skill usage (latest day) ---
        try:
            skill_data = self.get_skill_usage(latest_date.isoformat(), limit=50)
            result["skills"] = skill_data.get("items", [])
        except Exception as exc:
            logger.error("get_skill_usage error: %s", exc)
            result["errors"].append(f"skills: {str(exc)}")

        return result


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
_service_instance = None


def get_claude_analytics_service() -> ClaudeAnalyticsService:
    global _service_instance
    if _service_instance is None:
        _service_instance = ClaudeAnalyticsService()
    return _service_instance
