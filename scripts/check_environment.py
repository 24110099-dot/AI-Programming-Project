"""Check project imports without reading credentials or calling external services."""

import sys
from importlib import import_module
from importlib.metadata import version


def main() -> int:
    if sys.version_info < (3, 11):
        print("Error: Python 3.11 or newer is required.", file=sys.stderr)
        return 1
    for name in ("policy_agent", "groq", "mcp", "rank_bm25", "dotenv"):
        import_module(name)
    from mcp import Client
    from mcp.server import MCPServer

    print(f"Python: {sys.version.split()[0]}")
    print(f"Executable: {sys.executable}")
    print(f"MCP: {version('mcp')}")
    print("MCP v2 Client/MCPServer: ok")
    print("Project imports: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
