"""Project-defined demo contract, NOT verified DOC0102 business policy."""
import json
import math
from datetime import date

REQUIRED = {
    "REMOTE_WORK": ("reason", "location"),
    "INTL_WORK": ("reason", "country", "office"),
    "HARDWARE_PURCHASE": ("reason", "item"),
    "EXPENSE_CLAIM": ("reason", "currency", "receipt"),
    "SECURITY_REVIEW": ("reason", "system", "scope"),
}


def iso_date(value):
    if type(value) is not str:
        raise ValueError("date must be YYYY-MM-DD")
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        raise ValueError("date must be YYYY-MM-DD") from None
    if parsed.isoformat() != value:
        raise ValueError("date must be YYYY-MM-DD")
    return parsed


def date_range(start, end):
    first, last = iso_date(start), iso_date(end)
    if first > last:
        raise ValueError("start_date must be <= end_date")
    return first, last


def validate_request(request_type, employee, details, start_date="", end_date=""):
    if type(request_type) is not str or request_type not in REQUIRED:
        raise ValueError("unsupported request_type")
    if type(employee) is not str or not employee.strip():
        raise ValueError("employee must be a nonblank string")
    if type(details) is not str:
        raise ValueError("details must be a JSON object encoded as string")
    try:
        payload = json.loads(details)
    except ValueError:
        raise ValueError("details must be a JSON object encoded as string") from None
    if type(payload) is not dict:
        raise ValueError("details must contain a JSON object")
    for field in REQUIRED[request_type]:
        value = payload.get(field)
        if type(value) is not str or not value.strip():
            raise ValueError(f"details.{field} must be a nonblank string")
    if request_type == "EXPENSE_CLAIM":
        amount = payload.get("amount")
        if type(amount) not in (int, float) or not math.isfinite(amount) or amount <= 0:
            raise ValueError("details.amount must be a finite positive number")
    if type(start_date) is not str or type(end_date) is not str:
        raise ValueError("dates must be strings")
    if request_type in ("REMOTE_WORK", "INTL_WORK") or start_date or end_date:
        date_range(start_date, end_date)
