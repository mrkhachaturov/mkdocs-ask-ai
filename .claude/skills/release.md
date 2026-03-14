---
name: release
description: Use when publishing a new version of mkdocs-ask-ai to PyPI — bumps version, commits, tags, and pushes to trigger the automated GitHub Actions release workflow.
disable-model-invocation: true
---

# Release mkdocs-ask-ai

Automate the release of a new version to PyPI via GitHub Actions trusted publishing.

## When to Use

- User says "release", "publish", "bump version", "deploy to PyPI"
- A set of changes is ready to ship as a new version

## Prerequisites

- All tests pass (`make check`)
- GitHub environment `pypi` exists with trusted publisher configured on PyPI
- Working directory: the plugin repo root

## Release Steps

- [ ] **Gate check** — run `git log $(git describe --tags --abbrev=0)..HEAD --oneline` and review. If all commits are `docs:` / `chore:` / `refactor:`, **stop — there is nothing worth releasing**. Only proceed for `feat:` or `fix:` commits.
- [ ] **Determine version bump** — ask user if not specified: patch (x.y.z→x.y.Z), minor (x.y.z→x.Y.0), or major (x.y.z→X.0.0)
- [ ] **Update CHANGELOG.md** — rename `## [Unreleased]` to `## [X.Y.Z] - YYYY-MM-DD`, add a fresh empty `## [Unreleased]` above it, update the comparison links at the bottom. The release workflow extracts the **first versioned section** (2nd H2), so `[Unreleased]` must be above and empty.
- [ ] **Run checks** — `ruff check src/ tests/ && ruff format --check src/ tests/ && pytest tests/ -v`
- [ ] **Bump version** in both files:
  - `pyproject.toml` → `version = "X.Y.Z"`
  - `src/mkdocs_ask_ai/__init__.py` → `__version__ = "X.Y.Z"`
- [ ] **Commit** — `git add pyproject.toml src/mkdocs_ask_ai/__init__.py CHANGELOG.md && git commit -m "release: vX.Y.Z"`
- [ ] **Tag** — `git tag vX.Y.Z`
- [ ] **Push** — `git push origin main --tags`
- [ ] **Watch release workflow** — `gh run list --workflow release.yml --limit 1 && gh run watch <id>`
- [ ] **Verify** — confirm PyPI shows new version and GitHub Release was created

## What Happens Automatically

Pushing the `v*` tag triggers `.github/workflows/release.yml`:
1. Builds sdist + wheel via `python -m build`
2. Publishes to PyPI via trusted publishing (no token needed)
3. Creates GitHub Release with built artifacts

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Forgot to bump both files | Always edit `pyproject.toml` AND `__init__.py` |
| PyPI rejects duplicate version | PyPI is immutable — bump to next patch |
| Release workflow fails | Check that `pypi` environment exists on GitHub and trusted publisher is configured on PyPI |
