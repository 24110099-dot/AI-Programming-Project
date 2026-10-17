import pytest
from policy_agent.mcp_server.request_store import RequestStore


def test_create_and_get_request(tmp_path):
    store = RequestStore(tmp_path / "requests.json")
    created = store.create(
        "REMOTE_WORK",
        "Nguyen Van A",
        '{"reason": "work from home", "location": "HCMC"}',
        "2026-11-02",
        "2026-11-05",
    )
    fetched = store.get(created.request_id)
    assert created == fetched
    assert fetched.status == "submitted"


def test_supported_request_types(tmp_path):
    store = RequestStore(tmp_path / "requests.json")
    r1 = store.create("HARDWARE_PURCHASE", "An", '{"reason": "dev", "item": "Laptop"}')
    r2 = store.create("EXPENSE_CLAIM", "An", '{"reason": "meal", "currency": "USD", "receipt": "R1", "amount": 50}')
    r3 = store.create("SECURITY_REVIEW", "An", '{"reason": "vpn", "system": "APAC", "scope": "read"}')
    assert r1.request_id != r2.request_id != r3.request_id


def test_validation_rejects_bad_inputs(tmp_path):
    store = RequestStore(tmp_path / "requests.json")
    with pytest.raises(ValueError):
        store.create("UNKNOWN_TYPE", "An", '{"reason": "x"}')
    with pytest.raises(ValueError):
        store.create("EXPENSE_CLAIM", "An", '{"reason": "meal", "currency": "USD", "receipt": "R1", "amount": -10}')
    with pytest.raises(ValueError):
        store.create("REMOTE_WORK", "An", '{"reason": "x", "location": "home"}', "2026-11-06", "2026-11-02")
