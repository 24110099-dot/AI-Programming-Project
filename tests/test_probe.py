import json
import os
import subprocess
import sys
from pathlib import Path


def test_raw_probe(tmp_path):
    root = Path(__file__).resolve().parents[1]
    script = root / "scripts/probe_server.py"
    assert script.exists(), "raw JSON-RPC probe missing"
    completed = subprocess.run([sys.executable, str(script), "--state-dir", str(tmp_path)], cwd=root, capture_output=True, text=True, encoding="utf-8", timeout=40)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "RAW PROBE PASS: 5 tools; create/get/disk identical; stdout JSON only" in completed.stdout
    proof = json.loads((tmp_path / "probe-proof.json").read_text(encoding="utf-8"))
    assert proof["created"] == proof["verified"] == proof["disk"][0]
    assert proof["protocol"] == "2025-11-25"
    assert (tmp_path / "server.stderr.log").read_text(encoding="utf-8").find("FAKE") >= 0
