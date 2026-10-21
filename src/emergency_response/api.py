from functools import lru_cache
from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from emergency_response.ai.report_parser import (
    EmergencyReportParser,
    ParsedEmergencyReport,
)
from emergency_response.database.campus_repository import (
    CampusKnowledgeRepository,
)
from emergency_response.database.emergency_repository import (
    EmergencyRepository,
)
from emergency_response.database.repository import (
    load_ambulances,
)
from emergency_response.models.emergency import (
    EmergencyReport,
    EmergencyStatus,
    EmergencyType,
)
from emergency_response.services.emergency_workflow import (
    EmergencyWorkflow,
)


app = FastAPI(
    title="Intelligent Emergency Response Agent API",
    description=(
        "API for emergency reporting, priority evaluation, "
        "ambulance recommendations, routing, and status tracking."
    ),
    version="0.4.0",
)


class EmergencyCreateRequest(BaseModel):
    """Validate fields accepted when submitting an emergency."""

    model_config = ConfigDict(extra="forbid")

    description: Annotated[
        str,
        StringConstraints(
            min_length=3,
            max_length=2000,
            strip_whitespace=True,
        ),
    ]
    emergency_type: EmergencyType = EmergencyType.OTHER
    location_id: Annotated[
        str,
        StringConstraints(
            min_length=1,
            max_length=100,
            strip_whitespace=True,
        ),
    ]
    people_affected: int = Field(default=1, ge=1)


class EmergencyParseRequest(BaseModel):
    """Validate a natural-language emergency report."""

    model_config = ConfigDict(extra="forbid")

    text: Annotated[
        str,
        StringConstraints(
            min_length=3,
            max_length=2000,
            strip_whitespace=True,
        ),
    ]


class StatusUpdateRequest(BaseModel):
    """Validate requested emergency status transitions."""

    model_config = ConfigDict(extra="forbid")

    status: EmergencyStatus


class FacilityCreateRequest(BaseModel):
    """Validate a new campus facility."""

    model_config = ConfigDict(extra="forbid")

    location_id: Annotated[
        str,
        StringConstraints(
            min_length=1,
            max_length=100,
            strip_whitespace=True,
        ),
    ]

    name: Annotated[
        str,
        StringConstraints(
            min_length=1,
            max_length=150,
            strip_whitespace=True,
        ),
    ]

    details: Annotated[
        str,
        StringConstraints(
            max_length=1000,
            strip_whitespace=True,
        ),
    ] = ""


report_parser = EmergencyReportParser()


@lru_cache(maxsize=1)
def get_campus_repository() -> CampusKnowledgeRepository:
    project_root = Path(__file__).resolve().parents[2]
    data_dir = project_root / "data"
    repository = CampusKnowledgeRepository(
        data_dir / "campus.db"
    )
    repository.import_campus_map(
        data_dir / "campus_map.json"
    )
    return repository


def resolve_location(location_hint: str | None) -> str | None:
    return get_campus_repository().resolve_location(location_hint)


@lru_cache(maxsize=1)
def get_workflow() -> EmergencyWorkflow:
    """Create the workflow once and reuse it across API requests."""

    project_root = Path(__file__).resolve().parents[2]
    data_dir = project_root / "data"

    graph = get_campus_repository().load_graph()
    ambulances = load_ambulances(
        data_dir / "sample_ambulances.json"
    )
    repository = EmergencyRepository(
        data_dir / "emergency_reports.json"
    )

    return EmergencyWorkflow(
        repository=repository,
        graph=graph,
        ambulances=ambulances,
    )


def _submit_emergency(
    description: str,
    emergency_type: EmergencyType,
    location_id: str,
    people_affected: int,
) -> dict:
    """Create and submit a report through the existing workflow."""

    report = EmergencyReport(
        id=f"ER-{uuid4().hex[:12].upper()}",
        description=description,
        emergency_type=emergency_type,
        location_id=location_id,
        people_affected=people_affected,
    )

    try:
        result = get_workflow().submit_report(
            report=report,
            required_equipment={"first_aid"},
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    ambulance = result.ambulance

    return {
        "report_id": result.report_id,
        "description": report.description,
        "emergency_type": report.emergency_type.value,
        "location_id": report.location_id,
        "people_affected": report.people_affected,
        "status": report.status.value,
        "priority": result.priority,
        "priority_explanation": result.priority_explanation,
        "ambulance": (
            {
                "id": ambulance.id,
                "starting_location": ambulance.current_location_id,
            }
            if ambulance is not None
            else None
        ),
        "route": result.route,
        "route_cost": result.route_cost,
        "recommendation": result.recommendation,
    }


@app.get("/campus/locations", tags=["Campus"])
def list_campus_locations() -> list[dict]:
    """List all known campus locations."""

    return get_campus_repository().list_locations()


@app.get("/campus/facilities", tags=["Campus"])
def list_campus_facilities(
    location_id: str | None = None,
) -> list[dict]:
    """List facilities, optionally filtered by location ID."""

    repository = get_campus_repository()

    if location_id:
        known_ids = {
            location["id"]
            for location in repository.list_locations()
        }

        if location_id.strip().upper() not in known_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Campus location not found: {location_id}",
            )

    return repository.list_facilities(location_id)


@app.get("/campus/facilities/search", tags=["Campus"])
def search_campus_facilities(
    q: str = Query(min_length=1, max_length=100),
) -> list[dict]:
    """Search campus facility names and details."""

    return get_campus_repository().search_facilities(q)


@app.post(
    "/campus/facilities",
    status_code=status.HTTP_201_CREATED,
    tags=["Campus"],
)
def create_campus_facility(
    request: FacilityCreateRequest,
) -> dict:
    """Add a facility to an existing campus location."""

    try:
        return get_campus_repository().add_facility(
            location_id=request.location_id,
            name=request.name,
            details=request.details,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error


@app.get("/health", tags=["Health"])
def health_check() -> dict[str, str]:
    """Check that the API process is responding."""

    return {"status": "ok"}


@app.post(
    "/emergencies/parse",
    response_model=ParsedEmergencyReport,
    tags=["Emergencies"],
    summary="Parse a natural-language emergency report",
)
def parse_emergency_report(
    request: EmergencyParseRequest,
) -> ParsedEmergencyReport:
    """Extract report details without creating an emergency."""

    return report_parser.parse(request.text)


@app.post(
    "/emergencies",
    status_code=status.HTTP_201_CREATED,
    tags=["Emergencies"],
)
def create_emergency(
    request: EmergencyCreateRequest,
) -> dict:
    """Save and process a structured emergency report."""

    return _submit_emergency(
        description=request.description,
        emergency_type=request.emergency_type,
        location_id=request.location_id,
        people_affected=request.people_affected,
    )


@app.post(
    "/emergencies/from-text",
    status_code=status.HTTP_201_CREATED,
    tags=["Emergencies"],
    summary="Create an emergency from natural language",
)
def create_emergency_from_text(
    request: EmergencyParseRequest,
) -> dict:
    """Parse a report, resolve its location, and submit it."""

    try:
        parsed = report_parser.parse(request.text)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error

    location_id = resolve_location(parsed.location_hint)

    if location_id is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "Could not identify exactly one known campus location. "
                "Mention Main Gate, Library, Hostel, Auditorium, "
                "Medical Center, or Sports Ground."
            ),
        )

    return _submit_emergency(
        description=parsed.description,
        emergency_type=parsed.emergency_type,
        location_id=location_id,
        people_affected=parsed.people_affected,
    )


@app.get("/emergencies", tags=["Emergencies"])
def list_emergencies() -> list[EmergencyReport]:
    """Return all saved emergency reports."""

    return get_workflow().list_reports()


@app.get("/emergencies/{report_id}", tags=["Emergencies"])
def get_emergency(report_id: str) -> EmergencyReport:
    """Retrieve one emergency report by ID."""

    report = get_workflow().get_report(report_id)

    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Emergency report not found: {report_id}",
        )

    return report


@app.patch(
    "/emergencies/{report_id}/status",
    tags=["Emergencies"],
)
def update_emergency_status(
    report_id: str,
    request: StatusUpdateRequest,
) -> EmergencyReport:
    """Apply an allowed status transition and record its history."""

    try:
        return get_workflow().transition_status(
            report_id,
            request.status,
        )
    except KeyError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error