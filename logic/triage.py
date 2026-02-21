from dataclasses import dataclass
from typing import List, Dict


@dataclass
class TriageResult:
    urgency: str          # "Drive OK" | "Service Soon" | "Stop Now"
    confidence: float     # 0.0 - 1.0
    reasons: List[str]    # short bullet reasons
    next_steps: List[str] # actionable steps


def triage(case: Dict) -> TriageResult:
    """
    Rule-based triage for prototype purposes.
    Keeps safety logic deterministic and transparent.
    """

    warning_type = case.get("warning_type", "Check engine")
    light_behavior = case.get("light_behavior", "Steady")
    symptoms = set(case.get("symptoms", []))
    after_refuel = bool(case.get("after_refuel", False))
    driving_now = bool(case.get("driving_now", False))

    # Safety-first overrides
    if light_behavior == "Flashing" and warning_type == "Check engine":
        return TriageResult(
            urgency="Stop Now",
            confidence=0.92,
            reasons=[
                "Flashing check engine light can indicate serious engine misfire risk.",
                "Continuing to drive may cause damage."
            ],
            next_steps=[
                "Safely pull over when possible and turn off the engine.",
                "If the car runs rough, call roadside assistance / tow.",
                "Share the mechanic report with service."
            ],
        )

    if "Steam" in symptoms or warning_type == "Engine temperature":
        return TriageResult(
            urgency="Stop Now",
            confidence=0.9,
            reasons=[
                "Steam or high temperature can indicate overheating.",
                "Overheating can cause severe engine damage."
            ],
            next_steps=[
                "Stop when safe and turn off the engine.",
                "Do not open the coolant cap while hot.",
                "Call roadside assistance if needed."
            ],
        )

    if warning_type == "Oil pressure":
        return TriageResult(
            urgency="Stop Now",
            confidence=0.88,
            reasons=[
                "Low oil pressure can quickly damage the engine.",
            ],
            next_steps=[
                "Stop when safe and turn off the engine.",
                "Check oil level only when safe and parked.",
                "Tow to service if the warning persists."
            ],
        )

    # Non-emergency logic (scoring)
    score = 0
    reasons = []

    if "Burning smell" in symptoms:
        score += 3
        reasons.append("Burning smell suggests a potential overheating or electrical issue.")

    if "Loud unusual noise" in symptoms:
        score += 3
        reasons.append("Unusual noise can signal a mechanical problem.")

    if "Shaking" in symptoms:
        score += 2
        reasons.append("Shaking may indicate misfire or drivability issue.")

    if "Loss of power" in symptoms:
        score += 2
        reasons.append("Loss of power can indicate engine or powertrain fault.")

    if warning_type == "Brake warning":
        score += 3
        reasons.append("Brake warnings should be checked promptly for safety.")

    if after_refuel and warning_type == "Check engine":
        score -= 1
        reasons.append("Appeared after refueling: could be a loose fuel cap / EVAP alert.")

    # Decide urgency based on score
    if score >= 5:
        urgency = "Service Soon"
        confidence = 0.75
        next_steps = [
            "Avoid high speeds and aggressive acceleration.",
            "Schedule a diagnostic within 24–48 hours.",
            "If symptoms worsen, stop and seek assistance."
        ]
    else:
        urgency = "Drive OK"
        confidence = 0.7 if reasons else 0.6
        next_steps = [
            "Drive normally but monitor the warning and symptoms.",
            "If the light stays on for multiple trips, schedule a diagnostic.",
            "If new symptoms appear, re-run the triage."
        ]

    # Add context-based note
    if driving_now and urgency != "Stop Now":
        reasons.insert(0, "Since you're driving now, recommendations prioritize safe minimal actions.")

    # Keep reasons concise (max 3)
    reasons = reasons[:3] if reasons else ["No severe symptoms reported."]

    return TriageResult(
        urgency=urgency,
        confidence=confidence,
        reasons=reasons,
        next_steps=next_steps
    )