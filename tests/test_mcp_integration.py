"""MCP integration tests: exercise the MCP server through its stdio transport.

These tests spawn the MCP server as a subprocess and communicate via the MCP
protocol over stdin/stdout, simulating exactly what Claude Desktop, Cursor, or
Windsurf would do.
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
MCP_SERVER = str(ROOT / "mcp_server.py")

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    HAS_MCP_CLIENT = True
except ImportError:
    HAS_MCP_CLIENT = False

needs_mcp = pytest.mark.skipif(not HAS_MCP_CLIENT, reason="mcp client SDK not available")


async def _mcp_call_tool(tool_name: str, arguments: dict) -> dict:
    """Connect to the MCP server via stdio and call a tool."""
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[MCP_SERVER],
        cwd=str(ROOT),
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments)
            # result.content is a list of content blocks; first one has the text
            text = result.content[0].text
            return json.loads(text)


def _run(coro):
    """Run an async coroutine synchronously for pytest."""
    return asyncio.run(coro)


@needs_mcp
class TestMCPIntegrationCreate:
    """End-to-end: MCP stdio client → create_deck → deck JSON → PPTX."""

    def test_create_via_mcp_transport(self, tmp_path):
        result = _run(_mcp_call_tool("create_deck", {
            "prompt": "Integration test: 6-slide AI strategy deck",
            "mock": True,
            "output_dir": str(tmp_path),
        }))
        assert result["ok"] is True
        assert result["action"] == "create"
        assert result["slideCount"] > 0
        assert Path(result["pptxPath"]).exists()
        assert Path(result["deckJsonPath"]).exists()

        # Validate the deck JSON structure
        deck = json.loads(Path(result["deckJsonPath"]).read_text())
        assert "deckTitle" in deck
        assert "slides" in deck
        assert len(deck["slides"]) == result["slideCount"]

    def test_create_with_source_via_mcp(self, tmp_path):
        result = _run(_mcp_call_tool("create_deck", {
            "prompt": "Deck from source brief",
            "mock": True,
            "sources": [str(ROOT / "sample-source-brief.md")],
            "output_dir": str(tmp_path),
        }))
        assert result["ok"] is True
        assert len(result["sourcesUsed"]) == 1

    def test_tool_listing(self):
        """MCP server should expose exactly create_deck and revise_deck."""
        async def _list():
            server_params = StdioServerParameters(
                command=sys.executable,
                args=[MCP_SERVER],
                cwd=str(ROOT),
            )
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    tools = await session.list_tools()
                    return sorted([t.name for t in tools.tools])
        names = _run(_list())
        assert names == ["create_deck", "revise_deck"]


@needs_mcp
class TestMCPIntegrationRevise:
    """End-to-end: create → revise → verify the full chain."""

    def test_create_then_revise_via_mcp(self, tmp_path):
        # Step 1: Create
        create_result = _run(_mcp_call_tool("create_deck", {
            "prompt": "Base deck for MCP revision test",
            "mock": True,
            "output_dir": str(tmp_path),
        }))
        assert create_result["ok"] is True
        deck_path = create_result["deckJsonPath"]
        original_count = create_result["slideCount"]

        # Step 2: Revise
        revise_dir = tmp_path / "revised"
        revise_dir.mkdir()
        revise_result = _run(_mcp_call_tool("revise_deck", {
            "prompt": "Compress to 5 slides",
            "deck_path": deck_path,
            "mock": True,
            "output_dir": str(revise_dir),
        }))
        assert revise_result["ok"] is True
        assert revise_result["action"] == "revise"
        assert revise_result["slideCount"] <= 5
        assert Path(revise_result["pptxPath"]).exists()

        # Verify the revised deck JSON
        revised_deck = json.loads(Path(revise_result["deckJsonPath"]).read_text())
        assert len(revised_deck["slides"]) == revise_result["slideCount"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
