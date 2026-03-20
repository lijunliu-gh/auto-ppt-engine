"""MCP integration tests: exercise the MCP server through stdio and streamable-http transports.

These tests spawn the MCP server as a subprocess and communicate via the MCP
protocol, simulating exactly what Claude Desktop, Cursor, or Windsurf would do.
"""

from __future__ import annotations

import asyncio
import json
import socket
import subprocess
import sys
import time
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

try:
    from mcp.client.streamable_http import streamable_http_client
    HAS_HTTP_CLIENT = True
except ImportError:
    HAS_HTTP_CLIENT = False

needs_mcp = pytest.mark.skipif(not HAS_MCP_CLIENT, reason="mcp client SDK not available")
needs_http = pytest.mark.skipif(
    not (HAS_MCP_CLIENT and HAS_HTTP_CLIENT),
    reason="mcp client SDK with streamable-http not available",
)


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


# ── Streamable HTTP Transport ────────────────────────────────────────────────

def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_for_port(host: str, port: int, timeout: float = 10.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except OSError:
            time.sleep(0.2)
    return False


async def _http_call_tool(url: str, tool_name: str, arguments: dict) -> dict:
    """Connect to the MCP server via streamable-http and call a tool."""
    async with streamable_http_client(url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments)
            text = result.content[0].text
            return json.loads(text)


async def _http_list_tools(url: str) -> list[str]:
    """Connect to the MCP server via streamable-http and list tools."""
    async with streamable_http_client(url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            return sorted([t.name for t in tools.tools])


@needs_http
class TestMCPStreamableHTTP:
    """Integration tests: exercise the MCP server through streamable-http transport."""

    @pytest.fixture(autouse=True)
    def _start_server(self):
        """Start MCP server on a free port, tear down after each test."""
        self.port = _find_free_port()
        self.url = f"http://127.0.0.1:{self.port}/mcp"
        self.proc = subprocess.Popen(
            [sys.executable, MCP_SERVER,
             "--transport", "streamable-http",
             "--host", "127.0.0.1",
             "--port", str(self.port)],
            cwd=str(ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        assert _wait_for_port("127.0.0.1", self.port), \
            f"MCP HTTP server failed to start on port {self.port}"
        yield
        self.proc.terminate()
        self.proc.wait(timeout=5)

    def test_list_tools_via_http(self):
        names = _run(_http_list_tools(self.url))
        assert names == ["create_deck", "revise_deck"]

    def test_create_deck_via_http(self, tmp_path):
        result = _run(_http_call_tool(self.url, "create_deck", {
            "prompt": "HTTP transport test: 4-slide overview",
            "mock": True,
            "output_dir": str(tmp_path),
        }))
        assert result["ok"] is True
        assert result["action"] == "create"
        assert result["slideCount"] > 0
        assert Path(result["pptxPath"]).exists()

    def test_revise_deck_via_http(self, tmp_path):
        # Create first
        create_result = _run(_http_call_tool(self.url, "create_deck", {
            "prompt": "Base deck for HTTP revision",
            "mock": True,
            "output_dir": str(tmp_path),
        }))
        assert create_result["ok"] is True

        # Revise
        revise_dir = tmp_path / "revised"
        revise_dir.mkdir()
        revise_result = _run(_http_call_tool(self.url, "revise_deck", {
            "prompt": "Compress to 3 slides",
            "deck_path": create_result["deckJsonPath"],
            "mock": True,
            "output_dir": str(revise_dir),
        }))
        assert revise_result["ok"] is True
        assert revise_result["action"] == "revise"
        assert Path(revise_result["pptxPath"]).exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
