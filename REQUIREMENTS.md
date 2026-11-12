---
type: requirements
state: draft
updated: 2026-11-12
sequence: 1 — first on the critical path of the Personaje effort
---

# dossier-format — Requirements

`dossier-format` is the language-agnostic standard for a character dossier. It
says what is in a `.dossier` bundle, what the manifest records, and what a
conforming dossier page contains. It has no implementation of its own.
**SwiftDossier** is the first implementation: the Swift reader, writer,
validator and page generator.

This document is the requirements for the standard. The deliverables it asks
for (§13) are a specification, schemas, data files, the page template and
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
wins. The differences are listed in §12.

## 2. Scope

**In the standard:** names; discovery; the bundle layout; file naming; the
manifest; asset kinds, shapes and statuses; role tiers and what each requires;
CHARACTER.md; the face-crop rule; voice files; the dossier page's contents and
its template; validation results; versioning. Since 2.1.0, location bundles too: a
second bundle type that holds a location's description and plates, with its own index,
`LOCATIONS.md`, which `PROJECT.md` declares, and one synthesized LOCATIONS page for all of
a project's locations (DF-79 to DF-84, DF-96 to DF-99).

**Not in the standard:**

- Any programming language, API or CLI.
- How images or voices are generated, and by which model.
- `CAST.md` itself. Its format belongs to SwiftReparto. The standard says only
  which `CAST.md` fields it reads.
- `PROJECT.md` itself. Its format belongs to SwiftProyecto. The standard says only which
  `PROJECT.md` fields it reads (DF-96).
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
| DF-13 | **The bundle is the character's folder,** the one source of truth, read and written in place. It is not an export. The files on disk are the source of truth, and the manifest is an index of them: an edit isn't an alteration until it's saved and the file in the directory reflects it, and a hash mismatch means the manifest is behind the disk, not that the file is wrong. Readers and validators judge only what's on disk. |
| DF-14 | **The writer names image files:** `images/<kind>[-<variant>]-<sha8>.<ext>`, where `<sha8>` is the first 8 hex digits of the file's SHA-256 when the file was added. It records those bytes, and the manifest's hash is the authority: when `refresh` accepts a changed image, the file keeps its name and is never renamed (§5.6). |
| DF-15 | Voice files keep the names their producer gives them: `voice/<CHARACTER>.vox`, `voice/sample-<variant>.m4a`. |
| DF-16 | **No sidecar files.** A generator's sidecar metadata is folded into the asset's `provenance`. A `.json` sidecar inside a bundle is a validation warning. |
| DF-17 | **Candidates live outside the bundle,** in `<charactersDir>/.generations/<CHARACTER>/`. A render enters the bundle when it is selected or explicitly kept. The standard defines this location and nothing about its contents. |
| DF-18 | A writer doesn't modify an original in `images/` once it is in the bundle, and originals are never embedded in the page (§9). The disk is still the truth about an original (DF-13). A writer MAY strip metadata when it copies an image in: pixel data is untouched, embedded records are read for provenance first, and the stored hash and file name come from the stripped bytes. In a PNG, metadata means the chunks `tEXt`, `zTXt`, `iTXt`, `eXIf` and `tIME`; chunks such as `iCCP`, `gAMA` and `sRGB` are kept. |
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
| DF-26 | **`status`** is `selected`, `candidate` or `rejected`. At most one `selected` per `kind` + `variant` (for `voiceSample`, per `kind` + `variant` + `model`, because DF-38 asks for a neutral read on each model size). Selecting one demotes the previous selection of that combination to `candidate`. Nothing is ever deleted implicitly. |
| DF-27 | **`derivedFrom`** on `face`, `view`, `expression`, `voiceSample` and `dossier` records every input: the SHA-256 of each file and record, or, for a hosted voice, its provider and voice ID (DF-76). When an input's selected file changes, the derived asset is **stale**: flagged, never deleted. An imported `face`, `view` or `expression` isn't derived (DF-77). |
| DF-28 | **`provenance`** records `provider`, `model`, `prompt` (the prompt actually sent), `seed`, and `references`: `{path, sha256}` for every reference image sent. An imported file has `provider: "import"`. A hand-set face-crop box is recorded here. |
| DF-29 | **Writes are atomic and verified:** write to a temporary file, replace, re-read, and check. Output is pretty-printed with sorted keys. |
| DF-30 | **Single writer.** Only a conforming writer changes `manifest.json`. Other tools may put files in the bundle (a voice tool writing a `.vox`); they appear as unclassified until a writer's `refresh` adopts them. `refresh` is also the one way to accept a changed file; an ordinary write keeps the recorded hash. `refresh` drops the entry of a missing file with no asset, refuses a missing file an asset points at, and reports each (§5.6). |
| DF-31 | The standard ships a JSON Schema for version 2 and one for version 1. |
| DF-75 | **How a delivery instruction was sent** is `provenance.instructMethod` on a `voiceSample`: `parameter` (sent alongside the text) or `audio-tag` (written into the text as inline tags the engine interprets), or a tool's own word. `instructApplied` still records only whether the delivery was honoured, `yes`, `no` or `unverified`. A tool that sends audio tags and doesn't check the result writes `audio-tag` and `unverified`. |
| DF-76 | **A hosted voice** is a `derivedFrom` record `{role: voice, provider, voiceId}`, with no path and no hash. `provider` is lowercase, matching the member's normal-form `voices` key, and `voiceId` is non-empty. A `voiceSample` needs a `vox` or a `voice` input: `voice` when the member's `voices` entry for that provider is a bare voice ID, `vox` when the ID lives in a `.vox`. A selected asset with a `voice` input is stale when the member's normal-form `voices[provider]` doesn't contain `voiceId`, the key's absence included. With no member, neither a `voice` nor a `castMember` input is checked, and neither makes the asset stale. The specification gives a worked example. |
| DF-77 | **An imported asset.** `provenance.copiedFrom`, a project-relative path, is allowed on any kind, set when the file was brought in unchanged from elsewhere in the project. A `face`, `view` or `expression` with `copiedFrom` isn't derived: it needs no `derivedFrom` and is never stale. The schema expresses this as a conditional. A `portrait` with `copiedFrom` keeps its `artStyle` check. Decided: Q8. |
| DF-88 | **`displayName`** is an optional top-level manifest string: how people name the character in prose, captions and prompts. It is display text, never a key and never canonicalized. The `CAST.md` member's `displayName` wins, as its `role` does; the manifest's is a copy for a reader with no member. When both are present and differ, `W-DISPLAY-NAME`. |
| DF-89 | **`storyboardLabel`** is an optional asset string: the phrase a storyboard or image tool uses for the image when it sends it as a reference. Display text, like `label`; nothing in the format reads it. |
| DF-90 | **`provenance.copiedFromSha256`** is the SHA-256 of the file at `copiedFrom` when it was copied. It is valid only with `copiedFrom`. It is informational, since the source is outside the bundle. A writer that recorded it as `provenance.sha256` moves it; until then `provenance.sha256` is an unknown key. |
| DF-91 | **`provenance.voiceId` and `provenance.creditsUsed`** on a generated asset: the hosted voice's identifier as sent (a non-empty string), whether it came from the member or from a `.vox`, and what the service charged, in its own units (a number, 0 or more). Both are informational; staleness reads `derivedFrom`. |
| DF-92 | **`provenance.postProcess`** records processing applied to a generated file after it was made: `{tool, chain, dry?, notes?}`, with `tool` an object as in `provenance.tool`, `chain` the tool's identifier for the processing, and `dry` the project-relative path of the unprocessed original, kept outside the bundle. The file in the bundle is the processed one. Processing doesn't affect staleness. A writer that recorded this as `provenance.machineVoice` moves it. |
| DF-93 | **Lowercase is Unicode's default full lowercase mapping,** in the member's normal form and in a `voice` record's `provider`. A `provider` is lowercase when lowercasing it changes nothing; `vÖx` isn't. The schema states this as a generated pattern, exact for Unicode 17.0; the text decides for later code points. |
| DF-94 | **A malformed `voice` record is stale.** A `voice` record with no `provider` or `voiceId`, with either not a non-empty string, or with a `provider` that isn't lowercase is `E-SCHEMA`, and, when there is a member, its asset is also `W-STALE`, because it can't match the member's `voices`. It never makes a voice hosted. |
| DF-95 | **Project-relative sources.** `provenance.source` is allowed on any kind: on a `voiceSample` the line's `file:line` or `sampleLine`, as before, and on another kind the project-relative path the content came from. A `references` entry may carry `source`, the project-relative path of an image sent that isn't in the bundle. Both are informational. |

## 7. Asset kinds and tiers

| `kind` | `variant` | Shape | Derived from |
|--------|-----------|-------|--------------|
| `description` | none | `CHARACTER.md` | none |
| `portrait` | none | 9:16, head to mid-chest, three-quarter view | none (the anchor) |
| `face` | none | square, face centered | `portrait` |
| `view` | `front`, `profile`, `back` | 9:16, framed like the portrait | `portrait`, `face` |
| `expression` | an emotion name | square, framed like `face` | `face`, `portrait` |
| `vox` | none | a `.vox` file | none |
| `voiceSample` | `neutral`, or a register name | `.m4a` | the `.vox`, or a hosted voice (DF-76) |
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
| DF-38 | **Voice samples:** a neutral read on each model size (one neutral read for a hosted voice, DF-78), plus three or more range samples drawn from the character's own lines. The lines are listed in `voice/samples.yaml`. There is no fixed list of registers. |
| DF-78 | **A hosted voice meets the voice rows.** A character's voice is hosted when a selected `voiceSample` has a `voice` input that is current (DF-76). Then `vox.1.7b` and `vox.0.6b` are satisfied, and one selected `neutral` sample with a current `voice` input, whatever its `model`, satisfies both `sample.neutral.1.7b` and `sample.neutral.0.6b`. `sample.range` and `voicePrompt` are unchanged. The table keeps its rows and IDs; the specification states the rule in the check definitions, with a worked example. |
| DF-85 | **View variant families.** Besides `front`, `profile` and `back`, a `view` variant may be `storyboard` or `storyboard-<slug>` (a storyboard's reference image of the character) or `look-<slug>` (the character in another look, framed like the portrait). A slug is lowercase ASCII letters and digits in runs joined by single hyphens. Anything else, `look` alone included, is `W-VARIANT`. The vocabulary is closed: a one-off is a look. |
| DF-86 | **An imported image isn't checked for shape.** A `face`, `view`, `expression` or `plate` with `provenance.copiedFrom` is never `W-SHAPE`, as DF-77 makes it never stale. A `portrait` with `copiedFrom` keeps its shape check, as it keeps its `artStyle` check. |
| DF-87 | **An imported image keeps its format.** A file brought in with `copiedFrom` keeps its bytes, so it may be PNG (`.png`) or JPEG (`.jpg`); every other v2 image is PNG. Its name is `<kind>[-<variant>]-<sha8>.<ext>`. |

### Location bundles

| ID | Requirement |
|----|-------------|
| DF-79 | **Two bundle types.** The top-level `dossierType` says which a bundle is: `character`, the default when it is absent, or `location`. Any other value is reserved and read as `character`. Nothing else, such as the directory a bundle is in, decides it. A 2.0.0 character bundle needs no change. |
| DF-80 | **A location is found from the locations index that `PROJECT.md` declares** (DF-96), and from nothing else: not a file's name, and not its being beside `CAST.md`. The index, `LOCATIONS.md` by convention, has YAML front matter with `type: locations`, `schemaVersion: 1` and a `locations` list, each entry with `location` (the canonical name) and an optional `manifest:` pointer relative to the index. Pointers, `W-POINTER`, `E-MANIFEST` and `E-CAST` work as for `CAST.md`. Orphans are looked for in `locations/` beside the index, and only once the index has been read. The location's name is canonical by DF-2 and held in the manifest's `character`, so the manifest keeps its 2.0.0 shape. A `CAST.md` member that points at a location bundle, or a `LOCATIONS.md` entry that points at a character bundle, is `E-TYPE-MISMATCH`. *Revised 2026-11-12 (Q9): the index was found beside `CAST.md`.* |
| DF-81 | **`LOCATION.md`** is a location's description, the `description` asset at that path: front matter `type: location`, `location` (the name, compared as `E-NAME-MISMATCH`) and an optional `theme`, and a free Markdown body for people. `## Blocking` and `## Views` are recommended. Footnotes follow the `CHARACTER.md` rule. |
| DF-82 | **A location bundle holds `description`, `plate`, `view` and `sourcePhoto`.** Any other kind is `E-SCHEMA`, and `plate` is `E-SCHEMA` in a character bundle. A **plate** is an empty set for one camera setup: kind `plate`, a required lowercase slug `variant` naming the view, 16:9, at `images/plate-<variant>-<sha8>.png`, one `selected` per variant. It isn't derived and is never stale. A `view` in a location bundle MUST be imported (`copiedFrom`). A location has no tier, no completeness and no `W-INCOMPLETE`. |
| DF-83 | **The `location` record** is an optional manifest object: `name`, `description`, `theme` and `views`, the producing tool's recipe per view (`prompt`, `rule`, `refs`, `exterior`, `theme`), keyed by plate variant. Every key is optional and unknown keys are preserved. The record and the plates aren't compared. |
| DF-84 | **A location bundle has no page of its own.** It has no `dossier` asset and no preview, and per-location pages are out of scope. Its locations are shown on the project's one LOCATIONS page (DF-97), where each location's section has, in order: its name (`location.name`, or the entry's `location`), `LOCATION.md`'s body, each selected plate labelled with its variant (in `location.views` order, then byte order), then the selected views. *Revised 2026-11-12 (Q10): a host showed each bundle on its own, and there was no page.* |
| DF-96 | **`PROJECT.md` declares the locations.** Its format is SwiftProyecto's; the standard reads two of its front-matter fields, `locations` (a string: the index's path, relative to `PROJECT.md`) and `title`, and writes neither. No `PROJECT.md`, no front matter, or no `locations` key: the project has no locations, nothing is read or listed, and nothing is reported. A `PROJECT.md` that isn't UTF-8, whose front matter isn't a YAML mapping, or whose `locations` isn't a valid index path (non-empty, not starting with `/`, not leaving the project directory): `E-CAST`. A path that reaches no file: `W-POINTER`, and no locations. An index that can't be read (not UTF-8, YAML that doesn't parse, `type` other than `locations`, no `locations` list, an entry with no `location`): `E-CAST`. Character discovery never reads `PROJECT.md`, so none of these changes a character bundle's result. |
| DF-97 | **One LOCATIONS page, synthesized.** A viewer builds a single self-contained HTML page showing every entry of the index, in its order, each with DF-84's content, from the index and the bundles its entries point at, as they are on disk. It is derived: never written by hand, never the authority, in no bundle and no manifest, and not validated. It has the project's title, no script and no findings banner. Plates are embedded as JPEG 1280×720 copies (DF-43's 720×1280, turned to 16:9), views as JPEG copies that fit inside 1280×720, at quality 80, none stored. Its output is stable, as DF-45 says. An entry with no bundle, or one that can't be shown, says so in its section. |
| DF-98 | **The page is built on demand and cached under a key,** as a preview is (DF-68 to DF-72): in `.locations-page/<key>.html` beside the index, with `.locations-page/.gitignore` holding `*`. The key is the SHA-256 of `dossier-locations-page`, the rules' version, the hash of the index's bytes, the hash of `PROJECT.md`'s title, one line per entry holding the hash of the `manifest.json` it reaches, and the LOCATIONS page template's hash. A current page is shown with no write; otherwise the viewer builds, stores and shows. A rebuild, which any viewer may offer, writes nothing in a bundle. A viewer MAY export a copy, which the format gives no meaning. |
| DF-99 | **The LOCATIONS page template** is shipped in `template-locations/`, versioned and hashed apart from the dossier template so that neither makes the other's output stale. It carries `template/dossier.css` and `template/fonts.css` unchanged, so the page looks like a dossier page, and its hash covers them. **A host** shows the page read-only when the index or the `locations/` directory beside it is selected, and at the location's section when a location bundle is selected, with the validator's findings above. A location bundle no entry points at is one item with its finding and no page. |

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
| DF-52 | Only `selected` assets are shown. Missing required assets are listed by name. Integrity problems (a stale selection, a name mismatch) appear as a banner at the top. A missing file or a hash mismatch refuses the render, and nothing is changed (§11). Provenance is a line under each tab. |
| DF-53 | A complete lead's page should be about 3 MB. A validator warns above 10 MB. |

**Previews.** A bundle written by hand, or by a tool that never renders, has no page, and a page that exists can be behind its bundle. A viewer needs to show the bundle anyway, from what is on disk, at a cost it can pay on every selection.

| ID | Requirement |
|----|-------------|
| DF-68 | **Previews live in the bundle, hidden.** A viewer keeps its previews in `.preview/` in the bundle's root, outside `files`, `manifestChecksum` and validation. A preview file is `.preview/<key>.html`. The store is left out of version control; a viewer writes `.preview/.gitignore` with `*`. A viewer puts nothing else in the bundle, except through a rebuild (DF-73). |
| DF-69 | **The key is cheap and names the inputs a writer records.** It is the SHA-256 of five lines: `dossier-preview`, the preview rules' version, the hash of `manifest.json`'s bytes, the `CAST.md` member's hash (or nothing), and the current template's hash. It reads no image, voice or description bytes. An edit that no writer recorded isn't seen until a rebuild. |
| DF-70 | **A current preview is shown with no write.** If `.preview/<key>.html` exists, the viewer shows it and writes nothing. Otherwise it builds, stores and shows. It doesn't build while the bundle is being updated (DF-64); it shows the preview it has and waits. |
| DF-71 | **A preview can be built from any bundle with a description.** It is the page (§9), filled from the bundle as it is on disk. A broken inventory goes on the banner instead of refusing, a file that can't be read is left out, the member is optional, and any page in the bundle is ignored. Only a `CHARACTER.md` that is missing or isn't UTF-8 stops it. On a bundle a render accepts, it is the same bytes as that implementation's page. |
| DF-72 | **Storing never loses the last preview.** The viewer writes to a temporary name, renames it into place, and only then removes everything else in the store but `.gitignore`. A failed build or write removes nothing. Viewers need no lock: a preview that loses a race is rebuilt at the next showing. |
| DF-73 | **A rebuild is explicit and goes through a writer.** A person asks for it. A conforming writer, holding an update marker, refreshes the manifest from the disk and then builds and stores the preview even when one with that key exists. A refresh that refuses is reported, and the preview is built anyway. |
| DF-74 | **A host shows the preview.** Selecting a version 2 bundle shows its preview (DF-60), read-only, loading nothing from outside the file. A host that links a conforming writer MAY offer a rebuild. One that links only a reader still shows a stored preview and says when none matches the key. |

## 10. Hosting

A **host** is any application that shows a project's files and comes upon a
bundle: a project browser, an editor's sidebar, a scene tool's cast view. A
host is not a reader. It links one (SwiftDossier's `DossierCore`, or any
conforming reader) and asks it; the rules below say what the host itself
does and does not know.

| ID | Requirement |
|----|-------------|
| DF-58 | **One item.** A host that scans directories presents `<CHARACTER>.dossier` as a single item, named for the directory, and never lists or offers its contents. The package type reserved in DF-19 is how the operating system tells the host it is a bundle; where the type isn't registered a host MAY recognize the `dossier` extension directly. |
| DF-59 | **The manifest is the map.** A host locates the page, the face crop and every other asset through the manifest's `assets` entries (`kind: dossier`, `face`, …) by way of a reader, never by file name. A `<CHARACTER>-dossier.html` or a version 1 `dossier.html` found by listing the directory is not the page; the manifest says which file is. |
| DF-60 | **Selecting the item shows the bundle.** The host shows a version 2 bundle through its preview (DF-74), read-only in a web view, and a version 1 bundle's page with the bundle directory as the page's base, so its relative references still resolve. The host doesn't edit the bundle: the only thing it writes in one is the preview store (DF-68), and it changes `manifest.json` only through a rebuild (DF-73). A host that wants a character changed hands off to a writer (DF-30), for example through a URL scheme carrying the bundle path and a field key (DF-51). |
| DF-61 | **The host shows what the validator finds.** A bundle with an unknown `manifestVersion`, a name mismatch (DF-8) or an orphan (DF-10) is still one item. The host names the problem with the validator's code (DF-57): above the preview when one can be built, and in its place when none can (DF-71). It never hides, deletes or repairs the bundle. |
| DF-62 | **Hosts carry no format knowledge beyond the type.** Every rule above is answered by the reader the host links. A host that cannot link a reader shows the item and says a reader is needed. The reader MAY supply the item's icon (the selected `face` crop where there is one); the host's default icon is a person. |
| DF-63 | **Discovery stays with `CAST.md`.** A host's scan is presentation only (DF-7). Finding a bundle on disk does not make it a cast member; a bundle no `CAST.md` member points at is an orphan (DF-10) and is shown as one. |

**Update status.** A read-only application needs to know that a bundle is being updated, whichever tool or language is updating it, and whether or not the application was running when the update began.

| ID | Requirement |
|----|-------------|
| DF-64 | **A marker says a bundle is being updated.** It is a hidden file in the bundle's root, `.update-<id>.json`, and so is outside `files` and `manifestChecksum`. It is a signal, not a lock, and DF-30 still applies. Several may exist at once. |
| DF-65 | **A writer holds a marker for the whole update.** It writes and renews the marker atomically, sets `expiresAt` no more than 3600 seconds ahead, and removes the marker only after its last replacement of `manifest.json`, including when the update fails. |
| DF-66 | **A marker can't report an update forever.** A reader counts a marker only when `now < expiresAt <= now + 3600 seconds`. Any other marker, unreadable ones included, doesn't count. |
| DF-67 | **A host keeps the last page during an update.** It indicates the update on the item, doesn't report a problem it finds during the update, and reads the bundle again once when no marker is active. It never creates, renews or removes a marker (DF-60). |

## 11. Validation

A validator never changes anything.

| ID | Requirement |
|----|-------------|
| DF-54 | **Errors:** the bundle name and `character` don't match; unknown `manifestVersion`; a file is missing, or its hash or size doesn't match; `manifestChecksum` doesn't match; an asset has no `files` entry; more than one `selected` for a `kind` + `variant` (`voiceSample`: + `model`); a path escapes the bundle. |
| DF-55 | **Warnings:** unclassified files; stale derived assets; the page is over 10 MB or references anything outside itself; wrong shape (`portrait` or `view` not 9:16, `face` or `expression` not square); a required expression missing for the tier; a sidecar `.json` in the bundle; `CAST.md` `manifest:` doesn't point at this bundle; an orphan bundle. |
| DF-56 | **Report:** completeness against the tier, listing missing required assets by name. |
| DF-57 | Each error and warning has a stable code in the specification, so two validators report the same finding the same way. |

## 12. Version 1 to version 2

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

## 13. Deliverables

| Path | Contents |
|------|----------|
| `docs/DOSSIER-FORMAT.md` | The specification: §3 to §12 of this document as normative text, with examples. |
| `schemas/` | JSON Schema for the manifest (versions 1 and 2), `samples.yaml`, the embedded record, and `LOCATIONS.md`'s front matter. |
| `template-locations/` | The LOCATIONS page template (DF-99). Versioned. |
| `data/tiers.json` | The requirements table (DF-36). |
| `data/fields.json` | The field list (DF-47). |
| `data/tokens.json` | The design tokens (DF-48). |
| `template/` | The page template: skeleton, stylesheet, custom elements. Versioned. |
| `examples/` | Conformance fixtures: valid bundles, and one invalid bundle per error and warning code. |
| `CHANGELOG.md` | Format versions and template versions. |

**Versioning.** The format version is `manifestVersion`. The template has its
own version. A change that makes an existing valid bundle invalid is a new
format version.

## 14. Acceptance

1. A reader written from the specification alone, with no access to
   SwiftDossier, opens every valid fixture and rejects every invalid one with
   the expected code.
2. The manifest schemas validate every fixture's `manifest.json`.
3. The template, filled by hand for one fixture, opens offline in a browser
   with script off and shows all seven tabs.
4. `data/fields.json` has every field the page shows, and nothing the page
   doesn't.

## 15. Depends on

Nothing. The source text is already written (§1).

## 16. Blocks

- **SwiftDossier:** implements this.
- Through it: the podcast-granville migration, Personaje, and the Vinetas app.

## 17. Open questions

| # | Question | Recommendation |
|---|----------|----------------|
| Q1 | **License.** *Decided 2026-10-03:* CC0 1.0 Universal, the same as vox-format, for everything in the repository. Fonts embedded in the template keep the OFL. | — |
| Q2 | **Fixtures.** The only real characters live in a private repository. Their images and descriptions can't go into this public one without a decision. | Make a synthetic character for the public fixtures. **Updated 2026-10-20:** the implementations (SwiftDossier, SwiftPersonaje) are public too, so real characters go in no repository's tests; they are checked only by local acceptance runs against the private project checkout. |
| Q3 | *Decided 2026-10-19 (DOSSIER-FORMAT §8.3, `data/tiers.json`): required wherever `portrait` is.* **Tier requirement for `face`.** Version 1 had no face crop; the bundle draft doesn't give its row. | Required wherever `portrait` is required, since it is derived from the portrait at no cost. |
| Q4 | **Do the template, field list and tokens belong here or in SwiftDossier?** Decided 2026-10-03: here, "for the moment". | Revisit once a second renderer exists or the first one finds the split awkward. |
| Q5 | *Decided 2026-10-19 (D9; DOSSIER-FORMAT §9.3): footnoted claims with the classes Stated, Inferred, Author; generated values listed in `draft.generated`.* **Canon facts.** The Profile tab shows facts with a source (Stated, Inferred, Author) and marks generated values. Where and how `CHARACTER.md` stores them is defined in Personaje's CHARACTER_CREATION.md and isn't carried into this document yet. | Bring the storage rule into §8 before the specification is written. |
| Q6 | **The type identifier.** The draft uses `io.intrusive-memory.dossier`. A vendor-neutral standard may want a neutral one. | Keep the draft identifier until someone outside the organization implements the format. |
| Q7 | **Version 1 in the specification.** Only two version 1 records exist. | Describe version 1 in an appendix for readers; give it a schema; don't write fixtures beyond those two. |
| Q8 | *Decided 2026-11-12 by the user (DF-77; DOSSIER-FORMAT §7): the `copiedFrom` waiver.* **Imported reference images.** A reference image brought into the bundle unchanged, such as a drawing of the character from elsewhere in the project, is filed as a `view` (or `face`, `expression`) with `provenance.copiedFrom` and no `derivedFrom`, which waives the kind's `derivedFrom` requirement and staleness. The alternative is a separate kind for imported reference images, leaving `view` always derived. | Keep the `copiedFrom` waiver: it adds no kind, so the kind list, `data/tiers.json`, `data/fields.json` and the page don't change, and a reader changes only by the one conditional. The cost is that "is this view derived?" is answered by `copiedFrom`, not by `kind`, and an imported view counts toward completeness and is shown on the Views tab like a generated one. |
| Q9 | *Decided 2026-11-12 by the user: "locations needs to be defined in PROJECT.md" (DF-80, DF-96; DOSSIER-FORMAT §16.2).* **Who owns `LOCATIONS.md`?** `CAST.md` belongs to SwiftReparto, and nothing owned a location index. | `PROJECT.md`, which SwiftProyecto owns, declares the index with its `locations` key, and discovery starts there. The index's own format stays defined here. |
| Q10 | *Decided 2026-11-12 by the user: "a LOCATIONS page showing all of them should be synthesized from the LOCATIONS.md" (DF-84, DF-97 to DF-99; DOSSIER-FORMAT §16.6, §16.7).* **A page for locations.** | One project-level page for every location, built on demand from the index and the bundles, cached under a key beside the index, with a template of its own. No per-location page. |
