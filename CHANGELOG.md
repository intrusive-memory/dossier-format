---
type: changelog
updated: 2026-10-31
---

# Changelog

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
