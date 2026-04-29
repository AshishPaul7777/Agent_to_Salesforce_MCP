from __future__ import annotations

import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

_SERVER_SCRIPT = str(Path(__file__).parent.parent / "mcp_server" / "server.py")


class MCPClient:
    """Thin async wrapper around MCP ClientSession."""

    def __init__(self) -> None:
        self._session: ClientSession | None = None
        self._cm = None
        self.tools: list = []

    async def connect(self) -> None:
        server_params = StdioServerParameters(
            command=sys.executable,
            args=[_SERVER_SCRIPT],
        )
        self._cm = stdio_client(server_params)
        read, write = await self._cm.__aenter__()
        self._session = ClientSession(read, write)
        await self._session.__aenter__()
        await self._session.initialize()

        response = await self._session.list_tools()
        self.tools = response.tools

    async def call(self, tool_name: str, **kwargs) -> str:
        if self._session is None:
            raise RuntimeError("Call connect() before using the client.")
        result = await self._session.call_tool(tool_name, arguments=kwargs)
        return result.content[0].text

    async def close(self) -> None:
        if self._session:
            await self._session.__aexit__(None, None, None)
        if self._cm:
            await self._cm.__aexit__(None, None, None)
