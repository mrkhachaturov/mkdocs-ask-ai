---
name: changelog-entry
description: Draft a CHANGELOG.md entry for the next release from git commits since the last tag.
---

# Draft Changelog Entry

## Step 1 — Get commits since last tag

```bash
git log $(git describe --tags --abbrev=0)..HEAD --oneline
```

## Step 2 — Assess if a release is warranted

**Before writing anything**, classify the commits:

| Commit type | Release? |
|-------------|----------|
| `feat:` — new user-facing feature | Yes — minor bump |
| `fix:` — bug fix affecting users | Yes — patch bump |
| `docs:` — README, demo video, typos | **No** — not a release |
| `chore:` — tooling, CI, internal scripts | **No** — not a release |
| `refactor:` — internal code changes, no behaviour change | **No** — not a release |

If all commits since the last tag are `docs:` / `chore:` / `refactor:`, **stop and tell the user there is nothing worth releasing**. Do not bump the version.

## Step 3 — Write the entry

Add above the previous `## [x.y.z]` entry:

```markdown
## [Unreleased]

### Added
- ...

### Fixed
- ...

### Changed
- ...
```

Only include sections that have content. Keep entries short — one line per change. Do not list internal tooling, CI changes, or doc-only edits unless they directly affect users.

## Step 4 — Update CHANGELOG.md

Edit `CHANGELOG.md` in place. Do not commit yet — that happens in the release skill.
