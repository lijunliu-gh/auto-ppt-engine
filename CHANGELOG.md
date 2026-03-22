# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project follows Semantic Versioning while it remains a prototype.

## [Unreleased]

## [0.7.3] - 2026-03-22

### Added

- **Visual QA test suite** (`tests/test_visual_qa.py`): 44 new tests covering Issue dataclass, EMU helpers, bounding-box overlap, `_export_images` graceful degradation (soffice/pdftoppm missing), `analyze_visual_quality` heuristics (edge margin, overlap, empty slide, text-only), and `run_visual_qa` end-to-end report generation — `visual_qa.py` coverage from 18% → 98%

### Changed

- **Documentation alignment**: updated test count and coverage figures across CHANGELOG, CONTRIBUTING, ROADMAP, PRODUCT (EN/JA/ZH-CN), and README to reflect actual 409 tests / 84% coverage
- **HTTP port clarification**: integration guides (EN/JA/ZH-CN) now explain that local dev defaults to port 3010, Docker defaults to 5000, both controlled by `PORT` environment variable

## [0.7.2] - 2026-03-21

### Added

- **`pyproject.toml`**: standard Python packaging — `pip install .` replaces `pip install -r requirements.txt`; optional extras `[test]`, `[anthropic]`, `[gemini]`; `auto-ppt` CLI entry point registered via `[project.scripts]`
- **Visual QA CLI command** (`auto_ppt_cli.py`, `python_backend/visual_qa.py`): new `./auto-ppt qa-visual <deck.pptx>` workflow that runs structural visual heuristics (edge crowding, overlap candidates, empty slides), writes `visual-qa-report.json`, and optionally exports slide images when `soffice` + `pdftoppm` are available
- `--strict` mode for `qa-visual` to return non-zero on detected issues (CI-friendly quality gate)
- CLI tests for `qa-visual` command parsing and strict behavior (`tests/test_auto_ppt_cli.py`)
- **Theme System** (`generate-ppt.js`, `python_backend/template_engine.py`): Full theme architecture — all hardcoded colors, fonts, and chart palette references replaced with `_t` theme variable. Themes resolve from: `deck._theme` object → built-in theme JSON → default `business-clean` theme
- `resolveTheme()` / `mergeTheme()` in JS renderer — runtime theme resolution with fallback chain
- `resolve_theme()` / `load_theme()` / `template_config_to_theme()` in Python backend — theme bridge from templates and built-in theme files
- Theme schema (`assets/themes/theme-schema.json`) defining colors, fonts, and chartColors
- Default theme file (`assets/themes/business-clean.json`)
- `_theme` and `_nativeCharts` added to deck-schema.json as optional properties
- **5 Built-in Themes** (`assets/themes/`): `business-clean` (default), `corporate-blue`, `dark-executive`, `warm-modern`, `minimal`, `tech` — each with distinct color palette, fonts, and chart colors
- **`--theme` CLI flag** (`auto_ppt_cli.py`): Override theme via command line (e.g., `--theme dark-executive`)
- **Smart theme inference** (`smart_layer.py`): `infer_theme()` now maps to actual built-in themes based on prompt keywords (tech → `tech`, investor/board → `dark-executive`, training → `warm-modern`, internal → `minimal`, corporate → `corporate-blue`)
- **4 New Layout Types**: `kpi` (dashboard metric cards), `swot` (2×2 strategic grid), `image-text` (image + text sidebar), `funnel` (vertical pipeline visualization)
- New schema fields: `kpis`, `quadrants`, `imagePosition`, `funnel` for new layout data
- LLM prompt updated with instructions for new layout types
- Test input: `examples/inputs/new-layouts-test.json`

### Changed

- `buildDeck()` now calls `resolveTheme(deck)` to set the active theme before rendering
- All render functions (`renderTitleSlide`, `renderClosingSlide`, `renderQuoteSlide`, `renderTableSlide`, `renderChartSlide`, etc.) use theme references instead of hardcoded hex values
- Python entry points (`skill_api.py`, `py-generate-from-prompt.py`, `py-revise-deck.py`) inject `_theme` into deck JSON before Node rendering

## [0.7.1] - 2026-03-21

### Added

- **CJK Font Stack** (`generate-ppt.js`): Universal font fallback chain — `Aptos, Microsoft YaHei, PingFang SC, Meiryo, Noto Sans CJK SC` — ensures correct rendering for Chinese, Japanese, Korean, and mixed-language content on any platform
- **Chart Image Mode** (`generate-ppt.js`): Charts now render as PNG images by default (via `chart.js` + `chartjs-node-canvas`) for cross-platform compatibility with Keynote, Google Slides, and WPS. Native OOXML charts available via `--native-charts` flag for PowerPoint-only environments
- New dependencies: `chartjs-node-canvas`, `chart.js`

### Fixed

- **Text Overflow**: `addTextBox` defaults changed to `breakLine: true` + `shrinkText: true` — long text now auto-wraps and auto-shrinks instead of overflowing fixed-size boxes
- **Bullet List Overflow**: `addBulletList` now includes `shrinkText: true` for auto-fit
- **Table Overflow**: Table `autoFit` changed from `false` to `true` — cell content adapts to available space
- **Closing Slide Bullet Color**: `addBulletList` now accepts `color` parameter — closing slide bullets render in light color (`E2E8F0`) instead of invisible dark text on dark background

## [0.7.0] - 2026-03-20

### Added

- **Chart Determinism** (`python_backend/smart_layer.py`): New `repair_chart_data()` auto-repair function — corrects invalid chart types, coerces string-formatted numbers (e.g. `"$1,200"` → `1200`), and trims excess data arrays to match category length. Irreparable data (non-numeric values, missing data points) triggers automatic degradation to bullet layout instead of synthesizing false zero values
- Stricter chart schema (`deck-schema.json`): `enum` validation for chart types (`bar`, `line`, `pie`, `area`), `minItems` constraints on `categories` and `series`, `oneOf` to distinguish empty placeholders from valid chart data
- `MAX_REPAIR_ATTEMPTS` increased from 1 to 2 for more reliable LLM output recovery
- **Docker Packaging**: `Dockerfile` (Python 3.12 + Node.js 20), `docker-compose.yml` for one-command launch, `.dockerignore`
- **Remote MCP Transport** (`mcp_server.py`): `--transport streamable-http`, `--host`, `--port` CLI arguments for hosted/remote MCP deployments
- Docker and remote MCP sections added to `README.md`, all three Integration Guides, and all three Examples docs
- Docker build verification step added to `RELEASE_CHECKLIST.md`

### Fixed

- **Documentation Drift**: README smoke test command corrected from `npm run smoke` to `npm run ci:smoke` with individual smoke step listing
- `RELEASE_CHECKLIST.md` validation command updated to `npm run ci:smoke`

## [0.6.1] - 2026-03-20

### Added

- **OpenRouter Provider** (`python_backend/llm_provider.py`): New `OpenRouterProvider` class — access 200+ models (OpenAI, Anthropic, Google, Meta, Mistral, etc.) through a single API key via OpenRouter's OpenAI-compatible gateway
- OpenRouter auto-detection: when `OPENROUTER_API_KEY` is set, it takes priority over direct provider keys
- `.env.example` updated with `OPENROUTER_API_KEY`
- 8 new tests for OpenRouterProvider (init, chat, error handling, factory priority) — **409 total**

### Changed

- Provider detection order: OpenRouter (if key set) → model-name-based detection (Claude → Anthropic, Gemini → Google, otherwise → OpenAI)
- `llm_provider.py` docstring updated with OpenRouter setup example

## [0.6.0] - 2026-03-19

### Added

- **API Versioning**: `apiVersion: "1.0"` field in all requests and responses for forward-compatible API evolution
- **CI Hardening**: pytest matrix (Python 3.10/3.11/3.12) + Node.js 18/20/22 smoke matrix in GitHub Actions
- **Test Coverage Expansion**: 255 automated tests achieving 84% line coverage (up from 143 tests / 72%)
  - `tests/test_coverage_boost.py`: 111 new cross-module tests covering llm_provider, skill_api, source_loader, smart_layer
- All 14 GitHub issues closed

### Changed

- `skill-manifest.json` bumped to version 0.6.0 with `apiVersion` field
- `py-skill-server.py` includes `apiVersion` in all HTTP responses (health, success, error)
- CI workflow renamed from `smoke` to `CI` with matrix strategy
- `.gitignore` updated to exclude `.coverage` files

## [0.5.1] - 2026-03-19

### Added

- **Image Asset Pipeline** (`python_backend/image_handler.py`): Classify, resolve, and load images for slide rendering with full security (path traversal protection, SSRF validation, 10 MB size limit, extension whitelist)
- **Visual Object Schema** (`deck-schema.json`): New `visualObject` definition supporting `type: "image"` (with `path`/`url`) and `type: "placeholder"` (with `prompt`), plus `alt` and `position` fields. The `visuals` array now accepts both plain strings and visual objects via `oneOf`
- **Python Renderer Image Support** (`python_backend/pptx_renderer.py`): `_insert_visuals_on_slide()` partitions visuals into descriptions/images/placeholders, inserts actual images via `python-pptx`, renders placeholders as labeled boxes, and falls back to text suggestion boxes when no images resolve
- **JS Renderer Image Support** (`generate-ppt.js`): `renderVisualsOnSlide()` with `classifyVisual()` helper — inserts local images via PptxGenJS `addImage()`, renders placeholder boxes, falls back to text suggestions
- **LLM Visual Instructions**: System prompt now includes `VISUAL RULES` section explaining the three visual item types and position presets
- 48 new tests: classify_visual (10), partition_visuals (4), get_position (4), resolve_image/security (9), detect_image_ext (4), schema validation (4), looks_like_image_path (13) — **143 total**

### Changed

- `visuals` schema items changed from `{"type": "string"}` to `oneOf [string, visualObject]` (backward compatible)
- `render_deck_with_template()` and `_render_slide()` accept `base_dir` parameter for image path resolution
- `skill_api.py` passes `base_dir` to the Python renderer
- All 12 Python layout renderers now accept `**kwargs` for forward compatibility

## [0.5.0] - 2026-03-19

### Added

- **Brand Template Engine** (`python_backend/template_engine.py`): Parse .pptx master templates — extracts slide layouts, placeholders, theme colors, fonts, and auto-maps schema layouts to template layout indices
- **Python-native PPTX Renderer** (`python_backend/pptx_renderer.py`): Full python-pptx renderer supporting all 13 layout types (title, agenda, section, bullet, two-column, comparison, timeline, process, table, chart, quote, summary, closing), charts (bar/line/pie/area), tables, speaker notes, source citations
- **Dual Render Path**: `template` parameter in request → python-pptx renderer; no template → JS (pptxgenjs) renderer. Both MCP tools (`create_deck`, `revise_deck`) accept `template` parameter
- `template` field added to deck-schema.json (optional, path to .pptx brand template)
- `renderer` field in API response indicates which renderer was used (`"python-pptx"` or `"pptxgenjs"`)
- `describe_template()` helper for diagnostics (lists layouts, placeholders, colors, fonts)
- `python-pptx>=1.0.0` added to requirements.txt
- 25 new tests: template parsing (10), PPTX rendering (8), dual render path (3), color helpers (4) — 95 total

## [0.4.1] - 2026-03-19

### Added

- Chart-specific instructions in LLM system prompt with few-shot example and data format rules
- Chart data requirements section in SKILL.md
- `validate_chart_slides()`: validates chart data in planning output, degrades invalid chart slides to bullet layout with assumption notes
- `extract_numerical_hints()`: scans source material for numerical patterns (percentages, currency, scaled numbers) and injects chart usage hints into LLM prompt
- `_is_valid_chart()`: validates chart object structure (non-empty categories, numeric series data)
- Mock deck now includes a chart slide with sample bar chart data for testing
- 12 new unit tests: chart validation (8), numerical extraction (4) — 64 total tests

### Changed

- System prompt now includes explicit chart data rules: required fields, supported types, few-shot example, no empty arrays
- `build_create_prompt()` appends numerical data hints when source material contains extractable numbers
- Chart fallback runs in both mock and LLM planning paths before schema validation

### Removed

- `deck-agent-core.js`: legacy planning file deleted (functionality fully replaced by `python_backend/smart_layer.py` since v0.3.0)
- `source-loader.js`: legacy source loading file deleted (functionality fully replaced by `python_backend/source_loader.py` since v0.3.0)
- References to deleted files removed from ZH-CN and JA integration guides

## [0.4.0] - 2026-03-19

### Added

- `mcp_server.py`: MCP Server exposing `create_deck` and `revise_deck` as native MCP tools for Claude Desktop, Cursor, Windsurf, and other MCP-compatible AI environments
- `tests/test_mcp_server.py`: 9 pytest tests covering MCP tool invocation, output validation, source handling, custom output directories, and revision workflows
- `mcp>=1.26.0` added to `requirements.txt`
- MCP Server section in README with configuration examples for Claude Desktop, Cursor, and Windsurf
- MCP quick-start step in README Quick Start section

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