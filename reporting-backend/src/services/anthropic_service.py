"""
Anthropic Claude Service
Provides Claude AI-powered analytics for VITAL Worklife.
API key is read from the ANTHROPIC_API_KEY environment variable.
"""

import os
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Lazy-load the anthropic client so the app still starts if the package is
# not yet installed (e.g. during a Railway build before pip install completes).
_anthropic = None


def _get_anthropic():
    """Lazy-load the anthropic package."""
    global _anthropic
    if _anthropic is None:
        try:
            import anthropic as _lib
            _anthropic = _lib
        except ImportError:
            raise ImportError(
                "The 'anthropic' package is not installed. "
                "Add 'anthropic>=0.25.0' to requirements.txt and redeploy."
            )
    return _anthropic


# ---------------------------------------------------------------------------
# Default model – Claude 3.5 Sonnet is the recommended balance of speed/cost.
# Override via ANTHROPIC_MODEL env var if needed.
# ---------------------------------------------------------------------------
DEFAULT_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
MAX_TOKENS = int(os.getenv("ANTHROPIC_MAX_TOKENS", "2048"))


class AnthropicService:
    """
    Thin wrapper around the Anthropic Python SDK.

    Usage
    -----
    service = AnthropicService()
    result  = service.analyze(system_prompt, user_message)
    """

    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable is not set. "
                "Add it to your Railway / .env configuration."
            )
        lib = _get_anthropic()
        self.client = lib.Anthropic(api_key=api_key)
        self.model = DEFAULT_MODEL
        logger.info(
            "AnthropicService initialised (model=%s, key=...%s)",
            self.model,
            api_key[-6:],
        )

    # ------------------------------------------------------------------
    # Core helper
    # ------------------------------------------------------------------

    def analyze(self, system_prompt: str, user_message: str) -> dict:
        """
        Send a single-turn message to Claude and return a structured result.

        Returns
        -------
        {
            "success": bool,
            "content": str,          # raw text from Claude
            "model": str,
            "input_tokens": int,
            "output_tokens": int,
            "error": str | None
        }
        """
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=MAX_TOKENS,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
            )
            content = response.content[0].text if response.content else ""
            return {
                "success": True,
                "content": content,
                "model": response.model,
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                "error": None,
            }
        except Exception as exc:
            logger.error("AnthropicService.analyze error: %s", exc)
            return {
                "success": False,
                "content": "",
                "model": self.model,
                "input_tokens": 0,
                "output_tokens": 0,
                "error": str(exc),
            }

    # ------------------------------------------------------------------
    # VITAL Worklife – Case Data Analytics
    # ------------------------------------------------------------------

    VITAL_SYSTEM_PROMPT = """You are an expert analytics assistant for VITAL Worklife, an Employee
Assistance Programme (EAP) provider. You receive aggregated, de-identified case data and produce
clear, actionable insights for HR and clinical leadership.

Your output must always be valid JSON with the following top-level keys:
{
  "summary":        "<2-3 sentence executive summary>",
  "key_findings":   ["<finding 1>", "<finding 2>", ...],
  "trends":         ["<trend 1>", "<trend 2>", ...],
  "recommendations":["<action 1>", "<action 2>", ...],
  "risk_flags":     ["<flag 1>", ...]   // empty list if none
}

Be concise, evidence-based, and avoid speculation beyond what the data supports.
Do not include PHI or any information that could identify individuals."""

    def analyze_case_data(self, aggregated_stats: dict) -> dict:
        """
        Analyse aggregated VITAL case statistics and return structured insights.

        Parameters
        ----------
        aggregated_stats : dict
            Pre-aggregated, de-identified metrics (counts, averages, distributions).
            Never pass raw case records.

        Returns
        -------
        dict  – merged result from `analyze()` plus a parsed `insights` key.
        """
        user_message = (
            "Please analyse the following aggregated VITAL Worklife case statistics "
            "and provide insights:\n\n"
            + json.dumps(aggregated_stats, indent=2, default=str)
        )

        result = self.analyze(self.VITAL_SYSTEM_PROMPT, user_message)

        # Attempt to parse the JSON insights from Claude's response
        if result["success"]:
            try:
                result["insights"] = json.loads(result["content"])
            except json.JSONDecodeError:
                # Claude occasionally wraps JSON in markdown fences
                import re
                match = re.search(r"\{.*\}", result["content"], re.DOTALL)
                if match:
                    try:
                        result["insights"] = json.loads(match.group())
                    except json.JSONDecodeError:
                        result["insights"] = {"raw": result["content"]}
                else:
                    result["insights"] = {"raw": result["content"]}
        else:
            result["insights"] = {}

        return result

    # ------------------------------------------------------------------
    # VITAL Worklife – Satisfaction / Sentiment Deep-Dive
    # ------------------------------------------------------------------

    SENTIMENT_SYSTEM_PROMPT = """You are a clinical analytics expert for an EAP provider.
You receive batches of de-identified satisfaction comments and produce a structured sentiment
and theme analysis. Output valid JSON only:
{
  "overall_sentiment": "positive|neutral|negative",
  "sentiment_score":   <float -1.0 to 1.0>,
  "top_themes":        [{"theme": "...", "frequency": "high|medium|low", "sentiment": "positive|neutral|negative"}],
  "verbatim_highlights": {
      "positive": ["<quote 1>", "<quote 2>"],
      "negative": ["<quote 1>", "<quote 2>"]
  },
  "recommended_actions": ["<action 1>", "<action 2>"],
  "summary": "<2-3 sentence summary>"
}
Never include any information that could identify an individual."""

    def analyze_satisfaction_comments(self, comments: list[str], context: dict | None = None) -> dict:
        """
        Deep-dive sentiment and theme analysis on a batch of satisfaction comments.

        Parameters
        ----------
        comments : list[str]
            De-identified satisfaction comment strings (max 200 recommended).
        context  : dict, optional
            Extra context such as time period or organisation name.

        Returns
        -------
        dict – merged result from `analyze()` plus a parsed `insights` key.
        """
        payload = {"comments": comments[:200]}  # hard cap to stay within token budget
        if context:
            payload["context"] = context

        user_message = (
            "Analyse the following de-identified satisfaction comments from VITAL Worklife clients:\n\n"
            + json.dumps(payload, indent=2)
        )

        result = self.analyze(self.SENTIMENT_SYSTEM_PROMPT, user_message)

        if result["success"]:
            try:
                result["insights"] = json.loads(result["content"])
            except json.JSONDecodeError:
                import re
                match = re.search(r"\{.*\}", result["content"], re.DOTALL)
                if match:
                    try:
                        result["insights"] = json.loads(match.group())
                    except json.JSONDecodeError:
                        result["insights"] = {"raw": result["content"]}
                else:
                    result["insights"] = {"raw": result["content"]}
        else:
            result["insights"] = {}

        return result

    # ------------------------------------------------------------------
    # Generic free-form analytics prompt (for future extensibility)
    # ------------------------------------------------------------------

    def free_form_analytics(self, prompt: str, data: dict | None = None) -> dict:
        """
        Send a free-form analytics prompt to Claude, optionally with data.

        Parameters
        ----------
        prompt : str
            The analytics question or instruction.
        data   : dict, optional
            Supporting data to include in the message.

        Returns
        -------
        dict – result from `analyze()`.
        """
        system = (
            "You are an expert data analyst. Provide clear, concise, actionable insights. "
            "When data is provided, base your analysis strictly on that data."
        )
        user_message = prompt
        if data:
            user_message += "\n\nData:\n" + json.dumps(data, indent=2, default=str)

        return self.analyze(system, user_message)


# ---------------------------------------------------------------------------
# Module-level singleton helper (mirrors the pattern used by other services)
# ---------------------------------------------------------------------------
_service_instance: AnthropicService | None = None


def get_anthropic_service() -> AnthropicService:
    """Return the module-level singleton AnthropicService, creating it if needed."""
    global _service_instance
    if _service_instance is None:
        _service_instance = AnthropicService()
    return _service_instance
