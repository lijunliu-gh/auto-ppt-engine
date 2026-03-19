from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

from .js_renderer import render_deck_via_node
from .smart_layer import ROOT_DIR, ensure_parent_dir, execute_planning_flow, read_text_file, resolve_path
from .source_loader import load_source_contexts

DEFAULT_REQUEST_PATH = ROOT_DIR / "sample-agent-request.json"
DEFAULT_RESPONSE_PATH = ROOT_DIR / "output" / "py-agent-response.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Python JSON skill entrypoint.")
    parser.add_argument("--request", default=str(DEFAULT_REQUEST_PATH), help="JSON request payload for the skill")
    parser.add_argument("--response", default=str(DEFAULT_RESPONSE_PATH), help="Where to save the JSON response payload")
    return parser.parse_args()


def load_request(file_path: str | Path) -> Dict[str, Any]:
    payload = json.loads(read_text_file(file_path))
    if not isinstance(payload, dict):
        raise RuntimeError("Request payload must be a JSON object.")
    if payload.get("action") not in {"create", "revise"}:
        raise RuntimeError('Request payload action must be either "create" or "revise".')
    if not isinstance(payload.get("prompt"), str) or not payload["prompt"].strip():
        raise RuntimeError("Request payload prompt is required.")
    payload["_baseDir"] = str(Path(file_path).resolve().parent)
    return payload


def resolve_from_base(base_dir: str | Path, file_path: str) -> Path:
    path = Path(file_path)
    return path if path.is_absolute() else (Path(base_dir) / path).resolve()


def handle_skill_request(request: Dict[str, Any], response_path: str | Path | None = None) -> Dict[str, Any]:
    request_base_dir = Path(request.get("_baseDir") or ROOT_DIR)
    context_texts = []
    for file_path in request.get("contextFiles", []) or []:
        context_texts.append(read_text_file(resolve_from_base(request_base_dir, file_path)))

    source_data = load_source_contexts(request.get("sources", []) or [], request_base_dir)
    existing_deck = None
    if request.get("action") == "revise" and request.get("deckPath"):
        existing_deck = json.loads(read_text_file(resolve_from_base(request_base_dir, request["deckPath"])))

    deck = execute_planning_flow(
        prompt=request["prompt"],
        context_texts=context_texts + source_data["context_texts"],
        loaded_sources=source_data["loaded_sources"],
        research_enabled=bool(request.get("research")),
        mock=bool(request.get("mock")),
        mode=request["action"],
        existing_deck=existing_deck,
    )

    output_json = resolve_from_base(
        request_base_dir,
        request.get("outputJson")
        or ("output/py-agent-revised-deck.json" if request["action"] == "revise" else "output/py-agent-generated-deck.json"),
    )
    output_pptx = resolve_from_base(
        request_base_dir,
        request.get("outputPptx")
        or ("output/py-agent-revised-deck.pptx" if request["action"] == "revise" else "output/py-agent-generated-deck.pptx"),
    )

    ensure_parent_dir(output_json)
    render_deck_via_node(deck, output_json, output_pptx, ROOT_DIR)

    response = {
        "ok": True,
        "engine": "python-smart-layer",
        "action": request["action"],
        "prompt": request["prompt"],
        "deckJsonPath": str(output_json),
        "pptxPath": str(output_pptx),
        "slideCount": deck["slideCount"],
        "assumptions": deck.get("assumptions", []),
        "sourcesUsed": [
            {
                "label": source.get("label"),
                "type": source.get("type"),
                "location": source.get("location"),
                "trustLevel": source.get("trustLevel"),
                "priority": source.get("priority"),
            }
            for source in source_data["loaded_sources"]
        ],
    }

    if response_path:
        resolved_response_path = resolve_path(response_path)
        ensure_parent_dir(resolved_response_path)
        resolved_response_path.write_text(json.dumps(response, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Skill response saved to: {resolved_response_path}")

    return response


def main() -> None:
    args = parse_args()
    request = load_request(args.request)
    handle_skill_request(request, args.response)


if __name__ == "__main__":
    main()
