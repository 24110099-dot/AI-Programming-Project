import os
from pathlib import Path
import subprocess
import sys


def test_demo_is_offline_and_prints_verify_usage(tmp_path):
    root = Path(__file__).resolve().parents[1]
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    env.pop("GROQ_API_KEY", None)
    result = subprocess.run([sys.executable, str(root / "scripts/demo_agent_fake.py"), str(tmp_path)], cwd=root, env=env, capture_output=True, text=True, encoding="utf-8")
    assert result.returncode == 0, result.stderr
    assert "TEST-ONLY" in result.stdout
    assert '"action": "create_request"' in result.stdout
    assert '"action": "get_request"' in result.stdout
    assert '"event": "USAGE"' in result.stdout
