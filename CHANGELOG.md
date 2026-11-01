---
type: changelog
updated: 2026-10-31
---

# Changelog

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
