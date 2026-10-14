.PHONY: setup setup-env check-env test probe server
setup: setup-env
setup-env:
	uv sync --locked
check-env:
	uv run --locked python scripts/check_environment.py
test:
	uv run --locked pytest -q tests/test_request_store.py tests/test_server.py tests/test_mcp_client.py tests/test_probe.py
probe:
	uv run --locked python scripts/probe_server.py
server:
	uv run --locked python -m policy_agent.mcp_server.server
