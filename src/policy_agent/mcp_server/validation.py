"""Module kiem tra tinh hop le cua du lieu ho so thu tuc (Validation).

Dinh nghia cac truong bat buoc cho 5 loai don theo de tai T1:
- REMOTE_WORK: reason, location, va khoang thoi gian hop le
- INTL_WORK: reason, country, office, va khoang thoi gian hop le
- HARDWARE_PURCHASE: reason, item
- EXPENSE_CLAIM: reason, currency, receipt, va amount (so thuc duong)
- SECURITY_REVIEW: reason, system, scope
Nguoi phu trach: SV C (Khang).
"""

import json
import math
from datetime import date

# Cac truong bat buoc trong details cua tung loai don
REQUIRED_FIELDS = {
    "REMOTE_WORK": ("reason", "location"),
    "INTL_WORK": ("reason", "country", "office"),
    "HARDWARE_PURCHASE": ("reason", "item"),
    "EXPENSE_CLAIM": ("reason", "currency", "receipt"),
    "SECURITY_REVIEW": ("reason", "system", "scope"),
}


def iso_date(value: str) -> date:
    """Kiem tra va parse chuoi ngay theo chuan ISO (YYYY-MM-DD)."""
    if not isinstance(value, str):
        raise ValueError("date must be YYYY-MM-DD")
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        raise ValueError("date must be YYYY-MM-DD") from None

    if parsed.isoformat() != value:
        raise ValueError("date must be YYYY-MM-DD")
    return parsed


def date_range(start: str, end: str) -> tuple[date, date]:
    """Kiem tra khoang thoi gian hop le: start_date phai <= end_date."""
    first = iso_date(start)
    last = iso_date(end)
    if first > last:
        raise ValueError("start_date must be <= end_date")
    return first, last


def validate_request(
    request_type: str,
    employee: str,
    details: str,
    start_date: str = "",
    end_date: str = "",
):
    """Kiem tra toan bo tinh hop le cua mot ho so thu tuc."""
    if not isinstance(request_type, str) or request_type not in REQUIRED_FIELDS:
        raise ValueError("unsupported request_type")

    if not isinstance(employee, str) or not employee.strip():
        raise ValueError("employee must be a nonblank string")

    if not isinstance(details, str):
        raise ValueError("details must be a JSON object encoded as string")

    try:
        payload = json.loads(details)
    except ValueError:
        raise ValueError("details must be a JSON object encoded as string") from None

    if not isinstance(payload, dict):
        raise ValueError("details must contain a JSON object")

    # Kiem tra cac truong bat buoc
    for field in REQUIRED_FIELDS[request_type]:
        val = payload.get(field)
        if not isinstance(val, str) or not val.strip():
            raise ValueError(f"details.{field} must be a nonblank string")

    # Kiem tra so tien doi voi EXPENSE_CLAIM
    if request_type == "EXPENSE_CLAIM":
        amount = payload.get("amount")
        if (
            type(amount) is bool
            or not isinstance(amount, (int, float))
            or not math.isfinite(amount)
            or amount <= 0
        ):
            raise ValueError("details.amount must be a finite positive number")

    if not isinstance(start_date, str) or not isinstance(end_date, str):
        raise ValueError("dates must be strings")

    # Kiem tra ngay bat buoc doi voi REMOTE_WORK va INTL_WORK
    if request_type in ("REMOTE_WORK", "INTL_WORK") or start_date or end_date:
        date_range(start_date, end_date)
