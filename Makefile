.PHONY: setup setup-env check-env index demo chat eval probe host2 server test clean

setup:
	uv sync
	uv run python -m policy_agent.rag.build_index

setup-env:
	uv sync --locked

check-env:
	uv run python scripts/check_environment.py

index:
	uv run python -m policy_agent.rag.build_index

demo:
	uv run python scripts/demo.py

chat:
	uv run python scripts/chat.py

eval:
	uv run python -m policy_agent.eval.run_eval --mode both

probe:
	uv run python scripts/probe_server.py

host2:
	uv run python scripts/second_host.py

server:
	uv run python -m policy_agent.mcp_server.server

test:
	uv run pytest -q

clean:
	uv run python -c "import shutil; shutil.rmtree('data/index', ignore_errors=True)"
