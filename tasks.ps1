# Windows fallback for the Makefile (same targets). Usage: .\tasks.ps1 setup ; .\tasks.ps1 demo
param([Parameter(Mandatory = $true)][string]$Target)

switch ($Target) {
    "setup" { uv sync; if ($?) { uv run python -m policy_agent.rag.build_index } }
    "index" { uv run python -m policy_agent.rag.build_index }
    "demo"  { uv run python scripts/demo.py }
    "chat"  { uv run python scripts/chat.py }
    "eval"  { uv run python -m policy_agent.eval.run_eval }
    "probe" { uv run python scripts/probe_server.py }
    "host2" { uv run python scripts/second_host.py }
    "test"  { uv run pytest -q }
    "clean" { Remove-Item -Recurse -Force data/index -ErrorAction SilentlyContinue }
    default { Write-Error "Unknown target '$Target'. Use: setup index demo chat eval probe host2 test clean" }
}
