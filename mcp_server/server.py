"""MCP server — exposes rag_search, get_weather, get_transport_options as tools."""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

# Make sure `tools/` is importable when this script is spawned as a subprocess.
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from mcp import types
from mcp.server import Server
from mcp.server.stdio import stdio_server

from tools.rag_tool import RAGSearchTool
from tools.transport_tool import TransportTool
from tools.weather_tool import WeatherTool

_DATA_PATH = str(Path(__file__).parent.parent / "data" / "jaipur_places.txt")
_CHROMA_DIR = os.getenv("CHROMA_PERSIST_DIR", str(Path(__file__).parent.parent / "chroma_db"))

rag = RAGSearchTool(data_path=_DATA_PATH, persist_dir=_CHROMA_DIR)
weather = WeatherTool()
transport = TransportTool()

server = Server(name="itinerary-mcp", version="1.0.0")


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="rag_search",
            description="Semantic search over the Jaipur places knowledge base. Returns relevant place descriptions.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Natural language search query"},
                    "top_k": {"type": "integer", "default": 3, "description": "Number of results"},
                },
                "required": ["query"],
            },
        ),
        types.Tool(
            name="get_weather",
            description="Fetch current weather and 3-day forecast for a city.",
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {"type": "string"},
                    "country_code": {"type": "string", "default": "IN"},
                },
                "required": ["city"],
            },
        ),
        types.Tool(
            name="get_transport_options",
            description="Get local and intercity transport options for a city, including costs and booking methods.",
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {"type": "string"},
                },
                "required": ["city"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name == "rag_search":
        result = rag.search(
            query=arguments["query"],
            top_k=arguments.get("top_k", 3),
        )
    elif name == "get_weather":
        result = weather.get_weather(
            city=arguments["city"],
            country_code=arguments.get("country_code", "IN"),
        )
    elif name == "get_transport_options":
        result = transport.get_transport_options(city=arguments["city"])
    else:
        result = f"Unknown tool: {name}"

    return [types.TextContent(type="text", text=result)]


async def main() -> None:
    async with stdio_server() as streams:
        await server.run(*streams, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
