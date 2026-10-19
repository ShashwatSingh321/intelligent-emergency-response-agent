
from emergency_response.models.emergency import (
    EmergencyReport,
    EmergencyType,
)


def calculate_priority(report: EmergencyReport) -> int:
    """
    Calculate a preliminary priority from 1 (lowest) to 5 (highest).

    This is a simple prototype rule, not a medical diagnosis.
    """
    description = report.description.lower()

    # Highest preliminary priority for potentially life-threatening keywords.
    critical_keywords = (
        "unconscious",
        "not breathing",
        "severe bleeding",
        "cardiac arrest",
        "fire",
        "trapped",
    )

    if any(keyword in description for keyword in critical_keywords):
        return 5

    # High priority for reports involving multiple affected people.
    if report.people_affected >= 5:
        return 4

    # Emergency category provides a basic fallback.
    if report.emergency_type in {
        EmergencyType.MEDICAL,
        EmergencyType.FIRE,
        EmergencyType.ACCIDENT,
        EmergencyType.SECURITY,
    }:
        return max(report.priority, 3)

    return report.priority


def explain_priority(report: EmergencyReport) -> str:
    """Return a human-readable explanation of the preliminary priority."""
    priority = calculate_priority(report)

    if priority == 5:
        return "Potentially critical keywords detected; urgent human review is needed."
    if priority == 4:
        return "Multiple people may be affected; prompt human review is needed."
    if priority == 3:
        return "Standard preliminary priority; review the report for further details."
    return "Lower preliminary priority; review and update if new information emerges."
