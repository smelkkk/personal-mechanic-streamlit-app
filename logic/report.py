from typing import Dict
from .triage import TriageResult


def build_report(case: Dict, result: TriageResult) -> str:
    lines = []
    lines.append("PERSONAL MECHANIC — MECHANIC REPORT")
    lines.append("")
    lines.append(f"Vehicle: {case.get('car_model', 'Unknown')} | Mileage: {case.get('mileage', 'Unknown')} km")
    lines.append(f"Warning type: {case.get('warning_type', 'Unknown')}")
    lines.append(f"Light behavior: {case.get('light_behavior', 'Unknown')}")
    lines.append(f"Appeared after refueling: {'Yes' if case.get('after_refuel') else 'No'}")
    lines.append("")

    symptoms = case.get("symptoms", [])
    lines.append("Observed symptoms:")
    if symptoms:
        for s in symptoms:
            lines.append(f"- {s}")
    else:
        lines.append("- None reported")

    lines.append("")
    lines.append(f"Urgency: {result.urgency}  (confidence: {int(result.confidence * 100)}%)")
    lines.append("")
    lines.append("Reasons:")
    for r in result.reasons:
        lines.append(f"- {r}")

    lines.append("")
    lines.append("Recommended next steps:")
    for i, step in enumerate(result.next_steps, start=1):
        lines.append(f"{i}. {step}")

    lines.append("")
    lines.append("Disclaimer: Prototype guidance only. Consult a professional mechanic for diagnosis.")
    return "\n".join(lines)