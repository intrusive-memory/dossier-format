---
type: changelog
updated: 2026-11-01
---

# Changelog

## Format 2, release candidate 7 (2026-11-01)

Template 0.1.1. No valid bundle becomes invalid, so `manifestVersion` stays 2.

- **`template/fragments.html`, rule 4:** a `markSeparator` fragment goes between two
  footnote marks with nothing between them, so `1`, `2` doesn't read as `12`. This is in the
  markup, because a CSS sibling selector also matches two marks with text between them.
- **Rule 3:** a line break inside a paragraph or list item continues it, and `**` and `*`
  may span one.
- **Field rule 2:** a definition cited only from another definition's text counts as never
  cited.
- **Fixtures:** `valid/page-wrapped-text`. Every page is regenerated with template 0.1.1, and
  each fixture's expected result is unchanged.

## Format 2, release candidate 6 (2026-11-01)

No valid bundle becomes invalid, so `manifestVersion` stays 2. `template/` doesn't change.

- **`template/README.md` field rule 2, `data/fields.json`:** on the page, footnote
  definitions never cited go after the numbered sources, in file order, and a mark with no
  definition shows as plain text. `W-FOOTNOTE` still flags both.
- **Fixtures:** `warnings/W-FOOTNOTE-on-page`. No existing fixture changed.

## Format 2, release candidate 5 (2026-11-01)

Template 0.1.0. No valid bundle becomes invalid, so `manifestVersion` stays 2. The
rules in the last item state what a validator already had to do.

- **§6, §7:** when a required input's bytes have left the bundle, a writer records the
  hash actually sent, with the path of the current selection for that role, so a
  selected asset reads `W-STALE`. A reader MUST NOT assume the file at `path` has that
  `sha256`.
- **§1, §4, DF-18:** a writer MAY strip metadata as it copies an image in. Pixel data is
  untouched, an original isn't modified once it's in the bundle, embedded records are
  read first, and the hash and file name come from the stripped bytes. The PNG chunks
  that count are listed. A tool sending a reference should send the bundle's copy.
- **§11, `template/README.md`:** the template's rules 1 to 11 are adopted, and the readings
  of `data/fields.json` are stated as field rules. §11 points to both. `template/`'s hash
  doesn't change.
- **§14:** `C-NO-DESCRIPTION` and `C-KEY-MISSING`, for a check only, outside validation
  results. No verdict changes.
- **§5.6:** an adopted asset's `provenance` has `provider: import`.
- **§5.2, §9.1, §3, Appendix A:** a manifest path compares with a name on disk as NFC
  strings, case-sensitively. A `files` entry for a symlink or `manifest.json` is
  `E-FILE-MISSING`. A listed hidden file is checked as normal. A `CHARACTER.md` with no
  `character` key isn't `E-NAME-MISMATCH`. `E-MULTI-SELECTED` applies only to version 2.
- **Fixtures (104):** new `valid/name-on-disk-nfd`, `valid/description-no-character-key`,
  `errors/E-FILE-MISSING-symlink`, `errors/E-FILE-MISSING-manifest`,
  `warnings/W-V1-two-selected` and `warnings/W-STALE-input-left-bundle`. No fixture's
  expected result changed. Every page is now the shipped template, filled by
  `tools/build_examples.py`, and `conformance.json`'s `templateVersion` and
  `templateSha256` are `template/VERSION.json`'s.

## Template 0.1.0 (2026-11-01)

The first page template. A template version, not a format version: no bundle's validity
changes, and `manifestVersion` stays 2.

- **`template/`:** skeleton, fragments, stylesheet generated from `data/tokens.json`, the
  custom elements `<dossier-tabs>`, `<dossier-field>`, `<dossier-image-set>` and
  `<dossier-audio>`, DF-43's sizes in `page-copies.json`, and fonts under the OFL.
- **`template/VERSION.json`:** the version and its `sha256`. What the hash covers is
  proposed in `template/README.md`, since §11 doesn't say.
- **`template/example/`:** a page filled by hand for acceptance 3 and 4.
- **`tools/`:** `build_template_css.py`, `template_version.py` and `check_template.py`.
- **Fixtures:** unchanged. Their pages still carry `0.0.0-fixture`, and
  `examples/README.md` says they are regenerated when the template ships. That hasn't
  been done.

## Format 2, release candidate 4 (2026-11-01)

Read-only applications had no way to tell that a bundle was being updated. No bundle
that was valid becomes invalid, so `manifestVersion` stays 2.

- **§5.7, new:** update markers (DF-64 to DF-66). A writer holds a hidden
  `.update-<id>.json` in the bundle's root for the length of an update. A marker
  counts only when `now < expiresAt <= now + 3600 seconds`.
- **§12:** what a host does during an update (DF-67).
- **Schema:** `schemas/update-marker.schema.json`.
- **Fixtures:** `valid/update-active` and `valid/update-not-active`. Fixtures that
  test this carry the new `updateStatus` key in `conformance.json`. No existing
  fixture changed.

## Format 2, release candidate 3 (2026-10-31)

An independent read of rc.2 found rules with two readings on real input, and two
faults rc.2 introduced. A validator then written blind from this text found more:
the layout of `CAST.md` was nowhere stated. Each change has fixtures (96 in all). No
fixture changed its expected result except as noted.

- **§5.4, §8.2, §5.1, §6, schema:** the text and schema agree. `language` on a sample
  and `version` in `tool` and `generator` are optional. `training` is required on
  `kind: training`, in the schema as well as the text.
- **§7:** how a member's YAML is read, so the hash doesn't depend on the YAML library
  or change when a writer normalizes the file. The exact escapes. Fixed: a null
  `voicePrompt` no longer hides `voiceDescription`.
- **§7:** `W-STALE` applies to selected assets. An input with no current selection is
  stale. An image with no `provenance.artStyle` isn't compared.
- **§8.3, §14:** a tier comes from `CAST.md`. `W-ROLE` applies to a member with a dossier.
- **§14:** new codes `E-CAST` and `E-MANIFEST`.
- **§3:** the layout of `CAST.md`. `gender` values for `E-CAST`.
- **§3:** `W-POINTER` means a pointer that doesn't reach a manifest, including one to
  nothing. Other faults keep their own codes. Orphans are looked for in named
  directories, not recursively. Names compare exactly and `E-NAME-MISMATCH` covers
  `CHARACTER.md`. A bundle whose name isn't canonical is `E-NAME`.
- **§5.2:** `W-UNCLASSIFIED` and `E-ZERO-BYTE` apply to files on disk, whether or not
  `files` lists them.
- **§5.6:** what `refresh` may adopt. A sample is adopted only when its text and voice
  are known.
- **§8.1:** fixed: a missing file is only `E-FILE-MISSING`, not also `W-SHAPE`.
- **Fixtures:** `E-VERSION` may also report `E-SCHEMA`, as §14 allows. `W-POINTER` must
  report `W-ORPHAN` too. `W-PAGE-SIZE` is tested at 10,000,001 bytes, with a valid page at
  exactly 10,000,000. `conformance.json` covers each `W-STALE` input and each check row
  on its own.
- **§8.2:** `voices.voxalta` names the vox when any entry resolves to it. **Appendix A:**
  version 1 isn't held to version 2's rules.

## Format 2, release candidate 2 (2026-10-31)

Reviewing a first implementation's requirements against rc.1 found rules a
validator couldn't implement from the text alone. Fixtures added for each.

- **§2:** `^` is removed repeatedly, in any order with parentheticals, so
  `DUKE (V.O.) ^` and `DUKE^ (V.O.)` are `DUKE`.
- **§3:** how a `manifest:` pointer is resolved and compared (`W-POINTER`).
- **§5.2, schema:** which paths are `E-PATH`. Added: drive letters, URL schemes
  and backslashes. It covers every path in the manifest, not only `files`.
- **§7:** a `castMember` hash is taken over the member's normal form, so it doesn't
  depend on how `CAST.md` is written or change when a writer normalizes it.
  Hashes of members already in normal form don't change.
- **§8.1:** `W-SHAPE` as arithmetic, on selected assets, with the boundary stated.
- **§11:** the current template, for `W-STALE`. A page on any other template is
  stale, older or newer. What counts as a reference for `W-PAGE-EXTERNAL`. A
  cited `<a href="https://…">` is allowed.
- **Appendix A:** migration as ordered steps, with the rename to `.dossier` and
  the page after the manifest. A retired asset that can't be mapped stays as an
  unclassified file.
- **`conformance.json`:** adds `templateSha256`.

## Format 2, release candidate 1 (2026-10-31)

Conformance fixtures added (`examples/`). Writing them found these gaps in the
specification. None makes a valid bundle invalid.

- **§5.4, §14:** `E-MULTI-SELECTED` counts `voiceSample`s per `kind` + `variant`
  + `model`. As written, the neutral read on each model size that §8.2 requires
  was an error.
- **§6:** `provenance.box` is the face box, not the crop. §6 and §8.5 disagreed.
- **§7:** canonical JSON for the `castMember` hash is defined in full.
- **§8.2:** `voices.voxalta` paths are relative to the directory holding `CAST.md`.
- **§8.3:** how to tell that a `.vox` holds a model size.
- **§8.5:** the face crop is stated as arithmetic, with a worked example.
- **§11:** the embedded manifest excludes the page. A file can't contain its own
  hash, and an embedded `updatedAt` made two renders differ. `<` is escaped in
  the embedded record.
- **§11, §14:** `W-PAGE-SIZE` is 10,000,000 bytes.
- **§14:** `E-NOT-BUNDLE` applies to version 2 manifests, since Appendix A allows
  version 1 in a plain directory. A specific code may come with `E-SCHEMA`.
- **Schema:** `manifest-v2` no longer limits `view` variants. §14 makes a
  non-standard one `W-VARIANT`, and the text wins.

Not written: the page template, `data/fields.json`, `data/tokens.json`.

## Format 2 (2026-10-19)

First version 2 specification, schemas and tier table.
