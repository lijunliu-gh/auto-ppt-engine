# Publish Checklist

Use this checklist before making the repository public.

## Repository Metadata

- [ ] repository name is correct
- [ ] repository description is set
- [ ] repository topics are added
- [ ] social preview image is uploaded if desired
- [ ] default branch name is confirmed

## Legal And Governance

- [ ] `LICENSE` is present
- [ ] `CONTRIBUTING.md` is present
- [ ] `SECURITY.md` is present
- [ ] `.github/CODEOWNERS` has a real GitHub username or team instead of the placeholder

## Content Review

- [ ] `README.md` reflects the current product scope
- [ ] multilingual docs are present and linked
- [ ] no internal-only comments or secrets remain in docs
- [ ] generated files under `output/` are not committed

## Git Commit Scope

Files and folders that should normally be committed:

- source files such as `*.js` and `*.json`
- repository docs such as `README.md`, `PRODUCT.*.md`, `USER_GUIDE.*.md`, and `INTEGRATION_GUIDE.*.md`
- GitHub workflow and template files under `.github/`
- `LICENSE`, `CONTRIBUTING.md`, `SECURITY.md`, `GITHUB_SETUP.md`, `PUBLISH_CHECKLIST.md`, and release draft files
- `package.json` and `package-lock.json`
- sample input files such as `sample-input.json`, `sample-agent-request.json`, and `sample-source-brief.md`

Files and folders that should normally not be committed:

- `node_modules/`
- `output/`
- `.env`
- machine-local caches or editor junk

If you are unsure, use `.gitignore` as the default rule and avoid committing generated artifacts.

## Environment Review

- [ ] `.env` is not committed
- [ ] `.env.example` only contains placeholder values
- [ ] `.gitignore` excludes local-only artifacts

## Validation

- [ ] `npm install` works on a clean machine
- [ ] `node scripts/run-smoke.js` passes
- [ ] GitHub Actions smoke workflow is enabled

## Final Git Review

- [ ] `git status` only shows intended tracked files
- [ ] no generated `.pptx` or generated deck JSON files are staged
- [ ] no local secrets are staged
- [ ] `.github/CODEOWNERS` placeholder has been replaced or intentionally removed

## Release Preparation

- [ ] next release tag is chosen
- [ ] release notes are prepared
- [ ] the matching `RELEASE_DRAFT_vX.Y.Z.md` file is reviewed and adjusted

## Suggested Final Step

After publishing, create the first GitHub release from the chosen tag and paste the edited release notes into the release body.