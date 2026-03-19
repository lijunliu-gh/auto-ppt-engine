# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project follows Semantic Versioning while it remains a prototype.

## [0.3.1] - 2026-03-19

### Added

- `python_backend/llm_provider.py`: LLM provider abstraction with `LLMProvider` protocol and `OpenAIProvider` implementation, enabling future multi-model support
- `tests/test_smart_layer.py`: 39 pytest unit tests covering schema validation, inference functions, mock deck generation, heuristic revision, source loading, JSON extraction, and security checks
- `pytest>=8.0.0` added to `requirements.txt`
- `schemaVersion` field (`"0.3.0"`) added to `deck-schema.json` for forward-compatible schema migration
- Structured logging via Python `logging` module across `smart_layer.py`, `source_loader.py`, and `js_renderer.py`
- Source truncation tracking: `load_source_contexts()` now returns `truncated_sources` list; truncated sources are surfaced in deck `assumptions`

### Changed

- `execute_planning_flow()` accepts an optional `llm_provider` parameter, decoupling planning from hardcoded OpenAI calls
- Node renderer subprocess call now enforces a 120-second timeout to prevent indefinite hangs
- Legacy JS files (`deck-agent-core.js`, `source-loader.js`) marked with prominent `DEPRECATED` banners

### Fixed

- **Security: path traversal** — `_resolve_local_path()` now validates that resolved paths stay within the base directory
- **Security: SSRF** — `_fetch_url()` resolves hostnames and blocks private/loopback/reserved IP ranges before connecting
- **Security: file size DoS** — local source files exceeding 50 MB are rejected before parsing
- Removed redundant `raise RuntimeError` after `fail()` calls (3 occurrences)
- `normalize_closing_slide()` already handles empty slide lists gracefully (confirmed and tested)

## [0.3.0] - 2026-03-19

### Added

- Python smart-layer entrypoints for create, revise, skill, and HTTP service flows
- `python_backend/` package for planning, revision, source loading, skill orchestration, and JS renderer bridging
- `requirements.txt` for Python-side dependencies
- `CHANGELOG.md` for release tracking going forward

### Changed

- switched the public execution surface to Python-first commands and npm scripts
- converted legacy Node create, revise, skill, and server entrypoints into compatibility wrappers
- updated English, Simplified Chinese, and Japanese docs to reflect the Python-first architecture
- aligned sample request payloads and skill outputs around `python-smart-layer`
- marked legacy Node smart-layer and source-loader files as transitional reference implementations

### Fixed

- fixed Windows argument forwarding in the Node-to-Python compatibility bridge by disabling shell splitting

## [0.2.0] - 2026-03-19

### Added

- open-source publishing baseline with MIT license, governance docs, issue templates, PR template, and smoke CI
- agent-callable create and revise flows with JSON skill and local HTTP service support
- source-aware planning from local files and URLs
- multilingual documentation in English, Simplified Chinese, and Japanese

### Changed

- positioned the repository as an AI-agent-ready PowerPoint backend rather than a generic script

### Notes

- this release established the initial public GitHub baseline before the Python-first architecture shift