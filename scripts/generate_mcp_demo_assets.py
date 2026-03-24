from __future__ import annotations

import asyncio
import json
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


ROOT = Path(__file__).resolve().parent.parent
MCP_SERVER = ROOT / "mcp_server.py"
ASSET_DIR = ROOT / "assets" / "readme"
OUTPUT_DIR = ROOT / "output" / "readme-mcp-demo"

WIDTH = 1600
HEIGHT = 900
PADDING_X = 56
PADDING_Y = 46
LINE_HEIGHT = 30
TOP_BAR_HEIGHT = 44

BG = "#0B1020"
PANEL = "#111827"
TEXT = "#E5E7EB"
MUTED = "#94A3B8"
ACCENT = "#22D3EE"
GREEN = "#4ADE80"
YELLOW = "#FBBF24"


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Menlo.ttc",
        "/System/Library/Fonts/SFNSMono.ttf",
        "/Library/Fonts/Menlo.ttc",
    ]
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


FONT = _load_font(22)
FONT_SMALL = _load_font(18)
FONT_TITLE = _load_font(26)


async def _run_demo() -> tuple[list[str], dict]:
    output_dir = OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    server_params = StdioServerParameters(
        command=str(ROOT / ".venv" / "bin" / "python"),
        args=[str(MCP_SERVER)],
        cwd=str(ROOT),
    )

    transcript: list[str] = []
    transcript.append("$ python mcp_server.py")
    transcript.append("[stdio MCP server started]")
    transcript.append("")
    transcript.append("$ MCP initialize")

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            tool_names = sorted(t.name for t in tools.tools)
            transcript.append(f"tools: {', '.join(tool_names)}")
            transcript.append("")

            source_path = ROOT / "examples" / "inputs" / "sample-source-brief.md"
            arguments = {
                "prompt": "Create an 8-slide AI strategy deck for executives",
                "mock": True,
                "sources": [str(source_path)],
                "output_dir": str(output_dir),
            }

            display_arguments = {
                "prompt": arguments["prompt"],
                "mock": True,
                "sources": [str(source_path.relative_to(ROOT))],
                "output_dir": str(output_dir.relative_to(ROOT)),
            }

            transcript.append("$ MCP call create_deck")
            transcript.append(json.dumps(display_arguments, indent=2))
            transcript.append("")

            result = await session.call_tool("create_deck", arguments)
            text = result.content[0].text
            data = json.loads(text)
            deck_json_rel = Path(data.get("deckJsonPath", "")).resolve().relative_to(ROOT)
            pptx_rel = Path(data.get("pptxPath", "")).resolve().relative_to(ROOT)
            transcript.append("$ MCP result")
            transcript.append(json.dumps({
                "ok": data.get("ok"),
                "action": data.get("action"),
                "slideCount": data.get("slideCount"),
                "renderer": data.get("renderer"),
                "deckJsonPath": str(deck_json_rel),
                "pptxPath": str(pptx_rel),
            }, indent=2))

            return transcript, data


def _wrap_block(block: str, width: int = 92) -> list[tuple[str, str]]:
    lines: list[tuple[str, str]] = []
    for raw in block.splitlines() or [""]:
        if raw.startswith("$ "):
            parts = textwrap.wrap(raw, width=width, subsequent_indent="  ") or [raw]
            lines.extend((line, "accent") for line in parts)
        elif raw.startswith("tools:"):
            parts = textwrap.wrap(raw, width=width, subsequent_indent="  ") or [raw]
            lines.extend((line, "green") for line in parts)
        elif raw.startswith("[") and raw.endswith("]"):
            lines.append((raw, "muted"))
        else:
            parts = textwrap.wrap(raw, width=width, subsequent_indent="  ", replace_whitespace=False) or [raw]
            lines.extend((line, "text") for line in parts)
    return lines


def _render_frame(title: str, blocks: list[str], path: Path) -> None:
    img = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(img)

    draw.rounded_rectangle((24, 24, WIDTH - 24, HEIGHT - 24), radius=24, fill=PANEL)
    draw.rounded_rectangle((24, 24, WIDTH - 24, 24 + TOP_BAR_HEIGHT), radius=24, fill="#0F172A")
    draw.rectangle((24, 24 + TOP_BAR_HEIGHT, WIDTH - 24, 24 + TOP_BAR_HEIGHT + 12), fill="#0F172A")
    draw.ellipse((48, 38, 64, 54), fill="#EF4444")
    draw.ellipse((74, 38, 90, 54), fill="#F59E0B")
    draw.ellipse((100, 38, 116, 54), fill="#10B981")
    draw.text((140, 31), title, font=FONT_TITLE, fill=TEXT)

    x = 24 + PADDING_X
    y = 24 + TOP_BAR_HEIGHT + PADDING_Y

    color_map = {
        "text": TEXT,
        "muted": MUTED,
        "accent": ACCENT,
        "green": GREEN,
    }

    for block in blocks:
        for line, tone in _wrap_block(block):
            draw.text((x, y), line, font=FONT, fill=color_map[tone])
            y += LINE_HEIGHT
        y += 18

    footer = "Real MCP stdio round-trip against mcp_server.py · mock=true · generated assets saved under output/readme-mcp-demo"
    draw.text((x, HEIGHT - 70), footer, font=FONT_SMALL, fill=YELLOW)
    img.save(path)


def _build_frames(transcript: list[str], result: dict) -> list[Path]:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)

    blocks = [block for block in "\n".join(transcript).split("\n\n") if block.strip()]
    frames = [
        ("Auto PPT Engine · MCP Demo", blocks[:2]),
        ("Auto PPT Engine · MCP Demo", blocks[:4]),
        ("Auto PPT Engine · MCP Demo", blocks),
    ]

    frame_paths: list[Path] = []
    for idx, (title, frame_blocks) in enumerate(frames, start=1):
        frame_path = ASSET_DIR / f"mcp-demo-frame-{idx}.png"
        _render_frame(title, frame_blocks, frame_path)
        frame_paths.append(frame_path)

    poster_path = ASSET_DIR / "mcp-demo-poster.png"
    frame_paths[-1].replace(poster_path)
    frame_paths[-1] = poster_path
    return frame_paths


def _build_gif(frame_paths: list[Path]) -> Path:
    images = [Image.open(path).convert("P", palette=Image.ADAPTIVE) for path in frame_paths]
    gif_path = ASSET_DIR / "mcp-demo.gif"
    images[0].save(
        gif_path,
        save_all=True,
        append_images=images[1:],
        duration=[1200, 1700, 2600],
        loop=0,
        optimize=False,
        disposal=2,
    )
    for frame_path in frame_paths:
        if frame_path.name.startswith("mcp-demo-frame-") and frame_path.exists():
            frame_path.unlink()
    return gif_path


def main() -> None:
    transcript, result = asyncio.run(_run_demo())
    frame_paths = _build_frames(transcript, result)
    gif_path = _build_gif(frame_paths)

    transcript_path = ASSET_DIR / "mcp-demo-transcript.txt"
    transcript_path.write_text("\n".join(transcript) + "\n", encoding="utf-8")

    print(f"Wrote transcript: {transcript_path}")
    print(f"Wrote poster: {ASSET_DIR / 'mcp-demo-poster.png'}")
    print(f"Wrote GIF: {gif_path}")
    print(f"Deck JSON: {result.get('deckJsonPath')}")
    print(f"PPTX: {result.get('pptxPath')}")


if __name__ == "__main__":
    main()