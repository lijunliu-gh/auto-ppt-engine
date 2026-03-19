# Release Draft: v0.3.0

## Title

`v0.3.0 - Python-first smart layer and compatibility release`

## Suggested Release Notes

This release moves Auto PPT Prototype to a Python-first public architecture while keeping the existing JavaScript renderer as the stable PPTX output engine.

### Highlights

- new Python smart layer for planning, revision, source loading, and agent orchestration
- JavaScript renderer retained for final `.pptx` generation
- Node create, revise, skill, and server entrypoints kept as compatibility wrappers
- Python-first CLI, JSON skill, and HTTP service flows
- updated English, Simplified Chinese, and Japanese docs to match the new architecture
- sample requests and skill responses aligned around `python-smart-layer`

### Compatibility Notes

- existing Node entrypoints still work for older integrations
- new integrations should treat Python as the primary public entrypoint surface
- deck JSON remains the stable contract between planning and rendering

### Validation Notes

- Python create, revise, and skill flows were validated locally
- compatibility wrappers were validated after Windows argument forwarding fixes
- local health checks confirmed the Python skill server on port `3010`

### Notes

- this is still an experimental prototype
- the repository is an agent backend, not a full research agent
- OCR, stronger provenance mapping, and production-grade template control are still future work