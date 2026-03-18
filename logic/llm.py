import os
from typing import Dict, Tuple
from openai import OpenAI, AuthenticationError, APIConnectionError, RateLimitError, BadRequestError


def generate_text(case: Dict, decision: Dict, report_text: str) -> Tuple[bool, Dict[str, str], str]:
    """
    LLM is used ONLY for language:
    - calm explanation for the driver
    - nicer mechanic report wording/formatting
    Decision logic stays rule-based.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return False, {}, (
            "AI mode is ON, but the OpenAI API key is missing or invalid. "
            "Please set OPENAI_API_KEY in your terminal (or .env) and restart the app."
        )

    client = OpenAI(api_key=api_key)

    prompt = f"""
You are an automotive assistant. Keep it calm and short.
Do NOT change the urgency decision.

CASE:
- car_model: {case.get("car_model")}
- mileage_km: {case.get("mileage")}
- warning_type: {case.get("warning_type")}
- light_behavior: {case.get("light_behavior")}
- after_refuel: {case.get("after_refuel")}
- symptoms: {case.get("symptoms")}

DECISION (fixed):
- urgency: {decision.get("Urgency")}
- confidence: {decision.get("Confidence")}
- reasons: {decision.get("Top reasons")}
- next_steps: {decision.get("Next steps")}

CURRENT_REPORT_TEXT:
{report_text}

Return TWO sections clearly:
EXPLANATION: (max 4 sentences)
MECHANIC_REPORT: (same content but clearer formatting, sections + bullets)
"""

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        )
        out = resp.choices[0].message.content or ""

        explanation = out
        report = out

        if "MECHANIC_REPORT:" in out:
            parts = out.split("MECHANIC_REPORT:", 1)
            explanation = parts[0].replace("EXPLANATION:", "").strip()
            report = parts[1].strip()

        return True, {"explanation": explanation, "report": report}, ""

    except AuthenticationError:
        return False, {}, (
            "AI mode is ON, but the OpenAI API key is missing or invalid. "
            "Please set OPENAI_API_KEY in your terminal (or .env) and restart the app."
        )
    except RateLimitError:
        return False, {}, (
            "AI mode is temporarily unavailable due to rate limits. "
            "Please try again in a minute."
        )
    except APIConnectionError:
        return False, {}, (
            "AI mode couldn't connect to the server. "
            "Check your internet connection and try again."
        )
    except BadRequestError:
        return False, {}, (
            "AI mode failed due to an invalid request. "
            "Try again, or disable AI mode."
        )
    except Exception:
        return False, {}, (
            "AI mode failed unexpectedly. "
            "You can continue using the app without AI explanations."
        )