import asyncio
import pytest
from scripts.second_host import run_second_host


def test_second_host_execution(tmp_path, monkeypatch):
    """Kiem tra Host thu 2 giao tiep stdio thanh cong voi MCP Server."""
    monkeypatch.setenv("REQUESTS_PATH", str(tmp_path / "requests.json"))
    monkeypatch.setenv("LOGS_DIR", str(tmp_path / "logs"))
    success = asyncio.run(run_second_host())
    assert success is True
