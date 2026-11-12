---
type: changelog
updated: 2026-11-12
---

# Changelog

## Format 2.1.0 (unreleased)

Template 0.1.1, unchanged. A minor release: everything below is new and optional, so
`manifestVersion` stays 2 and no 2.0.0 fixture's result changes. It standardizes the shapes
a production's bundles already use that 2.0.0 didn't define: location bundles, two view
variant families, imported images of any shape and in JPEG, and six fields the schema let
through untyped. Keys that 2.0.0 left undefined are now typed, so a 2.0.0 bundle that used
one of these names with another type would now fail; no such bundle is known. Two 2.0.0
gaps are closed too.

- **§16, §3, §5.1, DF-79 to DF-84: location bundles.** `dossierType: "location"` makes a
  bundle a location: a place, holding its description and its **plates**, the empty sets a
  scene's people are painted onto, one per camera setup. Absent or `character`, a bundle is a
  character bundle as before; another value is reserved and read as `character`. A location
  is found from **`LOCATIONS.md`**, a second index beside `CAST.md` (`type: locations`,
  `schemaVersion: 1`, `locations: [{location, manifest?}]`, schema
  `schemas/locations.schema.json`), with orphans looked for in `locations/`. Its name is
  canonical and is held in the manifest's `character`, so the manifest keeps its 2.0.0 shape.
  Its description is **`LOCATION.md`** (`type: location`, `location`, optional `theme`; a free
  body, `## Blocking` and `## Views` recommended). It holds `description`, `plate`, `view`
  (always imported) and `sourcePhoto`, and any other kind is `E-SCHEMA`. A **plate** has a
  required lowercase slug `variant` naming its view, is 16:9, lives at
  `images/plate-<variant>-<sha8>.png`, isn't derived and is never stale. The optional
  **`location`** object records the location's `name`, `description`, `theme` and the
  producing tool's recipe per view. A location has no tier, no completeness, no member and
  **no page**: a viewer shows its name, `LOCATION.md`, its selected plates and its views,
  read-only, and builds no preview. `plate` in a character bundle is still `E-SCHEMA`.
- **New codes.** `E-TYPE-MISMATCH`: a `CAST.md` member points at a location bundle, or a
  `LOCATIONS.md` entry at a character bundle. `W-DISPLAY-NAME`: below. `E-CAST` also covers a
  `LOCATIONS.md` that can't be read, and `E-NAME-MISMATCH`, `W-ORPHAN` and `W-POINTER` cover
  locations.
- **§8.1, DF-85: view variant families.** `storyboard` and `storyboard-<slug>` (a storyboard's
  reference image of the character) and `look-<slug>` (the character in another look, framed
  like the portrait) aren't `W-VARIANT`. A slug is lowercase ASCII letters and digits joined by
  single hyphens. `look` alone, a family name with no slug, and anything else still is: the
  vocabulary is closed, and a one-off is a look (`look-second-body`).
- **§8.1, DF-86: an imported image isn't checked for shape.** A `face`, `view`, `expression` or
  `plate` with `copiedFrom` is never `W-SHAPE`, as DF-77 already makes it never stale. A
  portrait with `copiedFrom` keeps its shape check, as it keeps its `artStyle` check.
- **§4, DF-87: an imported image keeps its format,** PNG (`.png`) or JPEG (`.jpg`), since
  re-encoding it would change the bytes `copiedFrom` says were brought in unchanged. Every
  other v2 image is still PNG.
- **§5.1, DF-88: `displayName`,** an optional top-level string: how people name the character
  in prose, captions and prompts. The `CAST.md` member's `displayName` (now in the list of
  `CAST.md` fields read) wins, and the manifest's is a copy; when both are present and differ,
  `W-DISPLAY-NAME`. Not on the page yet.
- **§5.4, DF-89: `storyboardLabel`,** an optional asset string: the phrase a storyboard tool
  uses for the image when it sends it as a reference. Display text that nothing reads.
- **§6, DF-90: `provenance.copiedFromSha256`,** the hash of the source file when it was copied,
  valid only with `copiedFrom` (`E-SCHEMA` otherwise). *Migration:* a writer that recorded it as
  `provenance.sha256` moves it. Until then `provenance.sha256` is an unknown key, kept and
  read as nothing.
- **§6, DF-91: `provenance.voiceId`** (the hosted voice's identifier as sent, whether it came
  from the member or from a `.vox`) **and `provenance.creditsUsed`** (what the service charged,
  in its own units, 0 or more). Both are informational: staleness reads `derivedFrom`.
- **§6, DF-92: `provenance.postProcess`** records processing applied after generation:
  `{tool: {name, version?}, chain, dry?, notes?}`. `chain` is the tool's identifier for the
  processing, and `dry` the project-relative path of the unprocessed original, kept outside
  the bundle. The file in the bundle is the processed one, and staleness is unchanged.
  *Migration:* a writer that recorded `provenance.machineVoice: {chain, dry, tool}` moves it
  to `postProcess` with `tool` as `{"name": ...}`.
- **§6, DF-95: project-relative sources.** `provenance.source` is allowed on any kind (on
  another kind than `voiceSample`, the project-relative path the content came from), and a
  `references` entry may carry `source`, the project-relative path of an image sent that isn't
  in the bundle. `plate:<variant>` joins the reference roles.
- **§7, DF-93: lowercase means Unicode's full default lowercase mapping,** in the member's
  normal form and in a `voice` record's `provider`. The 2.0.0 schema's `^[^A-Z]+$` rejected only
  ASCII capitals, so it let `vÖx` through, which the text already ruled out; the schema now
  agrees with the text. The pattern excludes every code point that lowercasing changes in
  Unicode 17.0, generated and checked by `tools/build_provider_pattern.py`; for a code point
  assigned later, the text decides.
- **§7, DF-94: a malformed `voice` record is stale.** One with no `provider` or `voiceId`,
  either not a non-empty string, or a `provider` that isn't lowercase is `E-SCHEMA` and, when
  there is a member, `W-STALE`, because it can't match the member's `voices`. It never makes a
  voice hosted. 2.0.0 didn't say. `errors/E-SCHEMA-voice-input-provider-case` keeps `W-STALE` in
  `mayAlso`, unchanged; the new fixtures assert it.
- **`schemas/manifest-v2.schema.json`:** `dossierType`, `displayName`, `location`; kind `plate`,
  with its slug `variant`; `storyboardLabel`; `copiedFromSha256` (with `copiedFrom`),
  `creditsUsed`, `voiceId`, `postProcess`; `references[].source`; the generated `provider`
  pattern; a location bundle's kinds, and its views required to have `copiedFrom`; `plate`
  only in a location bundle. **New:** `schemas/locations.schema.json`.
- **Q9 and Q10** are open: who owns `LOCATIONS.md`, and a page for locations.
- **Fixtures (141):** `valid/location`, `valid/view-families`, `valid/display-name`,
  `valid/display-name-no-member-copy`, `valid/hosted-voice-provenance`,
  `valid/hosted-voice-non-ascii-provider`; `errors/E-SCHEMA-voice-input-provider-non-ascii-case`,
  `errors/E-SCHEMA-voice-input-malformed`, `errors/E-SCHEMA-location-kind`,
  `errors/E-SCHEMA-location-view-not-imported`, `errors/E-SCHEMA-plate-variant`,
  `errors/E-SCHEMA-plate-in-character`, `errors/E-SCHEMA-copied-from-sha256-alone`,
  `errors/E-SCHEMA-post-process-no-chain`, `errors/E-TYPE-MISMATCH`,
  `errors/E-TYPE-MISMATCH-location-entry`, `errors/E-CAST-locations-no-location`,
  `errors/E-NAME-MISMATCH-location`; `warnings/W-SHAPE-plate`,
  `warnings/W-SHAPE-imported-portrait`, `warnings/W-VARIANT-view-one-off`,
  `warnings/W-VARIANT-view-bare-look`, `warnings/W-VARIANT-view-family-not-slug`,
  `warnings/W-DISPLAY-NAME` and `warnings/W-ORPHAN-location`. A fixture project may now have a
  `LOCATIONS.md`. No existing fixture changed.

## Format 2.0.0 (2026-11-12)

Format 2 is released. The changes since rc.8:

Template 0.1.1, unchanged. No valid bundle becomes invalid, so `manifestVersion` stays 2:
each change below allows something rc.8 refused or warned about, or states a rule rc.8
left open, and the one schema rule added states a requirement §7 already made.

- **§6, DF-75: `provenance.instructMethod`** on a `voiceSample` records how the delivery
  instruction reached the engine: `parameter` (a separate value alongside the text) or
  `audio-tag` (inline tags in the text), or a tool's own word. `instructApplied` keeps its
  values and still records only whether the delivery was honoured. A tool that sends audio
  tags and doesn't check the result writes `audio-tag` and `unverified`.
- **§7, §8.2, DF-76: a hosted voice.** A new `derivedFrom` record,
  `{"role": "voice", "provider": "<provider>", "voiceId": "<id>"}`, with no `path` and no
  `sha256`, names a voice a service keeps. `provider` is lowercase, as the member's
  normal-form `voices` keys are. A `voiceSample` now needs a `vox` **or** a `voice` input:
  `voice` when the member's `voices` entry is a bare voice ID, `vox` when the ID is inside a
  `.vox`. A selected asset with a `voice` input is stale when the member's normal-form
  `voices[provider]` doesn't contain `voiceId`, including when the key is absent; with no
  member, neither a `voice` nor a `castMember` input is checked, one shared rule in §7 that
  rc.8 left unstated for `castMember`. §7 has a worked example. A bundle with no selected `vox`
  has neither `W-VOICE-ELSEWHERE` nor `W-VOICE-PROMPT`, which §8.2 now says.
- **§6, §7, DF-77: imported assets.** `provenance.copiedFrom` is allowed on any kind, not
  only `vox`: the file was brought in unchanged from elsewhere in the project. A `face`,
  `view` or `expression` with `copiedFrom` isn't derived: it needs no `derivedFrom`, and it
  is never stale, `artStyle` included. A portrait with `copiedFrom` keeps its `artStyle`
  check. Q8 is closed: the user chose this waiver over a separate kind on 2026-11-12.
- **§8.3, DF-78, `data/tiers.json`: a hosted voice meets the voice rows.** When a selected
  sample has a current `voice` input, the voice is hosted: `vox.1.7b` and `vox.0.6b` are
  satisfied, and one `neutral` sample with a current `voice` input, whatever its `model`,
  satisfies both neutral rows. The existing check rows take the case, so the table keeps its
  rows and IDs; only four labels and the `$comment` change. DF-38 says so.
- **Not yet on the page:** the Samples tab's provenance line reads only a `vox` record, so it
  shows no input for a hosted-voice sample. `template/` and `data/fields.json` don't change
  in rc.9.
- **DF-27** names `voiceSample` and the hosted-voice record, and points to DF-77.
- **`schemas/manifest-v2.schema.json`:** `instructMethod`; the `voice` record in
  `derivedFrom`; a `voiceSample`'s `derivedFrom` must contain a `vox` or `voice` record,
  which §7 already required of `vox` and the schema didn't check; the `derivedFrom`
  requirement on `face`, `view` and `expression` applies only when `provenance.copiedFrom`
  is absent.
- **Fixtures (116):** `valid/hosted-voice`, `valid/hosted-voice-supporting`,
  `valid/imported-view`, `warnings/W-STALE-input-voice`,
  `warnings/W-STALE-input-voice-provider-absent`, `warnings/W-INCOMPLETE-hosted-no-neutral`,
  `errors/E-SCHEMA-sample-no-voice-input` and `errors/E-SCHEMA-voice-input-provider-case`.
  No existing fixture changed.

## Format 2, release candidate 8 (2026-11-10)

Template 0.1.1, unchanged. No valid bundle becomes invalid, so `manifestVersion` stays 2.

- **§11.1, DF-68 to DF-74: the preview.** A viewer shows a bundle by building the page from
  what's on disk into `.preview/<key>.html`, a hidden store in the bundle, outside `files`,
  `manifestChecksum` and validation. The key is the SHA-256 of `dossier-preview`, the preview
  version (1), the hash of `manifest.json`'s bytes, the member's hash and the template's hash,
  so checking it reads only `manifest.json` and `CAST.md`. A stored preview with that key is
  shown with no write. Otherwise the viewer builds one leniently (a broken inventory goes on
  the banner, unreadable files are left out, the member is optional, any page is ignored),
  renames it into place, and only then removes everything else in the store but `.gitignore`.
  A **rebuild**, which a person asks for, is a writer's refresh (§5.6) under an update marker,
  followed by a build even when the key is unchanged. The store is kept out of git by
  `.preview/.gitignore` containing `*`.
- **§11:** the page is the only HTML file in the bundle's **inventory**. The rule that a broken
  inventory refuses a render is the page's and doesn't apply to a preview.
- **§12, DF-60, DF-61:** a host shows a version 2 bundle through its preview, and a version 1
  bundle's page as before. Its only write in a bundle is the preview store, plus
  `manifest.json` through a rebuild. A validator finding is shown above the preview, and in its
  place only when no preview can be built. A host that can't build shows a matching stored
  preview, or says none is stored.
- **§4:** `.preview/` added to the layout.
- **Fixtures:** `valid/preview-current` (a hit, beside an older preview and a leftover
  temporary file) and `valid/preview-out-of-date` (a miss). `conformance.json` gives each one's
  `preview.key` and `preview.hit`.

## Format 2, release candidate 7 (2026-11-01)

Template 0.1.1. No valid bundle becomes invalid, so `manifestVersion` stays 2.

- **`template/fragments.html`, rule 4:** a `markSeparator` fragment goes between two
  footnote marks with nothing between them, so `1`, `2` doesn't read as `12`. This is in the
  markup, because a CSS sibling selector also matches two marks with text between them.
- **Rule 3:** a line break inside a paragraph or list item continues it, and `**` and `*`
  may span one.
- **Field rule 2:** a definition cited only from another definition's text counts as never
  cited.
- **§11, DF-52, field rule 5:** a renderer refuses a bundle with `E-FILE-HASH` or
  `E-FILE-MISSING` on any file but the page being replaced, and changes nothing, so a
  re-render can't clear an integrity banner. A validator's results don't change.
- **Rule 3, `---`:** a line that is only `---` is dropped when reading description
  Markdown, and it ends the paragraph, list item or quote it follows, as a blank line does.
  The rule has no code fences, so a `---` between fences is dropped too. A section with only
  `---` lines under it is empty (field rule 3).
- **Rule 3, `>` quotes:** a line whose first non-space character is `>` is a quote line.
  Consecutive quote lines, and non-blank lines directly after one, are one `<blockquote>`. A
  quote directly after list-item text is inside its `<li>`; otherwise it's a block of its own.
  In Canon & Guardrails it's part of its item, or an item of its own (field rule 1).
  `<blockquote>` is a literal element, as `<p>`, `<ul>` and `<h4>` are, with its style from a
  new token, `component.blockquote`. The `canonItem` fragment's text is now in a `<div>`,
  because a quote can't sit in a `<span>`.
- **`data/fields.json`, rule 10:** `page.sources` is now a field of the Profile tab, before
  `profile.provenance`, so each tab still ends with its provenance line. Its key and the marks'
  `#page.sources` link don't change, and there are still 60 keys. `page.after` stays, with no
  fields, and its empty footer is hidden. A click on a mark on any tab opens Profile and scrolls
  to Sources, every time. With script off and in print, Sources shows once. A `page.*` anchor
  outside the tabs still scrolls and doesn't change the tab.
- **§5.6, DF-13:** the files on disk are the source of truth, and the manifest is an index of
  them. An edit isn't an alteration until it's saved and the file in the directory reflects it.
  `E-FILE-HASH` means the manifest is behind the disk, not that the file is wrong. Readers and
  validators judge only what's on disk.
- **§5.2, §5.6, §11, DF-30:** a writer's rescan adds an entry for an unlisted file, and keeps the
  recorded hash and size of a listed file that doesn't match, and the entry of one that's missing,
  unless the write itself changed or removed it. *Refresh* is the one way to accept a changed
  file. It drops the entry of a missing file with no asset, refuses a missing file an asset
  points at, and reports each by path. A renderer still refuses `E-FILE-HASH` and
  `E-FILE-MISSING`. A validator's results don't change.
- **§4, §13, DF-14, DF-18:** a name's `<sha8>` records the bytes when the file was added, and the
  manifest's hash is the authority. A file refresh accepts keeps its name, and the report says
  when a name no longer matches its hash. A writer doesn't modify an original, and the disk is
  still the truth about it. §13 no longer calls the hash a file's identity, and §4 and DF-14 no
  longer say a name can't collide or claim to be something it isn't.
- **Fixtures:** `valid/page-wrapped-text`, which also has `---` lines, quotes and a mark on the
  Voice tab. Every page is regenerated with template 0.1.1, and each fixture's expected result
  is unchanged.

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
