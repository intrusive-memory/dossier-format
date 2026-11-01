---
type: doc
updated: 2026-10-31
---

# Conformance fixtures

Every character here is invented. Images are flat shapes, `.vox` embeddings are
placeholders that can't produce a voice, and samples are 0.2 seconds of silence.

Each fixture is a small project: a `CAST.md` and a `characters/` directory.
Validate it from its `CAST.md`.

| Path | Contents |
|------|----------|
| `valid/` | Bundles a validator reports nothing about. |
| `errors/` | One or more per `E-` code. A reader rejects these. |
| `warnings/` | One or more per `W-` code. A reader opens these. |
| `conformance.json` | What each fixture must produce. |
| `names.json` | The canonicalization table in §2, as data, plus NFD and error cases. |

## `conformance.json`

| Key | Meaning |
|-----|---------|
| `path` | The project. |
| `bundle` | The bundle under test, relative to the project. |
| `verdict` | `valid`, `warnings` or `invalid`. |
| `codes` | Codes a validator MUST report. |
| `mayAlso` | Codes a validator MAY also report. Any other code is a failure. |
| `complete`, `missingRequired` | The completeness result against the tier (§8.3). Absent where it isn't asserted. |
| `note` | What the fixture is testing, where the name doesn't say. |

## Limits

- **The pages are hand-made,** because the template doesn't exist yet. They meet
  §11's structure and carry the template version `0.0.0-fixture`, whose hash is
  the SHA-256 of `dossier-format fixture template\n`. Treat that as the current
  template: it's `templateVersion` and `templateSha256` in `conformance.json`. These pages are test input for readers and validators, not a model
  for a renderer's output. They will be regenerated when the template ships.
- **Face detection has no fixture.** Images are shapes, not faces, so the face
  crops use `provenance.box`. §8.5's worked example is the portrait and box
  these fixtures use.
- **Some checks can't be expressed here.** `E-NAME` for a case-only collision is
  a writer's refusal (§2), and a fixture can't be created on a case-insensitive
  disk.
- `warnings/W-PAGE-SIZE` is 11 MB on disk, nearly all of it a comment. It
  compresses to almost nothing in git.

## Regenerating

`tools/build_examples.py` writes this directory, except this file. Run it after
any change to the standard (AGENTS.md rule 9). Output is byte-stable for the
pinned versions in `tools/requirements.txt`.
