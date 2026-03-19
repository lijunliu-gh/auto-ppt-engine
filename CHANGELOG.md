# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project follows Semantic Versioning while it remains a prototype.

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