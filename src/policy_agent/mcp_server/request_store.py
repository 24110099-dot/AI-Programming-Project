"""Luu tru ho so thu tuc duoi dang file JSON (Single-writer request store).

Su dung file tam thoi va os.replace de dam bao tinh nguyen tu (atomic write),
tranh truong hop file requests.json bi hong neu he thong bi ngat dot ngot.
Nguoi phu trach: SV C (Khang).
"""

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

    def _read(self) -> list[ProcedureRequest]:
        """Doc toan bo danh sach ho so tu file requests.json va validate tung ban ghi."""
        if not self.path.exists():
            return []
        try:
            raw_text = self.path.read_text(encoding="utf-8")
            data = json.loads(raw_text)
            if not isinstance(data, list):
                raise ValueError("expected list")

            records = [ProcedureRequest(**row) for row in data]
            seen_ids = set()
            for record in records:
                # Kiem tra hop le cua du lieu trong file
                validate_request(
                    record.request_type,
                    record.employee,
                    record.details,
                    record.start_date,
                    record.end_date,
                )
                if (
                    not record.request_id.startswith("REQ-")
                    or record.request_id in seen_ids
                    or record.status != "submitted"
                    or not record.created_at
                ):
                    raise ValueError("invalid record")
                seen_ids.add(record.request_id)

            return records
        except (ValueError, TypeError) as exc:
            raise ValueError("corrupt request store; restore manually, no overwrite") from exc

    def create(
        self,
        request_type: str,
        employee: str,
        details: str,
        start_date: str = "",
        end_date: str = "",
    ) -> ProcedureRequest:
        """Tao mot ho so moi, validate cac truong va luu nguyen tu vao file."""
        validate_request(request_type, employee, details, start_date, end_date)
        rows = self._read()

        new_id = "REQ-" + uuid4().hex
        record = ProcedureRequest(
            request_id=new_id,
            request_type=request_type,
            employee=employee,
            details=details,
            start_date=start_date,
            end_date=end_date,
            status="submitted",
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        rows.append(record)

        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp_file = None
        try:
            # Ghi ra file tam thoi roi moi replace de an toan du lieu
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.path.parent,
                suffix=".tmp",
                delete=False,
            ) as stream:
                temp_file = Path(stream.name)
                json.dump([asdict(r) for r in rows], stream, ensure_ascii=False, indent=2)
                stream.flush()
                os.fsync(stream.fileno())

            os.replace(temp_file, self.path)
        finally:
            if temp_file is not None:
                temp_file.unlink(missing_ok=True)

        return record

    def get(self, request_id: str) -> ProcedureRequest:
        """Doc mot ho so theo ma request_id."""
        if not isinstance(request_id, str) or not request_id.strip():
            raise ValueError("request_id must be a nonblank string")

        for record in self._read():
            if record.request_id == request_id:
                return record

        raise ValueError("not found")
