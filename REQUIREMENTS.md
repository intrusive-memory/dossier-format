---
type: requirements
state: draft
updated: 2026-10-03
sequence: 1 — first on the critical path of the Personaje effort
---

# dossier-format — Requirements

`dossier-format` is the language-agnostic standard for a character dossier. It
says what is in a `.dossier` bundle, what the manifest records, and what a
conforming dossier page contains. It has no implementation of its own.
**SwiftDossier** is the first implementation: the Swift reader, writer,
validator and page generator.

This document is the requirements for the standard. The deliverables it asks
for (§12) are a specification, schemas, data files, the page template and
conformance fixtures.

## 1. Where this text comes from

The format was drafted in two places, for a single Swift package. This document
brings the format parts of both into one place and leaves the Swift parts
behind.

| Source | What comes here | What goes to SwiftDossier |
|--------|-----------------|---------------------------|
| SwiftSemblanzas REQUIREMENTS §5 (v1 of the record) | §5.1 names, §5.2 discovery, §5.3 manifest, §5.4 kinds and tiers, §5.5 CHARACTER.md, §5.7 what verification reports | §5.6 the renderer, §5.8 library shape |
| Personaje `docs/REQUIREMENTS-DOSSIER-BUNDLE.md` (v2: the `.dossier` bundle) | §2 layout, §2.2 the page's contents, §3 manifest changes, §5 the face-crop rule, §7 validation, §8 what a migrated bundle looks like | §4 targets, API and CLI; Vision detection; the migration tool |
| Personaje `docs/REQUIREMENTS-APP-UI.md` | §5.1 the seven tabs, §5.4 the shared field list, §6 the page rules | The SwiftUI edit widget (Personaje's) |

Where the two sources disagree, the later one (the `.dossier` bundle, 2026-10-02)
wins. The differences are listed in §11.

## 2. Scope

**In the standard:** names; discovery; the bundle layout; file naming; the
manifest; asset kinds, shapes and statuses; role tiers and what each requires;
CHARACTER.md; the face-crop rule; voice files; the dossier page's contents and
its template; validation results; versioning.

**Not in the standard:**

- Any programming language, API or CLI.
- How images or voices are generated, and by which model.
- `CAST.md` itself. Its format belongs to SwiftReparto. The standard says only
  which `CAST.md` fields it reads.
- The `.vox` file. Its format is vox-format's.
- Byte-identical output across implementations (§9, DF-45).

**Conformance classes.** A **reader** opens and reads a bundle. A **writer**
creates or changes one. A **validator** reports on one without changing it. A
**renderer** produces the dossier page. An implementation may be any subset.
The key words MUST, SHOULD and MAY are used as in RFC 2119.

## 3. Names

| ID | Requirement |
|----|-------------|
| DF-1 | A character has **one name**: its screenplay cue, in uppercase. It is written identically as the `CAST.md` `character:` value, the bundle name, the manifest's `character`, the `CHARACTER.md` `character:` value, in file names that carry the name, and in command arguments. There are no slugs and no derived forms. |
| DF-2 | **Canonicalization**, applied to every name read from a screenplay, typed in, or found in `CAST.md`: (1) strip cue extensions (`(V.O.)`, `(O.S.)`, `(O.C.)`, `(CONT'D)` and any other trailing parenthetical) and the Fountain `@` force-marker; (2) trim, and collapse runs of whitespace to one space; (3) uppercase; (4) keep punctuation, digits and accents, stored in Unicode NFC. |
| DF-3 | A name containing `/` or `:`, or starting with `.`, is an **error**. There is never silent substitution. |
| DF-4 | A writer MUST refuse to create a bundle whose name differs from an existing one only by case. |
| DF-5 | Names contain spaces. Every path in the manifest and the page is stored unencoded; consumers quote or percent-encode at the point of use. |
| DF-6 | The specification includes a table of canonicalization examples that every implementation tests against. |

## 4. Discovery

| ID | Requirement |
|----|-------------|
| DF-7 | **Discovery starts at `CAST.md`.** A member that has a dossier carries a `manifest:` path, relative to the directory holding `CAST.md`. Nothing is found by scanning directories. |
| DF-8 | **Bundle name rule.** The bundle is a directory named `<character>.dossier`. The manifest's `character` MUST equal the directory name without the extension, and MUST equal the `CAST.md` member's `character`. A character directory with no `.dossier` extension is an error. |
| DF-9 | A member without `manifest:` has no dossier. That is valid. |
| DF-10 | A `.dossier` directory that no `CAST.md` member points at is an **orphan**. It is reported, never loaded and never deleted. |
| DF-11 | **Adoption.** The one exception to DF-7: when an orphan bundle's name exactly equals a member that has no `manifest:`, a writer's `refresh` MAY create the manifest and set the pointer. It never adopts a bundle whose name doesn't match exactly. |
| DF-12 | The `CAST.md` fields the standard reads are `character`, `role`, `manifest`, `voicePrompt` and `voices`. |

## 5. The bundle

```
characters/<CHARACTER>.dossier/
  manifest.json
  CHARACTER.md
  <CHARACTER>-dossier.html
  images/
    portrait-<sha8>.png
    face-<sha8>.png
    view-front-<sha8>.png   view-profile-<sha8>.png   view-back-<sha8>.png
    expression-<emotion>-<sha8>.png
  voice/
    <CHARACTER>.vox
    sample-<variant>.m4a
    samples.yaml
  source/  references/  training/  lora/
```

| ID | Requirement |
|----|-------------|
| DF-13 | **The bundle is the character's folder,** the one source of truth, read and written in place. It is not an export. |
| DF-14 | **The writer names image files:** `images/<kind>[-<variant>]-<sha8>.<ext>`, where `<sha8>` is the first 8 hex digits of the file's SHA-256. A file's name can't claim to be something it isn't, and names never collide. |
| DF-15 | Voice files keep the names their producer gives them: `voice/<CHARACTER>.vox`, `voice/sample-<variant>.m4a`. |
| DF-16 | **No sidecar files.** A generator's sidecar metadata is folded into the asset's `provenance`. A `.json` sidecar inside a bundle is a validation warning. |
| DF-17 | **Candidates live outside the bundle,** in `<charactersDir>/.generations/<CHARACTER>/`. A render enters the bundle when it is selected or explicitly kept. The standard defines this location and nothing about its contents. |
| DF-18 | Originals in `images/` are never modified, and never embedded in the page (§9). |
| DF-19 | The standard reserves a uniform type identifier and extension for the bundle (`dossier`, conforming to a package type) so an application can register it. A bundle shown as a plain folder is still valid. |
| DF-20 | **One home for a character's trained adapter:** the bundle's `lora/`. A tool that keeps adapters elsewhere treats the bundle's as the authority for a character that has a dossier. |

## 6. The manifest

`manifest.json` inventories the bundle. It has two layers.

| ID | Requirement |
|----|-------------|
| DF-21 | **`files`**: every regular file in the bundle except `manifest.json`, hidden files and symlinks. Each entry is exactly `path`, `sha256`, `sizeBytes`. Paths are relative to the bundle; a leading `/` is stripped; empty, `.` and `..` segments are rejected. Entries are sorted by `path`. Zero-byte files are refused. |
| DF-22 | **`manifestChecksum`** is the SHA-256 of the entries' `sha256` strings, sorted and concatenated. The specification states the algorithm in full with a worked example; it does not defer to another project's code. |
| DF-23 | **`assets`**: the semantic layer, keyed by `path`. Each entry has `kind`, `status`, and where they apply `variant`, `label`, `createdAt`, `provenance`, `review`, `derivedFrom`, and kind-specific data (`lora`, `sampleText`). Every asset has a `files` entry. A file with no asset entry is **unclassified**: allowed, and reported. |
| DF-24 | Top-level fields: `manifestVersion` (required), `character` (required), `role` (a copy of the `CAST.md` tier; `CAST.md` wins), `updatedAt` (required, ISO 8601), `generator` (name and version of the writing tool), `files` (required), `assets` (required, may be empty), `manifestChecksum` (required). |
| DF-25 | **`manifestVersion` is 2.** A reader MUST reject an unknown version. A reader MAY read version 1; a writer MUST NOT write it. |
| DF-26 | **`status`** is `selected`, `candidate` or `rejected`. At most one `selected` per `kind` + `variant`. Selecting one demotes the previous selection to `candidate`. Nothing is ever deleted implicitly. |
| DF-27 | **`derivedFrom`** on `face`, `view`, `expression` and `dossier` records the SHA-256 of every input. When an input's selected file changes, the derived asset is **stale**: flagged, never deleted. |
| DF-28 | **`provenance`** records `provider`, `model`, `prompt` (the prompt actually sent), `seed`, and `references`: `{path, sha256}` for every reference image sent. An imported file has `provider: "import"`. A hand-set face-crop box is recorded here. |
| DF-29 | **Writes are atomic and verified:** write to a temporary file, replace, re-read, and check. Output is pretty-printed with sorted keys. |
| DF-30 | **Single writer.** Only a conforming writer changes `manifest.json`. Other tools may put files in the bundle (a voice tool writing a `.vox`); they appear as unclassified until a writer's `refresh` adopts them. |
| DF-31 | The standard ships a JSON Schema for version 2 and one for version 1. |

## 7. Asset kinds and tiers

| `kind` | `variant` | Shape | Derived from |
|--------|-----------|-------|--------------|
| `description` | none | `CHARACTER.md` | none |
| `portrait` | none | 9:16, head to mid-chest, three-quarter view | none (the anchor) |
| `face` | none | square, face centered | `portrait` |
| `view` | `front`, `profile`, `back` | 9:16, framed like the portrait | `portrait`, `face` |
| `expression` | an emotion name | square, framed like `face` | `face`, `portrait` |
| `vox` | none | a `.vox` file | none |
| `voiceSample` | `neutral`, or a register name | `.m4a` | the `.vox` |
| `dossier` | none | the dossier page | everything else (DF-46) |
| `sourcePhoto`, `lora`, `training`, `crowdRef` | | unchanged from version 1 | |

| ID | Requirement |
|----|-------------|
| DF-32 | **The view set** is `portrait` (which is the three-quarter view) plus `view` `front`, `profile` and `back`. The profile always faces screen-left. |
| DF-33 | **Expressions** are separate images, one per emotion. The version 2 set is `happy`, `sad`, `frightened`, `mad`. The face crop stands for neutral and is not generated. The set is the same for every character. |
| DF-34 | **Retired kinds:** `turnaround`, `faceSheet`, `expressions`, `wardrobe`, `palette`. A reader of version 1 recognizes them; a writer never produces them. Wardrobe and palette are a project's scene style, not a character's assets, and don't count toward completeness. |
| DF-35 | **Role tiers:** `lead`, `supporting`, `guest`, `narrator`, `costar`, `underfive`, `background`. Major is `lead`, `supporting`, `guest`, `narrator`. |
| DF-36 | **The requirements table is data,** shipped as a file in this repository, with each kind marked required, recommended or not needed per tier. **Complete** means every required asset for the tier exists as `selected`. Implementations read the table; they don't restate it. |
| DF-37 | The version 2 table is version 1's (SwiftSemblanzas §5.4) with these changes: where it required a turnaround it requires the view set; `expression` is required for `lead` (the four), recommended for `supporting` and `guest`, and not needed otherwise; `wardrobe` and `palette` rows are removed. The `face` row is open (Q3). |
| DF-38 | **Voice samples:** a neutral read on each model size, plus three or more range samples drawn from the character's own lines. The lines are listed in `voice/samples.yaml`. There is no fixed list of registers. |

## 8. CHARACTER.md and the face crop

| ID | Requirement |
|----|-------------|
| DF-39 | `CHARACTER.md` has front matter (`type: character`, `character`, `role`, `age`, `pronouns`, `occupation`, …) and a body with these sections, in order: Logline, Appearance, Personality, Backstory, Arc, Relationships, Voice & Speech, Pronunciation, Wardrobe. **Full** (major tiers) has all of them. **Short** (`costar`, `underfive`) has Logline, Appearance, and Voice & Speech. |
| DF-40 | Unknown front-matter keys are preserved on write. In Relationships, other characters are referred to by their exact canonical name. |
| DF-41 | **The face crop:** a square centered on the largest detected face in the selected portrait, with a side 1.8 times the larger dimension of the face box, clamped to the image, never upscaled, saved as PNG. A hand-set box replaces the detected one and is recorded in provenance. How a face is detected is the implementation's. |

## 9. The dossier page

`<CHARACTER>-dossier.html` is the one HTML file in the bundle.

| ID | Requirement |
|----|-------------|
| DF-42 | **One self-contained file.** Styles, scripts, fonts, images and voice samples are all embedded. The page makes no network request and references no other file. Sent on its own, it loses nothing. |
| DF-43 | **Page copies, not originals.** Portrait and views are embedded as JPEG at 720×1280; face and expressions as JPEG at 512×512; quality 80. Sizes are set in one place in the template. Voice samples and subset fonts are embedded as they are. Everything is a `data:` URI. The copies are not stored in the bundle. |
| DF-44 | **The record is embedded** as `<script type="application/json" id="character-record">`, so a tool holding only the page can read the character. |
| DF-45 | **Stable output.** A renderer SHOULD produce identical bytes from identical inputs and template: no render timestamps, fixed encoder settings, stable ordering. This is a property of one implementation. Byte equality between two implementations is not required, because image encoders differ. |
| DF-46 | The page is registered as `kind: dossier`. Its `derivedFrom` covers `CHARACTER.md`, the `CAST.md` member, a checksum of every other file in the bundle except the manifest, and the template's version and hash. The page also records the template version and hash in a `<meta>` tag. A newer template makes the page stale. |
| DF-47 | **The field list is data,** shipped in this repository: the seven tabs (Profile, Portrait, Face, Views, Expressions, Voice, Samples) and, per tab, every field in order, each with a stable key (`profile.age`, `voice.pronunciation`), a label, a kind (text, long text, list, image, image set, audio) and its empty text. Every renderer, and any native editor meant to match the page, lays out from this list. None adds, drops or reorders a field. |
| DF-48 | **The template is shipped in this repository:** an HTML skeleton, a stylesheet generated from the design tokens, and a script of custom elements (`<dossier-tabs>`, `<dossier-field>`, `<dossier-image-set>`, `<dossier-audio>`). The tokens (type scale, colors, spacing, radii) are a data file. The template has a version number. |
| DF-49 | **Content is plain HTML inside the custom elements.** Script only adds behavior: tabs, a lightbox, one audio player at a time. With script off, every tab shows, stacked in order; that is also the print layout. |
| DF-50 | Tabs and fields are anchors (`#voice`, `#profile.age`). Audio plays on click only. The page has light and dark modes and works at phone width. One file serves a narrow and a wide layout. |
| DF-51 | **Other characters are plain-text names,** never links to other files. A host application MAY intercept a click on a name or a field; the page posts the field key to a host message handler when one is present and does nothing otherwise. |
| DF-52 | Only `selected` assets are shown. Missing required assets are listed by name. Integrity problems (a missing file, a hash mismatch, a stale selection, a name mismatch) appear as a banner at the top. Provenance is a line under each tab. |
| DF-53 | A complete lead's page should be about 3 MB. A validator warns above 10 MB. |

## 10. Validation

A validator never changes anything.

| ID | Requirement |
|----|-------------|
| DF-54 | **Errors:** the bundle name and `character` don't match; unknown `manifestVersion`; a file is missing, or its hash or size doesn't match; `manifestChecksum` doesn't match; an asset has no `files` entry; more than one `selected` for a `kind` + `variant`; a path escapes the bundle. |
| DF-55 | **Warnings:** unclassified files; stale derived assets; the page is over 10 MB or references anything outside itself; wrong shape (`portrait` or `view` not 9:16, `face` or `expression` not square); a required expression missing for the tier; a sidecar `.json` in the bundle; `CAST.md` `manifest:` doesn't point at this bundle; an orphan bundle. |
| DF-56 | **Report:** completeness against the tier, listing missing required assets by name. |
| DF-57 | Each error and warning has a stable code in the specification, so two validators report the same finding the same way. |

## 11. Version 1 to version 2

What changed from the record as first drafted, and what a migrated bundle looks
like. The migration tool is an implementation's.

| Version 1 | Version 2 |
|-----------|-----------|
| `characters/<CHARACTER>/` | `characters/<CHARACTER>.dossier/` |
| `dossier.html`, linking to assets by relative path | `<CHARACTER>-dossier.html`, everything embedded |
| Relationships link to other dossiers | plain-text names |
| `characters/index.html` cast index | removed |
| `turnaround`, `faceSheet`, `expressions` | the view set, `face`, `expression` |
| `wardrobe`, `palette` | not character assets |
| Fixed range samples (neutral, angry, quiet, joyful) | neutral, plus any three or more from the character's lines |
| Sidecar `.json` next to images | folded into `provenance` |
| Candidates and rejected images inside `images/` | candidates in `.generations/`; the bundle holds what was selected or kept |
| Free-form image file names | `<kind>[-<variant>]-<sha8>.<ext>` |

## 12. Deliverables

| Path | Contents |
|------|----------|
| `docs/DOSSIER-FORMAT.md` | The specification: §3 to §11 of this document as normative text, with examples. |
| `schemas/` | JSON Schema for the manifest (versions 1 and 2), `samples.yaml`, and the embedded record. |
| `data/tiers.json` | The requirements table (DF-36). |
| `data/fields.json` | The field list (DF-47). |
| `data/tokens.json` | The design tokens (DF-48). |
| `template/` | The page template: skeleton, stylesheet, custom elements. Versioned. |
| `examples/` | Conformance fixtures: valid bundles, and one invalid bundle per error and warning code. |
| `CHANGELOG.md` | Format versions and template versions. |

**Versioning.** The format version is `manifestVersion`. The template has its
own version. A change that makes an existing valid bundle invalid is a new
format version.

## 13. Acceptance

1. A reader written from the specification alone, with no access to
   SwiftDossier, opens every valid fixture and rejects every invalid one with
   the expected code.
2. The manifest schemas validate every fixture's `manifest.json`.
3. The template, filled by hand for one fixture, opens offline in a browser
   with script off and shows all seven tabs.
4. `data/fields.json` has every field the page shows, and nothing the page
   doesn't.

## 14. Depends on

Nothing. The source text is already written (§1).

## 15. Blocks

- **SwiftDossier:** implements this.
- Through it: the podcast-granville migration, Personaje, and the Vinetas app.

## 16. Open questions

| # | Question | Recommendation |
|---|----------|----------------|
| Q1 | **License.** *Decided 2026-10-03:* CC0 1.0 Universal, the same as vox-format, for everything in the repository. Fonts embedded in the template keep the OFL. | — |
| Q2 | **Fixtures.** The only real characters live in a private repository. Their images and descriptions can't go into this public one without a decision. | Make a synthetic character for the public fixtures. Keep the real ones as private fixtures in the implementation's tests. |
| Q3 | **Tier requirement for `face`.** Version 1 had no face crop; the bundle draft doesn't give its row. | Required wherever `portrait` is required, since it is derived from the portrait at no cost. |
| Q4 | **Do the template, field list and tokens belong here or in SwiftDossier?** Decided 2026-10-03: here, "for the moment". | Revisit once a second renderer exists or the first one finds the split awkward. |
| Q5 | **Canon facts.** The Profile tab shows facts with a source (Stated, Inferred, Author) and marks generated values. Where and how `CHARACTER.md` stores them is defined in Personaje's CHARACTER_CREATION.md and isn't carried into this document yet. | Bring the storage rule into §8 before the specification is written. |
| Q6 | **The type identifier.** The draft uses `io.intrusive-memory.dossier`. A vendor-neutral standard may want a neutral one. | Keep the draft identifier until someone outside the organization implements the format. |
| Q7 | **Version 1 in the specification.** Only two version 1 records exist. | Describe version 1 in an appendix for readers; give it a schema; don't write fixtures beyond those two. |
