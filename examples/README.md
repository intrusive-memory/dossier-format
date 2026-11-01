---
type: doc
updated: 2026-11-01
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
| `updateStatus` | The update status of `bundle` (§5.7): `at` is the time to use as `now`, and `updating` is the answer. Absent where it isn't asserted. |
| `note` | What the fixture is testing, where the name doesn't say. |

## Limits

- **The pages are the shipped template, filled.** `templateVersion` and
  `templateSha256` in `conformance.json` are `template/VERSION.json`'s: treat that as
  the current template. The tool fills only what these pages need, so its banner is
  always empty and it refuses a footnote that isn't both cited and defined. A page that
  tests a fault has it added afterwards: `W-PAGE-EXTERNAL` markup goes before the
  record, `W-PAGE-SIZE` and `valid/page-at-size-limit` get a comment after `</html>`,
  and `W-STALE-template` claims another hash. These pages are test input, not a
  reference for a renderer, though `valid/complete-lead`'s is the same bytes as
  `template/example/`.
- **Stripping metadata (§4) has no fixture.** It happens as a file is copied in, and a
  fixture holds only the result, which is an ordinary PNG with its own hash. Nor can a
  fixture show that an original wasn't changed later. §4 has a worked example. Adoption
  by *refresh* (§5.6) has no fixture for the same reason.
- **Check findings (§14) aren't asserted.** `C-` codes are outside validation results,
  so they aren't in `codes` or `mayAlso`. `valid/empty-background` and
  `valid/description-no-character-key` say in their notes which one a check reports.
- **`valid/name-on-disk-nfd` depends on the checkout.** Its file's name on disk is NFD.
  Linux and APFS keep that, and HFS+ doesn't. Git on a Mac stores such a name as NFC unless
  it's added with `git -c core.precomposeunicode=false add`, and reports it as untracked
  in NFC form, which is why the repository's `.gitignore` names that form.
- **Face detection has no fixture.** Images are shapes, not faces, so the face
  crops use `provenance.box`. §8.5's worked example is the portrait and box
  these fixtures use.
- **Some checks can't be expressed here.** `E-NAME` for a case-only collision is
  a writer's refusal (§2), and a fixture can't be created on a case-insensitive
  disk.
- `warnings/W-PAGE-SIZE` and `valid/page-at-size-limit` are 10 MB on disk, nearly
  all of it a comment. They compress to almost nothing in git. Each other page carries
  the template's fonts, stylesheet and script, about 220 KB, which git packs as deltas.

## Regenerating

`tools/build_examples.py` writes this directory, except this file. Run it after
any change to the standard or the template (AGENTS.md rule 9). Output is byte-stable
for the pinned versions in `tools/requirements.txt`.
