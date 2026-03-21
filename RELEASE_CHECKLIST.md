# Release Checklist

Use this checklist before tagging a new version release.

## Version Bump

- [ ] `package.json` version is updated
- [ ] `skill-manifest.json` version is updated
- [ ] `CHANGELOG.md` has a new entry for this version
- [ ] `ROADMAP.md` version and timeline are updated

## Content Review

- [ ] `README.md` reflects the current product scope
- [ ] `PRODUCT.*.md` lists all current capabilities (en, ja, zh-CN)
- [ ] `USER_GUIDE.*.md` covers all entry points and new features (en, ja, zh-CN)
- [ ] `INTEGRATION_GUIDE.*.md` covers all integration paths (en, ja, zh-CN)
- [ ] `EXAMPLES.*.md` includes examples for new features (en, ja, zh-CN)
- [ ] no references to deleted files or removed features
- [ ] no internal-only comments or secrets remain in docs
- [ ] generated files under `output/` are not committed

## Git Commit Scope

Files and folders that should normally be committed:

- source files such as `*.py`, `*.js`, and `*.json`
- repository docs such as `README.md`, `PRODUCT.*.md`, `USER_GUIDE.*.md`, and `INTEGRATION_GUIDE.*.md`
- GitHub workflow and template files under `.github/`
- `LICENSE`, `CONTRIBUTING.md`, `SECURITY.md`
- `Dockerfile`, `docker-compose.yml`, `.dockerignore`
- `package.json` and `package-lock.json`
- sample input files under `examples/inputs/` such as `sample-input.json`, `sample-agent-request.json`, and `sample-source-brief.md`

Files and folders that should normally not be committed:

- `node_modules/`
- `output/`
- `.env`
- `__pycache__/`
- machine-local caches or editor junk

## Environment Review

- [ ] `.env` is not committed
- [ ] `.env.example` only contains placeholder values
- [ ] `.gitignore` excludes local-only artifacts

## Validation

- [ ] `npm install` works on a clean checkout
- [ ] `pip install -r requirements.txt` works on a clean checkout
- [ ] `npm run ci:smoke` passes (smoke tests)
- [ ] `python -m pytest tests/ -v` passes (all tests green)
- [ ] `docker build -t auto-ppt-engine .` succeeds
- [ ] MCP server starts without error: `python mcp_server.py`
- [ ] GitHub Actions CI workflow passes

## Final Git Review

- [ ] `git status` only shows intended tracked files
- [ ] no generated `.pptx` or generated deck JSON files are staged
- [ ] no local secrets are staged

## Release

- [ ] tag the release: `git tag v<version>`
- [ ] push the tag: `git push origin v<version>`
- [ ] create GitHub Release from the tag with release notes from `CHANGELOG.md`