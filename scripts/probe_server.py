"""Raw JSON-RPC over real subprocess stdio. No MCP SDK client imports."""
import argparse
import json
import os
import queue
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

EXPECTED = {"search_policy", "get_document", "calc_business_days", "create_request", "get_request"}


def probe(state_dir: Path):
    root = Path(__file__).resolve().parents[1]
    state_dir = state_dir.resolve()
    state_dir.mkdir(parents=True, exist_ok=True)
    state_path = state_dir / "requests.json"
    if state_path.exists():
        raise ValueError("Use a NEW --state-dir; probe never resets existing state")
    env = os.environ.copy()
    env.update(PYTHONPATH=str(root / "src"), PYTHONUNBUFFERED="1", PYTHONIOENCODING="utf-8", REQUESTS_PATH=str(state_path), LOGS_DIR=str(state_dir / "logs"))
    inbox = queue.Queue()
    received = []
    with (state_dir / "server.stderr.log").open("w", encoding="utf-8") as err:
        process = subprocess.Popen([str(Path(sys.executable).resolve()), "-m", "policy_agent.mcp_server.server"], cwd=str(root), env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=err, text=True, encoding="utf-8", bufsize=1)
        def read_stdout():
            for line in process.stdout:
                inbox.put(line)
            inbox.put(None)
        reader = threading.Thread(target=read_stdout, daemon=True)
        reader.start()
        counter = 0
        def send(payload):
            process.stdin.write(json.dumps(payload, ensure_ascii=False) + "\n")
            process.stdin.flush()
        def parse(line):
            if line is None:
                raise RuntimeError("server closed stdout")
            message = json.loads(line)
            assert message.get("jsonrpc") == "2.0", "non JSON-RPC stdout"
            received.append(message)
            return message
        def rpc(method, params):
            nonlocal counter
            counter += 1
            send({"jsonrpc":"2.0", "id":counter, "method":method, "params":params})
            while True:
                message = parse(inbox.get(timeout=15))
                if message.get("id") == counter:
                    if "error" in message:
                        raise RuntimeError(str(message["error"]))
                    return message["result"]
                assert "method" in message, "unexpected response id"
        def call(name, arguments):
            result = rpc("tools/call", {"name":name,"arguments":arguments})
            assert not result.get("isError", False), result
            return "\n".join(block["text"] for block in result["content"] if block["type"] == "text")
        try:
            initialized = rpc("initialize", {"protocolVersion":"2025-11-25", "capabilities":{}, "clientInfo":{"name":"phase1-raw-probe","version":"1.0"}})
            assert initialized["protocolVersion"] == "2025-11-25"
            send({"jsonrpc":"2.0", "method":"notifications/initialized", "params":{}})
            tools = rpc("tools/list", {})["tools"]
            assert {tool["name"] for tool in tools} == EXPECTED
            assert len(tools) == 5
            print("TOOLS: " + ", ".join(sorted(tool["name"] for tool in tools)))
            assert "FAKE" in call("search_policy", {"query":"remote"})
            assert "FAKE" in call("get_document", {"doc_id":"DEMO_REMOTE"})
            assert call("calc_business_days", {"start_date":"2026-11-02","end_date":"2026-11-06"}) == "5"
            created = json.loads(call("create_request", {"request_type":"REMOTE_WORK","employee":"Demo Employee","details":'{"reason":"demo","location":"home"}',"start_date":"2026-11-02","end_date":"2026-11-03"}))
            verified = json.loads(call("get_request", {"request_id":created["request_id"]}))
            disk = json.loads(state_path.read_text(encoding="utf-8"))
            assert created == verified and disk == [created]
            assert created["status"] == "submitted"
            assert call("get_request", {"request_id":"missing"}).startswith("Error:")
            print("CREATED: " + json.dumps(created, ensure_ascii=False))
            print("VERIFIED: " + json.dumps(verified, ensure_ascii=False))
            proof = {"protocol":initialized["protocolVersion"], "tools":tools, "created":created, "verified":verified, "disk":disk}
        finally:
            process.stdin.close()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.terminate()
                process.wait(timeout=5)
            reader.join(timeout=5)
            process.stdout.close()
        while not inbox.empty():
            line = inbox.get_nowait()
            if line is not None:
                parse(line)
        assert process.returncode == 0, f"server exit {process.returncode}"
    proof["stdout_messages"] = received
    (state_dir / "probe-proof.json").write_text(json.dumps(proof, ensure_ascii=False, indent=2), encoding="utf-8")
    print("RAW PROBE PASS: 5 tools; create/get/disk identical; stdout JSON only")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-dir", type=Path, help="New isolated directory; retained proof, never overwrite state")
    args = parser.parse_args()
    if args.state_dir:
        probe(args.state_dir)
    else:
        with tempfile.TemporaryDirectory(prefix="phase1-raw-probe-") as folder:
            probe(Path(folder))


if __name__ == "__main__":
    main()
