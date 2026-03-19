from __future__ import annotations

import argparse

from python_backend import (
    ROOT_DIR,
    ensure_parent_dir,
    execute_planning_flow,
    load_source_contexts,
    read_text_file,
    render_deck_via_node,
    resolve_path,
)

DEFAULT_JSON_OUTPUT = ROOT_DIR / "output" / "py-generated-deck.json"
DEFAULT_PPTX_OUTPUT = ROOT_DIR / "output" / "py-generated-deck.pptx"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a PowerPoint deck through the Python smart layer.")
    parser.add_argument("--prompt", help="Presentation request in natural language")
    parser.add_argument("--prompt-file", help="Read the request from a text file")
    parser.add_argument("--out-json", default=str(DEFAULT_JSON_OUTPUT), help="Where to save the generated deck JSON")
    parser.add_argument("--out-pptx", default=str(DEFAULT_PPTX_OUTPUT), help="Where to save the generated PPTX file")
    parser.add_argument("--context-file", action="append", default=[], help="Extra context material to include in planning")
    parser.add_argument("--source", action="append", default=[], help="Source file path or URL to include in planning")
    parser.add_argument("--research", action="store_true", help="Attempt optional web research when TAVILY_API_KEY is configured")
    parser.add_argument("--mock", action="store_true", help="Skip model calls and use the local heuristic planner")
    args = parser.parse_args()
    if args.prompt_file:
        args.prompt = read_text_file(resolve_path(args.prompt_file))
    if not args.prompt or not args.prompt.strip():
        parser.error("A presentation prompt is required. Use --prompt or --prompt-file.")
    return args


def main() -> None:
    args = parse_args()
    context_texts = [read_text_file(resolve_path(path)) for path in args.context_file]
    source_data = load_source_contexts(args.source, ROOT_DIR)
    deck = execute_planning_flow(
        prompt=args.prompt,
        context_texts=context_texts + source_data["context_texts"],
        loaded_sources=source_data["loaded_sources"],
        research_enabled=args.research,
        mock=args.mock,
        mode="create",
    )
    output_json = resolve_path(args.out_json)
    output_pptx = resolve_path(args.out_pptx)
    ensure_parent_dir(output_json)
    render_deck_via_node(deck, output_json, output_pptx, ROOT_DIR)
    print(f"Deck JSON saved to: {output_json}")
    if source_data["loaded_sources"]:
        print(f"Loaded sources: {len(source_data['loaded_sources'])}")


if __name__ == "__main__":
    main()
