"""SDK v2 stdio adapter. Tool names/schemas are discovered, never prescribed."""
import os
import sys
from pathlib import Path
from mcp import Client, StdioServerParameters
from policy_agent.models import ToolSpec


def server_parameters(root: Path, requests_path: Path | None = None, logs_dir: Path | None = None):
    root = Path(root).resolve()
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root / "src") + os.pathsep + env.get("PYTHONPATH", "")
    env["PYTHONUNBUFFERED"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    if requests_path is not None:
        env["REQUESTS_PATH"] = str(Path(requests_path).resolve())
    if logs_dir is not None:
        env["LOGS_DIR"] = str(Path(logs_dir).resolve())
    return StdioServerParameters(command=str(Path(sys.executable).resolve()), args=["-m", "policy_agent.mcp_server.server"], cwd=str(root), env=env)


class MCPToolClient:
    def __init__(self, *, root: Path | None = None, requests_path: Path | None = None, logs_dir: Path | None = None):
        root = Path(root) if root is not None else Path(__file__).resolve().parents[3]
        self.parameters = server_parameters(root, requests_path, logs_dir)
        self._client = None

    async def __aenter__(self):
        client = Client(self.parameters, read_timeout_seconds=15)
        await client.__aenter__()
        self._client = client
        return self

    async def __aexit__(self, exc_type, exc, tb):
        client, self._client = self._client, None
        if client is not None:
            return await client.__aexit__(exc_type, exc, tb)

    async def list_tools(self) -> list[ToolSpec]:
        if self._client is None:
            raise RuntimeError("Use async with MCPToolClient()")
        tools, cursor = [], None
        while True:
            result = await self._client.list_tools(cursor=cursor)
            tools.extend(ToolSpec(tool.name, tool.description or "", tool.input_schema) for tool in result.tools)
            cursor = result.next_cursor
            if not cursor:
                return tools

    async def call_tool(self, name: str, args: dict) -> str:
        if self._client is None:
            return "Error: client not connected"
        try:
            result = await self._client.call_tool(name, args)
            text = "\n".join(item.text for item in result.content if item.type == "text")
            if result.is_error and not text.startswith("Error:"):
                return "Error: " + (text or "tool rejected call")
            return text
        except Exception as exc:
            return "Error: MCP call failed (" + type(exc).__name__ + ")"
