import logging
import os
import sys
from pathlib import Path
from mcp import Client, StdioServerParameters
from policy_agent.models import ToolSpec

logger = logging.getLogger(__name__)


def server_parameters(
    root: Path,
    requests_path: Path | None = None,
    logs_dir: Path | None = None,
) -> StdioServerParameters:
    root = Path(root).resolve()
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root / "src") + os.pathsep + env.get("PYTHONPATH", "")
    env["PYTHONUNBUFFERED"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    env["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
    env["TOKENIZERS_PARALLELISM"] = "false"
    if requests_path is not None:
        env["REQUESTS_PATH"] = str(Path(requests_path).resolve())
    if logs_dir is not None:
        env["LOGS_DIR"] = str(Path(logs_dir).resolve())
    return StdioServerParameters(
        command=str(Path(sys.executable).resolve()),
        args=["-m", "policy_agent.mcp_server.server"],
        cwd=str(root),
        env=env,
    )


class MCPToolClient:
    def __init__(
        self,
        *,
        root: Path | None = None,
        requests_path: Path | None = None,
        logs_dir: Path | None = None,
    ):
        base_root = Path(root) if root is not None else Path(__file__).resolve().parents[3]
        self.parameters = server_parameters(base_root, requests_path, logs_dir)
        self._client = None

    async def __aenter__(self):
        client = Client(self.parameters, read_timeout_seconds=45)
        await client.__aenter__()
        self._client = client
        return self


    async def __aexit__(self, exc_type, exc, tb):
        client, self._client = self._client, None
        if client is not None:
            return await client.__aexit__(exc_type, exc, tb)

    async def list_tools(self) -> list[ToolSpec]:
        if self._client is None:
            raise RuntimeError("Client not connected")
        tools = []
        cursor = None
        while True:
            result = await self._client.list_tools(cursor=cursor)
            for tool in result.tools:
                tools.append(ToolSpec(
                    name=tool.name,
                    description=tool.description or "",
                    input_schema=tool.input_schema,
                ))
            cursor = result.next_cursor
            if not cursor:
                return tools

    async def call_tool(self, name: str, args: dict) -> str:
        if self._client is None:
            return "Error: client not connected"
        try:
            result = await self._client.call_tool(name, args)
            text_blocks = []
            for item in result.content:
                if item.type == "text":
                    text_blocks.append(item.text)
            merged_text = "\n".join(text_blocks)
            if result.is_error and not merged_text.startswith("Error:"):
                return "Error: " + (merged_text or "tool rejected call")
            return merged_text
        except Exception as exc:
            logger.warning("MCP tool call error: %s (%s)", name, type(exc).__name__)
            return "Error: MCP call failed (" + type(exc).__name__ + ")"
