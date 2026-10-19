
import json
from pathlib import Path

from emergency_response.models.emergency import EmergencyReport


class EmergencyRepository:
    """Store and retrieve emergency reports using a JSON file."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

        if not self.path.exists():
            self.path.write_text("[]", encoding="utf-8")

    def _read_reports(self) -> list[EmergencyReport]:
        """Read and validate all saved reports."""
        with self.path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, list):
            raise ValueError("Emergency report storage must contain a JSON list.")

        return [
            EmergencyReport.model_validate(record)
            for record in data
        ]

    def _write_reports(self, reports: list[EmergencyReport]) -> None:
        """Write reports using JSON serialization."""
        with self.path.open("w", encoding="utf-8") as file:
            json.dump(
                [report.model_dump(mode="json") for report in reports],
                file,
                indent=2,
                ensure_ascii=False,
            )

    def save(self, report: EmergencyReport) -> EmergencyReport:
        """Save a new report; reject duplicate report IDs."""
        reports = self._read_reports()

        if any(existing.id == report.id for existing in reports):
            raise ValueError(f"Report ID already exists: {report.id}")

        reports.append(report)
        self._write_reports(reports)
        return report

    def get_by_id(self, report_id: str) -> EmergencyReport | None:
        """Return a report by ID, or None if it does not exist."""
        for report in self._read_reports():
            if report.id == report_id:
                return report

        return None

    def list_all(self) -> list[EmergencyReport]:
        """Return all saved reports."""
        return self._read_reports()

    def update(self, report: EmergencyReport) -> EmergencyReport:
        """Replace an existing report with the same ID."""
        reports = self._read_reports()

        for index, existing in enumerate(reports):
            if existing.id == report.id:
                reports[index] = report
                self._write_reports(reports)
                return report

        raise KeyError(f"Report not found: {report.id}")
