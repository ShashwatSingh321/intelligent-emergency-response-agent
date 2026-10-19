
from pydantic import BaseModel, Field


class Location(BaseModel):
    id: str
    name: str
    latitude: float | None = None
    longitude: float | None = None
    connected_locations: list[str] = Field(default_factory=list)
