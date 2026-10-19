
from datetime import datetime, timezone

from pydantic import BaseModel, Field

from emergency_response.models.emergency import EmergencyStatus


class StatusHistoryEntry(BaseModel):
    """Record a single emergency status change."""

    report_id: str = Field(min_length=1)
    previous_status: EmergencyStatus
    new_status: EmergencyStatus
    changed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
