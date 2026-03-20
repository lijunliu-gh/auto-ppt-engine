from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from python_backend import ROOT_DIR, read_text_file, resolve_path
from python_backend.skill_api import handle_skill_request

DEFAULT_CREATE_JSON = Path("output") / "py-generated-deck.json"
DEFAULT_CREATE_PPTX = Path("output") / "py-generated-deck.pptx"
DEFAULT_REVISE_JSON = Path("output") / "py-revised-deck.json"
DEFAULT_REVISE_PPTX = Path("output") / "py-revised-deck.pptx"
DEFAULT_ENV_PATH = ROOT_DIR / ".env"

PROVIDER_PRESETS = {
    "openai": {
        "key_name": "OPENAI_API_KEY",
        "default_model": "gpt-4.1-mini",
        "base_url": None,
        "provider_label": "OpenAI / reasoning models",
    },
    "openrouter": {
        "key_name": "OPENROUTER_API_KEY",
        "default_model": "openai/gpt-4.1-mini",
        "base_url": None,
        "provider_label": "OpenRouter",
    },
    "anthropic": {
        "key_name": "ANTHROPIC_API_KEY",
        "default_model": "claude-sonnet-4-20250514",
        "base_url": None,
        "provider_label": "Anthropic Claude",
    },
    "gemini": {
        "key_name": "GOOGLE_API_KEY",
        "default_model": "gemini-2.5-pro",
        "base_url": None,
        "provider_label": "Google Gemini",
    },
    "openai-compatible": {
        "key_name": "OPENAI_API_KEY",
        "default_model": "qwen-plus",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "provider_label": "OpenAI-compatible endpoint",
    },
}


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="auto-ppt",
        description="Official CLI for generating and revising PowerPoint decks.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init", help="Create or update local .env configuration")
    init.add_argument(
        "--provider",
        choices=list(PROVIDER_PRESETS.keys()),
        help="LLM provider preset to configure",
    )
    init.add_argument("--api-key", help="API key to write into the local .env file")
    init.add_argument("--model", help="Default model to use")
    init.add_argument("--base-url", help="Base URL for OpenAI-compatible endpoints")
    init.add_argument("--output-dir", help="Default output directory to write into .env")
    init.add_argument("--env-file", default=str(DEFAULT_ENV_PATH), help="Path to the .env file to write")
    init.add_argument("--non-interactive", action="store_true", help="Fail instead of prompting for missing values")

    generate = subparsers.add_parser("generate", help="Create a new deck from a prompt")
    _add_common_generation_args(generate)

    revise = subparsers.add_parser("revise", help="Revise an existing deck from a prompt")
    _add_common_generation_args(revise)
    revise.add_argument(
        "--deck",
        "--input-deck",
        dest="deck",
        help="Existing deck JSON file to revise (default: the generated deck in your configured output directory)",
    )

    score = subparsers.add_parser("score", help="Run quality scorecard on a deck JSON file")
    score.add_argument("deck", help="Path to the deck JSON file to score")

    return parser


def _add_common_generation_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--prompt", help="Presentation request in natural language")
    parser.add_argument("--prompt-file", help="Read the prompt from a text file")
    parser.add_argument("--source", action="append", default=[], help="Source file path or URL to include")
    parser.add_argument(
        "--context-file",
        action="append",
        default=[],
        help="Extra context material to include in planning",
    )
    parser.add_argument("--template", help="Optional .pptx template path")
    parser.add_argument("--research", action="store_true", help="Enable optional web research")
    parser.add_argument("--mock", action="store_true", help="Use the local mock planner instead of an LLM")
    parser.add_argument("--output-dir", help="Directory for output files")
    parser.add_argument("--output-name", help="Base filename for outputs, without extension")
    parser.add_argument("--out-json", help="Explicit path for deck JSON output")
    parser.add_argument("--out-pptx", help="Explicit path for PPTX output")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = create_parser()
    args = parser.parse_args(argv)
    if args.command in ("init", "score"):
        return args
    if args.prompt_file:
        args.prompt = read_text_file(resolve_path(args.prompt_file))
    if not args.prompt or not args.prompt.strip():
        parser.error("A prompt is required. Use --prompt or --prompt-file.")
    return args


def _is_url(value: str) -> bool:
    return value.startswith(("http://", "https://"))


def _resolve_user_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (Path.cwd() / path).resolve()


def validate_runtime_inputs(args: argparse.Namespace) -> None:
    if args.command == "revise":
        deck_path = _resolve_user_path(resolve_input_deck_path(args))
        if not deck_path.exists():
            raise RuntimeError(
                f"Deck file not found: {deck_path}. "
                "Run ./auto-ppt generate first or pass --deck with an existing deck JSON file."
            )

    if getattr(args, "template", None):
        template_path = _resolve_user_path(args.template)
        if not template_path.exists():
            raise RuntimeError(
                f"Template file not found: {template_path}. "
                "Check --template or remove it to use the default renderer."
            )

    for source in getattr(args, "source", []) or []:
        if _is_url(source):
            continue
        source_path = _resolve_user_path(source)
        if not source_path.exists():
            raise RuntimeError(
                f"Source file not found: {source_path}. "
                "Check --source or remove it from the command."
            )

    for context_file in getattr(args, "context_file", []) or []:
        context_path = _resolve_user_path(context_file)
        if not context_path.exists():
            raise RuntimeError(
                f"Context file not found: {context_path}. "
                "Check --context-file or remove it from the command."
            )


def build_request(args: argparse.Namespace) -> dict:
    base_dir = Path.cwd()
    request: dict = {
        "action": "create" if args.command == "generate" else "revise",
        "prompt": args.prompt,
        "mock": bool(args.mock),
        "research": bool(args.research),
        "_baseDir": str(base_dir),
    }

    if args.source:
        request["sources"] = [
            {"url": value} if value.startswith(("http://", "https://")) else {"path": value}
            for value in args.source
        ]
    if args.context_file:
        request["contextFiles"] = list(args.context_file)
    if args.template:
        request["template"] = args.template
    if args.command == "revise":
        request["deckPath"] = resolve_input_deck_path(args)

    output_json, output_pptx = _resolve_output_paths(args)
    request["outputJson"] = str(output_json)
    request["outputPptx"] = str(output_pptx)
    return request


def _resolve_output_paths(args: argparse.Namespace) -> tuple[Path, Path]:
    default_output_dir = os.getenv("AUTO_PPT_OUTPUT_DIR")
    if args.output_dir:
        base = Path(args.output_dir)
    elif default_output_dir:
        base = Path(default_output_dir)
    else:
        base = None

    default_json_name, default_pptx_name = _default_output_names(args)

    if base is not None:
        default_json = base / default_json_name
        default_pptx = base / default_pptx_name
    else:
        default_json = Path("output") / default_json_name
        default_pptx = Path("output") / default_pptx_name

    output_json = Path(args.out_json) if args.out_json else default_json
    output_pptx = Path(args.out_pptx) if args.out_pptx else default_pptx
    return output_json, output_pptx


def _default_output_names(args: argparse.Namespace) -> tuple[str, str]:
    if args.output_name:
        stem = args.output_name
        return f"{stem}.json", f"{stem}.pptx"
    if args.command == "generate":
        return DEFAULT_CREATE_JSON.name, DEFAULT_CREATE_PPTX.name
    return DEFAULT_REVISE_JSON.name, DEFAULT_REVISE_PPTX.name


def resolve_input_deck_path(args: argparse.Namespace) -> str:
    if getattr(args, "deck", None):
        return args.deck
    default_output_dir = os.getenv("AUTO_PPT_OUTPUT_DIR")
    if default_output_dir:
        return str(Path(default_output_dir) / DEFAULT_CREATE_JSON.name)
    return str(DEFAULT_CREATE_JSON)


def load_local_env(env_path: Path = DEFAULT_ENV_PATH) -> None:
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if value.startswith(('"', "'")) and value.endswith(('"', "'")) and len(value) >= 2:
            value = value[1:-1]
        os.environ.setdefault(key, value)


def read_env_file(env_path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not env_path.exists():
        return values
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def write_env_file(env_path: Path, values: dict[str, str]) -> None:
    lines = [f"{key}={value}" for key, value in values.items()]
    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _prompt_value(prompt: str, default: str | None = None, secret: bool = False) -> str:
    suffix = f" [{default}]" if default else ""
    rendered = f"{prompt}{suffix}: "
    if secret:
        import getpass

        value = getpass.getpass(rendered)
    else:
        value = input(rendered)
    value = value.strip()
    return value or (default or "")


def run_init(args: argparse.Namespace) -> int:
    env_path = resolve_path(args.env_file)
    current = read_env_file(env_path)

    provider = args.provider
    if not provider:
        if args.non_interactive:
            print("auto-ppt init: --provider is required in non-interactive mode", file=sys.stderr)
            return 1
        print("Choose a provider:")
        names = list(PROVIDER_PRESETS.keys())
        for index, name in enumerate(names, start=1):
            print(f"{index}. {name} ({PROVIDER_PRESETS[name]['provider_label']})")
        choice = _prompt_value("Provider number", "1")
        try:
            provider = names[int(choice) - 1]
        except Exception:  # noqa: BLE001
            print("auto-ppt init: invalid provider selection", file=sys.stderr)
            return 1

    preset = PROVIDER_PRESETS[provider]
    key_name = preset["key_name"]
    api_key = args.api_key or current.get(key_name) or os.getenv(key_name)
    if not api_key:
        if args.non_interactive:
            print(f"auto-ppt init: --api-key is required for provider {provider}", file=sys.stderr)
            return 1
        api_key = _prompt_value(f"{key_name}", secret=True)
    if not api_key:
        print(f"auto-ppt init: {key_name} cannot be empty", file=sys.stderr)
        return 1

    model = args.model or current.get("OPENAI_MODEL") or os.getenv("OPENAI_MODEL") or preset["default_model"]
    if not args.model and not args.non_interactive:
        model = _prompt_value("Default model", model)

    base_url_default = args.base_url or current.get("OPENAI_BASE_URL") or os.getenv("OPENAI_BASE_URL") or preset["base_url"] or ""
    base_url = base_url_default
    if provider == "openai-compatible" and not args.base_url and not args.non_interactive:
        base_url = _prompt_value("Base URL", base_url_default)

    output_dir = args.output_dir or current.get("AUTO_PPT_OUTPUT_DIR") or os.getenv("AUTO_PPT_OUTPUT_DIR") or "output"
    if not args.output_dir and not args.non_interactive:
        output_dir = _prompt_value("Default output directory", output_dir)

    new_values = {
        "OPENAI_API_KEY": current.get("OPENAI_API_KEY", ""),
        "OPENAI_MODEL": model,
        "OPENAI_BASE_URL": current.get("OPENAI_BASE_URL", ""),
        "OPENROUTER_API_KEY": current.get("OPENROUTER_API_KEY", ""),
        "ANTHROPIC_API_KEY": current.get("ANTHROPIC_API_KEY", ""),
        "GOOGLE_API_KEY": current.get("GOOGLE_API_KEY", ""),
        "TAVILY_API_KEY": current.get("TAVILY_API_KEY", ""),
        "AUTO_PPT_OUTPUT_DIR": output_dir,
    }
    for env_key in ("OPENAI_API_KEY", "OPENROUTER_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY"):
        new_values[env_key] = ""
    new_values[key_name] = api_key
    new_values["OPENAI_MODEL"] = model
    new_values["OPENAI_BASE_URL"] = base_url if provider == "openai-compatible" else ""

    env_path.parent.mkdir(parents=True, exist_ok=True)
    write_env_file(env_path, new_values)

    print(f"Wrote configuration to: {env_path}")
    print(f"Provider: {provider}")
    print(f"Model: {model}")
    print(f"Default output directory: {output_dir}")
    print("Next step:")
    print('  ./auto-ppt generate --prompt "Create a 6-slide deck about AI agents"')
    return 0


def format_user_error(error: Exception) -> str:
    message = str(error).strip()

    if "API_KEY is not set" in message:
        return (
            f"auto-ppt: error: {message}\n"
            "Hint: run ./auto-ppt init to configure a provider, or add --mock to test the pipeline without a model."
        )

    if message.startswith("Deck file not found:"):
        return f"auto-ppt: error: {message}"

    if message.startswith("Template file not found:"):
        return f"auto-ppt: error: {message}"

    if message.startswith("Source file not found:"):
        return f"auto-ppt: error: {message}"

    if message.startswith("Context file not found:"):
        return f"auto-ppt: error: {message}"

    if message.startswith("File not found:"):
        return (
            f"auto-ppt: error: {message}\n"
            "Hint: check the file path and run the command from the repository root, or pass an absolute path."
        )

    if message.startswith("Template not found:"):
        return (
            f"auto-ppt: error: {message}\n"
            "Hint: verify the template path, or remove --template to use the default renderer."
        )

    if message.startswith("Node renderer timed out"):
        return (
            f"auto-ppt: error: {message}\n"
            "Hint: try a smaller deck, then rerun. If the problem persists, verify Node.js is installed and working."
        )

    if message.startswith("Node renderer failed:"):
        return (
            f"auto-ppt: error: {message}\n"
            "Hint: run npm install, verify Node.js 18+ is available, and rerun the command."
        )

    if message == "Model output did not contain a JSON object.":
        return (
            "auto-ppt: error: The model response was not valid deck JSON.\n"
            "Hint: rerun the command, try a different model, or use --mock to verify the local pipeline first."
        )

    if message == "Model returned no content.":
        return (
            "auto-ppt: error: The model returned no usable content.\n"
            "Hint: rerun the command, check your provider/model configuration, or switch models with ./auto-ppt init."
        )

    return f"auto-ppt: error: {message}"


def run_score(args: argparse.Namespace) -> int:
    import json
    from python_backend.quality_scorer import score_deck

    deck_path = _resolve_user_path(args.deck)
    if not deck_path.exists():
        print(f"auto-ppt: error: Deck file not found: {deck_path}", file=sys.stderr)
        return 1
    deck = json.loads(deck_path.read_text(encoding="utf-8"))
    result = score_deck(deck)

    print(result["summary"])
    print(f"Hard: {result['hard_score']}  Soft: {result['soft_score']}")
    if result["hard_failures"]:
        print("\nHard failures:")
        for cat, issues in result["hard_failures"].items():
            for issue in issues:
                print(f"  [{cat}] {issue}")
    if result["soft_warnings"]:
        print("\nSoft warnings:")
        for cat, issues in result["soft_warnings"].items():
            for issue in issues:
                print(f"  [{cat}] {issue}")
    return 0 if result["pass"] else 1


def main(argv: list[str] | None = None) -> int:
    try:
        load_local_env()
        args = parse_args(argv)
        if args.command == "init":
            return run_init(args)
        if args.command == "score":
            return run_score(args)
        validate_runtime_inputs(args)
        response = handle_skill_request(build_request(args), response_path=None)
    except Exception as error:  # noqa: BLE001
        print(format_user_error(error), file=sys.stderr)
        return 1

    verb = "Generated" if response.get("action") == "create" else "Revised"
    print(f"Action: {response['action']}")
    print(f"Deck JSON: {response['deckJsonPath']}")
    print(f"PPTX: {response['pptxPath']}")
    print(f"Renderer: {response['renderer']}")
    print(f"Slides: {response['slideCount']}")
    if response.get("sourcesUsed"):
        print(f"Sources used: {len(response['sourcesUsed'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())