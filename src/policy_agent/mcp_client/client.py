"""MCP Client adapter ket noi toi MCP Server qua stdio (Tuan 7).

Kham pha cong cu dong (Dynamic Tool Discovery): Khong bao gio hardcode danh sach tool.
Goi cac tool mot cach an toan va tra ve ket qua dang chuoi.
Nguoi phu trach: SV C (Khang).
"""

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
    """Cau hinh tham so khoi chay MCP Server qua stdio."""
    root = Path(root).resolve()
    env = os.environ.copy()
    # Dam bao server tim thay package policy_agent trong src/
    env["PYTHONPATH"] = str(root / "src") + os.pathsep + env.get("PYTHONPATH", "")
    env["PYTHONUNBUFFERED"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"

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
    """Client giao tiep voi MCP Server qua kenh stdio JSON-RPC."""

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
        client = Client(self.parameters, read_timeout_seconds=15)
        await client.__aenter__()
        self._client = client
        return self

    async def __aexit__(self, exc_type, exc, tb):
        client, self._client = self._client, None
        if client is not None:
            return await client.__aexit__(exc_type, exc, tb)

    async def list_tools(self) -> list[ToolSpec]:
        """Kham pha danh sach cong cu duoc dang ky tren MCP Server (Dynamic Discovery)."""
        if self._client is None:
            raise RuntimeError("Can su dung 'async with MCPToolClient()'")

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
        """Goi mot cong cu tren MCP Server va tra ve text ket qua."""
        if self._client is None:
            return "Error: client not connected"

        try:
            result = await self._client.call_tool(name, args)
            text_blocks = [item.text for item in result.content if item.type == "text"]
            merged_text = "\n".join(text_blocks)

            if result.is_error and not merged_text.startswith("Error:"):
                return "Error: " + (merged_text or "tool rejected call")
            return merged_text

        except Exception as exc:
            logger.warning("MCP tool call error: %s (%s)", name, type(exc).__name__)
            return "Error: MCP call failed (" + type(exc).__name__ + ")"
