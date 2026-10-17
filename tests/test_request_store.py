import json
from policy_agent.mcp_server import request_store as module


def test_create_readback(tmp_path):
    assert hasattr(module, "RequestStore"), "RequestStore feature missing"
    store = module.RequestStore(tmp_path / "requests.json")
    record = store.create("REMOTE_WORK", "Demo Employee", '{"reason":"demo","location":"home"}', "2026-11-02", "2026-11-03")
    assert record.status == "submitted"
    assert store.get(record.request_id) == record
    assert json.loads(store.path.read_text(encoding="utf-8"))[0]["request_id"] == record.request_id


import os
import pytest


def test_failed_replace_preserves_old_file(tmp_path, monkeypatch):
    store = module.RequestStore(tmp_path / "requests.json")
    first = store.create("REMOTE_WORK", "Demo", '{"reason":"demo","location":"home"}', "2026-11-02", "2026-11-03")
    before = store.path.read_bytes()
    def fail(*args):
        raise OSError("synthetic replace failure")
    monkeypatch.setattr(os, "replace", fail)
    with pytest.raises(OSError):
        store.create("REMOTE_WORK", "Demo", '{"reason":"demo","location":"home"}', "2026-11-02", "2026-11-03")
    assert store.path.read_bytes() == before
    assert store.get(first.request_id) == first
    assert list(tmp_path.glob("*.tmp")) == []


@pytest.mark.parametrize("raw", ["broken", "{}", "[{}]", '[{"request_id":42}]'])
def test_corruption_rejected_without_overwrite(tmp_path, raw):
    store = module.RequestStore(tmp_path / "requests.json")
    store.path.write_text(raw, encoding="utf-8")
    with pytest.raises(ValueError, match="corrupt"):
        store.create("REMOTE_WORK", "Demo", '{"reason":"demo","location":"home"}', "2026-11-02", "2026-11-03")
    assert store.path.read_text(encoding="utf-8") == raw


@pytest.mark.parametrize("kwargs", [
    {"request_type":"INVALID"}, {"employee":" "}, {"details":"free text"},
    {"details":"{}"}, {"start_date":"2026-11-05","end_date":"2026-11-03"},
    {"start_date":"20261102"}, {"details":'{"reason":"demo","location":42}'},
])
def test_validation_before_write(tmp_path, kwargs):
    store = module.RequestStore(tmp_path / "requests.json")
    args = dict(request_type="REMOTE_WORK", employee="Demo", details='{"reason":"demo","location":"home"}', start_date="2026-11-02", end_date="2026-11-03")
    args.update(kwargs)
    with pytest.raises(ValueError):
        store.create(**args)
    assert not store.path.exists()


@pytest.mark.parametrize("kind,details", [
    ("REMOTE_WORK", '{"reason":"demo","location":"home"}'),
    ("INTL_WORK", '{"reason":"demo","country":"Demo Country","office":"Demo Office"}'),
    ("HARDWARE_PURCHASE", '{"reason":"demo","item":"Demo laptop"}'),
    ("EXPENSE_CLAIM", '{"reason":"demo","currency":"USD","receipt":"DEMO-001","amount":1}'),
    ("SECURITY_REVIEW", '{"reason":"demo","system":"Demo system","scope":"Demo scope"}'),
])
def test_supported_types(tmp_path, kind, details):
    store = module.RequestStore(tmp_path / "requests.json")
    record = store.create(kind, "Demo", details, "2026-11-02", "2026-11-03")
    assert store.get(record.request_id) == record


@pytest.mark.parametrize("amount", [0, -1, True, "10", float("nan"), float("inf")])
def test_invalid_expense_amount(tmp_path, amount):
    store = module.RequestStore(tmp_path / "requests.json")
    details = json.dumps(dict(reason="demo", currency="USD", receipt="DEMO-001", amount=amount))
    with pytest.raises(ValueError):
        store.create("EXPENSE_CLAIM", "Demo", details)
    assert not store.path.exists()


def test_missing_id(tmp_path):
    with pytest.raises(ValueError, match="not found"):
        module.RequestStore(tmp_path / "requests.json").get("missing")


def test_multiple_records(tmp_path):
    store = module.RequestStore(tmp_path / "requests.json")
    first = store.create("HARDWARE_PURCHASE", "Demo", '{"reason":"demo","item":"demo"}')
    second = store.create("HARDWARE_PURCHASE", "Demo", '{"reason":"demo","item":"demo"}')
    assert first.request_id != second.request_id
    assert store.get(first.request_id) == first
    assert store.get(second.request_id) == second


def test_duplicate_ids_rejected(tmp_path):
    store = module.RequestStore(tmp_path / "requests.json")
    store.create("HARDWARE_PURCHASE", "Demo", '{"reason":"demo","item":"demo"}')
    raw = json.loads(store.path.read_text(encoding="utf-8"))
    store.path.write_text(json.dumps(raw + raw), encoding="utf-8")
    before = store.path.read_bytes()
    with pytest.raises(ValueError, match="corrupt"):
        store.create("HARDWARE_PURCHASE", "Demo", '{"reason":"demo","item":"demo"}')
    assert store.path.read_bytes() == before
