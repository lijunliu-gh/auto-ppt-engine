from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger("auto-ppt")
RENDER_TIMEOUT_SECONDS = 120


def render_deck_via_node(deck: Dict[str, Any], output_json_path: str | Path, output_pptx_path: str | Path, repo_root: str | Path) -> None:
    repo_root_path = Path(repo_root)
    json_path = Path(output_json_path)
    pptx_path = Path(output_pptx_path)

    json_path.parent.mkdir(parents=True, exist_ok=True)
    pptx_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(deck, indent=2, ensure_ascii=False), encoding="utf-8")

    command = [
        "node",
        str(repo_root_path / "generate-ppt.js"),
        str(json_path),
        str(pptx_path),
    ]
    logger.info("Rendering PPTX via Node: %s -> %s", json_path.name, pptx_path.name)
    try:
        result = subprocess.run(
            command, cwd=str(repo_root_path), capture_output=True, text=True,
            check=False, timeout=RENDER_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"Node renderer timed out after {RENDER_TIMEOUT_SECONDS}s")
    if result.returncode != 0:
        error_output = (result.stderr or result.stdout or "Unknown renderer error").strip()
        raise RuntimeError(f"Node renderer failed: {error_output}")
