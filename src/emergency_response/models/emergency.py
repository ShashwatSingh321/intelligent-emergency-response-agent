
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class EmergencyType(str, Enum):
    MEDICAL = "medical"
    FIRE = "fire"
    SECURITY = "security"
    ACCIDENT = "accident"
    OTHER = "other"


class EmergencyStatus(str, Enum):
    REPORTED = "reported"
    UNDER_REVIEW = "under_review"
    ASSIGNED = "assigned"
    RESPONDING = "responding"
    RESOLVED = "resolved"
    CANCELLED = "cancelled"


class EmergencyReport(BaseModel):
    id: str = Field(description="Unique emergency report ID")
    description: str = Field(min_length=3, max_length=2000)
    emergency_type: EmergencyType = EmergencyType.OTHER
    location_id: str = Field(description="ID of the reported campus location")
    reported_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    status: EmergencyStatus = EmergencyStatus.REPORTED
    priority: int = Field(default=3, ge=1, le=5)
    people_affected: int = Field(default=1, ge=1)

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: str) -> str:
        value = value.strip()

        if len(value) < 3:
            raise ValueError(
                "Emergency description must contain at least 3 "
                "non-whitespace characters."
            )

        return value

    @field_validator("location_id")
    @classmethod
    def validate_location_id(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Campus location ID cannot be blank.")

        return value
