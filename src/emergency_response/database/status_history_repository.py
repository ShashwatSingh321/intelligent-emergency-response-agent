
import json
from pathlib import Path

from emergency_response.models.status_history import StatusHistoryEntry


class StatusHistoryRepository:
    """Persist emergency status history in a separate JSON file."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

        if not self.path.exists():
            self.path.write_text("[]", encoding="utf-8")

    def _read_entries(self) -> list[StatusHistoryEntry]:
        """Read and validate saved history entries."""
        with self.path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, list):
            raise ValueError("Status history storage must contain a JSON list.")

        return [
            StatusHistoryEntry.model_validate(entry)
            for entry in data
        ]

    def record(self, entry: StatusHistoryEntry) -> StatusHistoryEntry:
        """Append one status change to the history."""
        entries = self._read_entries()
        entries.append(entry)

        with self.path.open("w", encoding="utf-8") as file:
            json.dump(
                [
                    item.model_dump(mode="json")
                    for item in entries
                ],
                file,
                indent=2,
                ensure_ascii=False,
            )

        return entry

    def list_for_report(
        self,
        report_id: str,
    ) -> list[StatusHistoryEntry]:
        """Return history entries for one report, in recorded order."""
        return [
            entry
            for entry in self._read_entries()
            if entry.report_id == report_id
        ]
