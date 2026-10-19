
from enum import Enum
from pydantic import BaseModel, Field


class AmbulanceStatus(str, Enum):
    AVAILABLE = "available"
    DISPATCHED = "dispatched"
    BUSY = "busy"
    MAINTENANCE = "maintenance"


class Ambulance(BaseModel):
    id: str
    current_location_id: str
    status: AmbulanceStatus = AmbulanceStatus.AVAILABLE
    equipment: set[str] = Field(default_factory=set)
    capacity: int = Field(default=2, ge=1)
