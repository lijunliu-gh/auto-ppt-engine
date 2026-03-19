"""MCP Server for auto-ppt-prototype.

Exposes ``create_deck`` and ``revise_deck`` as MCP tools so that
Claude Desktop, Cursor, Windsurf, and other MCP-compatible AI environments
can natively invoke PowerPoint generation and revision.

Usage (stdio transport — the default for local MCP):

    python mcp_server.py

Or via the ``mcp`` CLI for development inspection:

    mcp dev mcp_server.py
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Annotated

from mcp.server.fastmcp import FastMCP

from python_backend.skill_api import handle_skill_request
from python_backend.smart_layer import ROOT_DIR

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger("auto-ppt.mcp")

mcp = FastMCP(
    "auto-ppt-prototype",
    instructions="AI-agent-ready PowerPoint backend: plan, revise, and render PPTX decks from natural-language prompts.",
)


@mcp.tool()
def create_deck(
    prompt: Annotated[str, "Natural-language description of the presentation to create"],
    sources: Annotated[list[str] | None, "Optional list of file paths or URLs to use as trusted source material"] = None,
    template: Annotated[str | None, "Path to a .pptx brand template file. When set, renders via python-pptx instead of JS"] = None,
    mock: Annotated[bool, "Use the offline mock planner instead of calling an LLM"] = False,
    research: Annotated[bool, "Run Tavily web research before planning (requires TAVILY_API_KEY)"] = False,
    output_dir: Annotated[str | None, "Directory for output files (defaults to ./output)"] = None,
) -> str:
    """Create a new PowerPoint deck from a natural-language prompt.

    Returns a JSON summary with paths to the generated deck JSON and PPTX files,
    slide count, and any assumptions made during planning.
    """
    logger.info("MCP create_deck: prompt=%r, mock=%s, sources=%d", prompt, mock, len(sources or []))

    base_dir = str(Path.cwd())
    request: dict = {
        "action": "create",
        "prompt": prompt,
        "mock": mock,
        "research": research,
        "_baseDir": base_dir,
    }
    if sources:
        request["sources"] = [{"path": s} if not s.startswith(("http://", "https://")) else {"url": s} for s in sources]
    if template:
        request["template"] = template
    if output_dir:
        out = Path(output_dir)
        request["outputJson"] = str(out / "mcp-generated-deck.json")
        request["outputPptx"] = str(out / "mcp-generated-deck.pptx")

    result = handle_skill_request(request, response_path=None)
    return json.dumps(result, indent=2, ensure_ascii=False)


@mcp.tool()
def revise_deck(
    prompt: Annotated[str, "Natural-language revision instruction"],
    deck_path: Annotated[str, "Path to the existing deck JSON file to revise"],
    sources: Annotated[list[str] | None, "Optional additional source file paths or URLs"] = None,
    template: Annotated[str | None, "Path to a .pptx brand template file. When set, renders via python-pptx instead of JS"] = None,
    mock: Annotated[bool, "Use the offline mock planner instead of calling an LLM"] = False,
    research: Annotated[bool, "Run Tavily web research before revision (requires TAVILY_API_KEY)"] = False,
    output_dir: Annotated[str | None, "Directory for output files (defaults to ./output)"] = None,
) -> str:
    """Revise an existing PowerPoint deck based on a natural-language instruction.

    The deck_path must point to a valid deck JSON file previously generated
    by create_deck or this tool's revision output.

    Returns a JSON summary with paths to the revised deck JSON and PPTX files.
    """
    logger.info("MCP revise_deck: prompt=%r, deck=%s, mock=%s", prompt, deck_path, mock)

    base_dir = str(Path.cwd())
    request: dict = {
        "action": "revise",
        "prompt": prompt,
        "deckPath": deck_path,
        "mock": mock,
        "research": research,
        "_baseDir": base_dir,
    }
    if sources:
        request["sources"] = [{"path": s} if not s.startswith(("http://", "https://")) else {"url": s} for s in sources]
    if template:
        request["template"] = template
    if output_dir:
        out = Path(output_dir)
        request["outputJson"] = str(out / "mcp-revised-deck.json")
        request["outputPptx"] = str(out / "mcp-revised-deck.pptx")

    result = handle_skill_request(request, response_path=None)
    return json.dumps(result, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    mcp.run()
