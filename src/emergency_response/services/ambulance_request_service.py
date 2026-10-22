"""Persistent storage for additional ambulance requests."""

import json
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from uuid import uuid4


class AmbulanceRequestRepository:
    """Store and retrieve additional ambulance requests in JSON."""

    def __init__(self, file_path: Path):
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()

        if not self.file_path.exists():
            self.file_path.write_text("[]", encoding="utf-8")

    def list_requests(self) -> list[dict]:
        with self._lock:
            data = json.loads(self.file_path.read_text(encoding="utf-8"))
            if not isinstance(data, list):
                raise ValueError("Ambulance request data must be a JSON list.")
            return sorted(
                data,
                key=lambda item: item.get("created_at", ""),
                reverse=True,
            )

    def create_request(
        self,
        location_id: str,
        location_name: str,
        ambulance_count: int,
        reason: str,
    ) -> dict:
        with self._lock:
            data = json.loads(self.file_path.read_text(encoding="utf-8"))
            if not isinstance(data, list):
                raise ValueError("Ambulance request data must be a JSON list.")

            record = {
                "request_id": f"AMB-{uuid4().hex[:10].upper()}",
                "location_id": location_id,
                "location_name": location_name,
                "ambulance_count": ambulance_count,
                "reason": reason,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "notification_status": "pending",
            }
            data.append(record)
            self.file_path.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            return record.copy()

    def update_notification_status(
        self,
        request_id: str,
        notification_status: str,
    ) -> dict | None:
        with self._lock:
            data = json.loads(self.file_path.read_text(encoding="utf-8"))

            for record in data:
                if record.get("request_id") == request_id:
                    record["notification_status"] = notification_status
                    self.file_path.write_text(
                        json.dumps(data, indent=2, ensure_ascii=False),
                        encoding="utf-8",
                    )
                    return record.copy()

            return None