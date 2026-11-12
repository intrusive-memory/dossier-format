---
type: doc
updated: 2026-11-12
---

# Conformance fixtures

Every character here is invented. Images are flat shapes, `.vox` embeddings are
placeholders that can't produce a voice, and samples are 0.2 seconds of silence.

Each fixture is a small project: a `CAST.md` and a `characters/` directory, and for a
location (§16) a `PROJECT.md` whose `locations` key names the index, usually `LOCATIONS.md`
with a `locations/` directory beside it. Validate it from its `CAST.md` and from its
`PROJECT.md` when it has one (§16.2). A fixture's `PROJECT.md` has the four keys SwiftProyecto
requires and the two the format reads; the rest of that file is SwiftProyecto's.

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
| `preview` | The preview of `bundle` (§11.1): `key` is its key, against the template in `templateSha256`, and `hit` says whether `.preview/<key>.html` is already stored. Absent where it isn't asserted. |
| `locationsPage` | The project's LOCATIONS page (§16.6): `key` is its key, against the template in `locationsTemplateSha256`, and `hit` says whether `.locations-page/<key>.html` is already stored beside the index. Absent where it isn't asserted. |
| `note` | What the fixture is testing, where the name doesn't say. |

## Limits

- **The pages are the shipped template, filled.** `templateVersion` and
  `templateSha256` in `conformance.json` are `template/VERSION.json`'s: treat that as
  the current template. `locationsTemplateVersion` and `locationsTemplateSha256` are
  `template-locations/VERSION.json`'s, the current LOCATIONS page template. The tool fills only what these pages need, so its banner is
  always empty and it refuses a footnote that isn't both cited and defined. A page that
  tests a fault has it added afterwards: `W-PAGE-EXTERNAL` markup goes before the
  record, `W-PAGE-SIZE` and `valid/page-at-size-limit` get a comment after `</html>`,
  and `W-STALE-template` claims another hash. These pages are test input, not a
  reference for a renderer, though `valid/complete-lead`'s is the same bytes as
  `template/example/`.
- **Stripping metadata (§4) has no fixture.** It happens as a file is copied in, and a
  fixture holds only the result, which is an ordinary PNG with its own hash. Nor can a
  fixture show that a writer left an original alone later. §4 has a worked example. Adoption
  by *refresh* (§5.6) has no fixture for the same reason, and neither does a writer's
  rescan keeping a recorded hash, or *refresh* accepting a changed file or dropping a missing
  one: a fixture holds a bundle before or after, and a validator judges only that.
- **Previews (§11.1) are asserted by key only.** A fixture can show a store and the key that
  should find it, but not a viewer's build, clean-up or rebuild, which happen over time.
  The stored preview in `valid/preview-current` is that bundle's page, and the store's other
  files are what clean-up would remove. Each store's `.gitignore` holds `*`, as §11.1 says, so
  git here ignores the store too: a new file in one needs `git add -f`.
- **Check findings (§14) aren't asserted.** `C-` codes are outside validation results,
  so they aren't in `codes` or `mayAlso`. `valid/empty-background` and
  `valid/description-no-character-key` say in their notes which one a check reports.
- **`valid/name-on-disk-nfd` depends on the checkout.** Its file's name on disk is NFD.
  Linux and APFS keep that, and HFS+ doesn't. Git on a Mac stores such a name as NFC unless
  it's added with `git -c core.precomposeunicode=false add`, and reports it as untracked
  in NFC form, which is why the repository's `.gitignore` names that form.
- **Inputs read from the member, with no member, have no fixture.** Every fixture is
  validated from its `CAST.md`, and `conformance.json` has no way to say "open the bundle
  without one", so there is always a member to check a `castMember` or `voice` input
  against. §7 states the rule (neither is checked) and its worked example covers a bundle
  opened without a `CAST.md`.
- **The Samples tab shows no input for a hosted-voice sample yet.** Its provenance line
  reads only a `vox` record (`data/fields.json`), so on the pages of
  `valid/hosted-voice-supporting` and `warnings/W-INCOMPLETE-hosted-no-neutral` the samples
  say nothing about the voice they were made with. The template change is deferred. The `copiedFrom` path in `valid/imported-view` names a file
  that isn't in the fixture, since nothing reads it.
- **Files outside the bundle aren't in the fixtures.** The `copiedFrom` and `source` paths
  of the imported images in `valid/view-families` and `valid/location`, and the `dry`
  paths of `valid/hosted-voice-provenance`'s `postProcess`, name files that aren't there,
  since nothing reads them.
- **Locations have no page of their own and no completeness** (§16.4, §16.6). The project's
  LOCATIONS page is asserted by key only, like a preview: `valid/locations-page-current`
  stores it, with an older page and a temporary file that clean-up would remove, and
  `valid/locations-page-out-of-date` stores only an older one. The stored page is
  `template-locations/example/LOCATIONS.html`, byte for byte. Each store's `.gitignore` holds
  `*`, so a new file in one needs `git add -f`. What a host shows (§16.7) isn't asserted.
- **Project-level findings name a bundle anyway.** `conformance.json` has one bundle per
  fixture, so a fixture whose finding is about `PROJECT.md` or the locations index
  (`E-CAST-project-*`, `E-CAST-locations-*`, `W-POINTER-locations-*`) names the location
  bundle that the broken discovery leaves unread, and `valid/locations-no-key` and
  `valid/locations-no-project` name a character bundle, since the project has no locations.
- **The provider pattern is generated.** `tools/build_provider_pattern.py` writes the
  `voice` record's `provider` pattern in `schemas/manifest-v2.schema.json` from Unicode 17.0
  and checks it with `--check`. `valid/hosted-voice-non-ascii-provider` and
  `errors/E-SCHEMA-voice-input-provider-non-ascii-case` test a non-ASCII capital.
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
