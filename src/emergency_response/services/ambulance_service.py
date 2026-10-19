
from emergency_response.models.ambulance import Ambulance, AmbulanceStatus
from emergency_response.models.emergency import EmergencyReport


def select_ambulance(
    report: EmergencyReport,
    ambulances: list[Ambulance],
    required_equipment: set[str] | None = None,
) -> Ambulance | None:
    """
    Select the most suitable available ambulance.

    Returns None if no ambulance meets all requirements.
    This prototype does not yet calculate route distance or travel time.
    """
    required_equipment = required_equipment or set()

    suitable = [
        ambulance
        for ambulance in ambulances
        if ambulance.status == AmbulanceStatus.AVAILABLE
        and ambulance.capacity >= report.people_affected
        and required_equipment.issubset(ambulance.equipment)
    ]

    if not suitable:
        return None

    # Prefer an ambulance with fewer unnecessary extra equipment items.
    # Use its ID as a stable tie-breaker.
    return min(
        suitable,
        key=lambda ambulance: (
            len(ambulance.equipment - required_equipment),
            ambulance.id,
        ),
    )
