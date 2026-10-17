"""Single-writer JSON request store; records use B's shared dataclass."""
import json
import os
import tempfile
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from policy_agent.models import ProcedureRequest
from .validation import validate_request


class RequestStore:
    def __init__(self, path: Path):
        self.path = Path(path)

    def _read(self):
        if not self.path.exists():
            return []
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if type(data) is not list:
                raise ValueError("expected list")
            records = [ProcedureRequest(**row) for row in data]
            ids = set()
            for record in records:
                validate_request(record.request_type, record.employee, record.details, record.start_date, record.end_date)
                if not record.request_id.startswith("REQ-") or record.request_id in ids or record.status != "submitted" or not record.created_at:
                    raise ValueError("invalid record")
                ids.add(record.request_id)
            return records
        except (ValueError, TypeError) as exc:
            raise ValueError("corrupt request store; restore manually, no overwrite") from exc

    def create(self, request_type, employee, details, start_date="", end_date=""):
        validate_request(request_type, employee, details, start_date, end_date)
        rows = self._read()
        record = ProcedureRequest("REQ-" + uuid4().hex, request_type, employee, details, start_date, end_date, created_at=datetime.now(timezone.utc).isoformat())
        rows.append(record)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=self.path.parent, suffix=".tmp", delete=False) as stream:
                temporary = Path(stream.name)
                json.dump([asdict(row) for row in rows], stream, ensure_ascii=False, indent=2)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
        return record

    def get(self, request_id):
        if type(request_id) is not str or not request_id.strip():
            raise ValueError("request_id must be a nonblank string")
        for record in self._read():
            if record.request_id == request_id:
                return record
        raise ValueError("not found")
