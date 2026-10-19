
from emergency_response.models.emergency import (
    EmergencyReport,
    EmergencyType,
)


CRITICAL_KEYWORDS = (
    "unconscious",
    "not breathing",
    "severe bleeding",
    "cardiac arrest",
    "fire",
    "trapped",
)

HIGH_PRIORITY_PEOPLE_THRESHOLD = 5


def calculate_priority(report: EmergencyReport) -> int:
    """
    Calculate preliminary priority from 1 (lowest) to 5 (highest).

    This is a rule-based prototype, not a medical diagnosis.
    A human responder must assess the actual situation.
    """
    description = report.description.lower()

    # Potentially life-threatening indicators take precedence.
    if any(keyword in description for keyword in CRITICAL_KEYWORDS):
        return 5

    # Multiple affected people may require prompt attention.
    if report.people_affected >= HIGH_PRIORITY_PEOPLE_THRESHOLD:
        return max(report.priority, 4)

    # Preserve the existing priority for less common categories.
    if report.emergency_type in {
        EmergencyType.MEDICAL,
        EmergencyType.FIRE,
        EmergencyType.ACCIDENT,
        EmergencyType.SECURITY,
    }:
        return max(report.priority, 3)

    return report.priority


def explain_priority(report: EmergencyReport) -> str:
    """Explain the rule responsible for the preliminary priority."""
    priority = calculate_priority(report)
    description = report.description.lower()

    matched_keywords = [
        keyword
        for keyword in CRITICAL_KEYWORDS
        if keyword in description
    ]

    if matched_keywords:
        return (
            "Potentially critical indicator(s) detected: "
            f"{', '.join(matched_keywords)}. "
            "Urgent human review is needed."
        )

    if report.people_affected >= HIGH_PRIORITY_PEOPLE_THRESHOLD:
        return (
            f"{report.people_affected} people are reported affected. "
            "Prompt human review is needed."
        )

    if priority >= 3:
        return (
            "Priority reflects the existing report priority and "
            "emergency category rules. Human review is needed."
        )

    return (
        "Lower preliminary priority under the current rules. "
        "This does not establish that the situation is safe."
    )
