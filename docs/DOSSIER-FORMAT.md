---
type: specification
state: draft
formatVersion: 2
updated: 2026-10-31
---

# The dossier format, version 2

A **dossier** is one dramatic character, as a folder: a `.dossier` bundle
holding the character's description, images, voice and a self-contained HTML
page, inventoried by `manifest.json`.

This document is normative. It implements [REQUIREMENTS.md](../REQUIREMENTS.md)
(DF-1 to DF-63); the requirement each section satisfies is cited in brackets.
Decisions D1–D10 and the evidence behind every property are in
[PROPERTY-INVENTORY.md](PROPERTY-INVENTORY.md).

Machine-readable parts: [`schemas/`](../schemas) (JSON Schema 2020-12) and
[`data/`](../data). Where this text and a schema disagree, this text wins and
the schema is a bug.

## 1. Conventions

- **MUST, MUST NOT, SHOULD, MAY** are used as in RFC 2119.
- **Reader** opens and reads a bundle. **Writer** creates or changes one.
  **Validator** reports on one without changing it. **Renderer** produces the
  page. An implementation may be any subset. [§2]
- **Timestamps** are RFC 3339 in UTC with a `Z` suffix and whole seconds:
  `2026-10-19T17:04:00Z`.
- **Hashes** are SHA-256, written as 64 lowercase hexadecimal characters.
  `<sha8>` is the first 8 of them.
- **Paths** inside the bundle are relative to the bundle directory, use `/`,
  and are stored unencoded (spaces as spaces). A path MUST NOT be empty,
  start with `/`, or contain an empty, `.` or `..` segment. [DF-5, DF-21]
- **Project-relative paths** (in provenance: `copiedFrom`, `source`) are
  relative to the directory holding `CAST.md`.
- **No absolute paths** anywhere in a bundle: not in the manifest, not in
  `CHARACTER.md`, not in the page. A path from another machine is noise to
  every other reader.

## 2. Names [DF-1 to DF-6]

A character has **one name**: its screenplay cue, uppercase. The same string
is the `CAST.md` `character:`, the bundle name (without `.dossier`), the
manifest's `character`, the `CHARACTER.md` `character:`, and the
`<CHARACTER>` part of every file name. There are no slugs.

**Canonicalization,** applied to every name read from a screenplay, typed in,
or found in `CAST.md`:

1. Remove a leading Fountain `@`. Then remove, repeatedly and in any order, a
   trailing parenthetical (`(V.O.)`, `(O.S.)`, `(CONT'D)`, …) and a trailing `^`
   (Fountain's dual-dialogue mark), trimming whitespace after each.
2. Trim; collapse every run of whitespace to one space.
3. Uppercase (Unicode default case mapping).
4. Normalize to NFC. Punctuation, digits and accents are kept.

A name that is empty after canonicalization, contains `/` or `:`, or starts
with `.` is an **error** (`E-NAME`). So is a bundle whose manifest `character`
isn't already canonical, which is to say canonicalizing changes it. A `CAST.md`
member without a dossier isn't checked. Nothing is silently substituted. A
writer MUST refuse to create a bundle whose name differs from an existing
bundle's only by case.

| Input | Canonical name |
|-------|----------------|
| `Mitch` | `MITCH` |
| `@McCowley` | `MCCOWLEY` |
| `BILLY (V.O.)` | `BILLY` |
| `BILLY (CONT'D) (O.S.)` | `BILLY` |
| `Aunt   Stanley` | `AUNT STANLEY` |
| `mccowley's wife` | `MCCOWLEY'S WIFE` |
| `CB#1` | `CB#1` |
| `josé` | `JOSÉ` (NFC) |
| `DUKE^` | `DUKE` |
| `DUKE (V.O.) ^` | `DUKE` |
| `AC/DC` | error `E-NAME` |
| `.HIDDEN` | error `E-NAME` |

## 3. Discovery [DF-7 to DF-12, DF-63]

- **`CAST.md`** is a Markdown file. Its YAML front matter, between `---` lines at
  the top, has `type: cast`, `schemaVersion: 1` and a `cast` list, and each entry
  of the list is a **member**.
- Discovery starts at `CAST.md`. A member with a dossier has a `manifest:`
  path, relative to the directory holding `CAST.md`. Nothing is found by
  scanning directories.
- The bundle is the directory `<CHARACTER>.dossier` containing that
  manifest. The manifest's `character` MUST equal the directory name without
  `.dossier`, and MUST equal the member's `character` (`E-NAME-MISMATCH`).
- **Resolving a pointer.** Split the `manifest:` value on `/`, drop empty and
  `.` segments, and let each `..` remove the segment before it, without reading
  the disk or following links. Compare the result with the bundle manifest's
  path relative to the same directory, as NFC strings, case-sensitively. A
  member **points at** a bundle when they are equal.
- **`W-POINTER`:** a member's `manifest:` doesn't lead to a manifest: its last
  segment isn't `manifest.json`, or neither that file nor its directory exists.
  Where the directory exists but the manifest is missing or unreadable, it is
  `E-MANIFEST`. A pointer that reaches a manifest is never `W-POINTER`, and any other
  fault has its own code: names that disagree are `E-NAME-MISMATCH`, a version 2
  manifest outside a `.dossier` directory is `E-NOT-BUNDLE`, and version 1 is `W-V1`.
- **Names compare exactly,** as NFC strings. `E-NAME-MISMATCH` covers the
  directory name, the manifest's `character`, the `CAST.md` member's `character`
  and `CHARACTER.md`'s `character`.
- A member with no `manifest:` has no dossier; that is valid.
- A `.dossier` directory no member points at is an **orphan** (`W-ORPHAN`):
  reported, never loaded, never deleted. A validator looks for orphans only in
  `characters/` beside `CAST.md` and in each directory holding a bundle a member
  points at, not recursively. This is the only directory listing the format
  uses. A writer's *refresh* MAY adopt an orphan whose name equals a member that
  has no `manifest:`, by setting the pointer. It never adopts on a near match.
- Everything for a character lives in its bundle: description, art style
  (§9.1), images, voice and LoRA (§8.4). No copy elsewhere is the authority.
- Where bundles go is the producing tool's setting (conventionally
  `characters/`); the format only requires that `manifest:` points there.

**`CAST.md` fields read** (the format belongs to SwiftReparto): `character`,
`role`, `manifest`, `voicePrompt`, `voices.voxalta`, `language`, `actor`.
The format writes none of them except through a `CAST.md` writer.

## 4. The bundle [DF-13 to DF-20]

```
<CHARACTER>.dossier/
  manifest.json                     the inventory (§5)
  CHARACTER.md                      the description (§9)
  <CHARACTER>-dossier.html          the page (§11)
  images/
    portrait-<sha8>.png
    face-<sha8>.png
    view-front-<sha8>.png  view-profile-<sha8>.png  view-back-<sha8>.png
    expression-<variant>-<sha8>.png
  voice/
    <CHARACTER>.vox                 vox-format; holds one or more model sizes
    sample-<variant>[-<model>].m4a  one per sample (§8.2)
    samples.yaml                    optional: the lines to render (§10)
  source/                           sourcePhoto assets
  training/                         training assets
  lora/<CHARACTER>-v<N>.safetensors lora assets
```

- **The bundle is the character's one source of truth,** read and written in
  place. It is not an export.
- **Image names.** A writer names every file it adds under `images/` as
  `<kind>[-<variant>]-<sha8>.png`. The name is derived from the content, so
  it never collides and can't claim to be something it isn't. v2 images are
  PNG. [DF-14]
- **Voice names** are the producer's: `voice/<CHARACTER>.vox`,
  `voice/sample-<variant>.m4a`; a sample on a model size other than the
  `.vox`'s default adds `-<model>` (`sample-neutral-0.6b.m4a`). [DF-15]
- **No sidecars.** A generator's sidecar is folded into the asset's
  `provenance` (§6) and stays outside the bundle. A `.json` file in `images/`
  is `W-SIDECAR`. [DF-16]
- **Candidates live outside,** in `<charactersDir>/.generations/<CHARACTER>/`.
  A file enters the bundle when it is selected or explicitly kept. Names in
  `.generations/` that aren't a character name (lowercase, e.g. `scenes`) are
  reserved for other tools. [DF-17]
- **Originals are never modified** and never embedded in the page. [DF-18]
- **One home for the character's adapter:** `lora/`. A tool that keeps
  adapters elsewhere treats the bundle's as authoritative. [DF-20]
- **Type identifier:** `io.intrusive-memory.dossier`, conforming to
  `com.apple.package`, extension `dossier` (provisional; REQUIREMENTS Q6). A
  bundle shown as a plain folder is still valid. [DF-19]
- **Other files** (any file not listed as an asset) are allowed and
  reported as unclassified (`W-UNCLASSIFIED`), except `samples.yaml`, which
  is a known file without an asset.

## 5. The manifest [DF-21 to DF-31]

`manifest.json` is UTF-8 JSON, pretty-printed with 2-space indentation and
keys sorted, ending in a newline. Schema: [`schemas/manifest-v2.schema.json`](../schemas/manifest-v2.schema.json).

### 5.1 Top level

| Key | Required | Type | Meaning |
|-----|----------|------|---------|
| `manifestVersion` | yes | `2` | The format version. A reader MUST reject an unknown version (`E-VERSION`). |
| `character` | yes | string | The canonical name (§2). |
| `role` | no | tier (§8.3) | A copy of the `CAST.md` role. `CAST.md` wins. |
| `updatedAt` | yes | timestamp | The last write. |
| `generator` | no | `{name, version?}` | The writing tool. |
| `prompts` | no | object (§5.5) | The prompts images are built from. |
| `files` | yes | array (§5.2) | The integrity layer. |
| `assets` | yes | array (§5.4), may be empty | The semantic layer. |
| `manifestChecksum` | yes | hash (§5.3) | |

Unknown top-level keys MUST be preserved by writers and MAY be ignored by
readers. [D10]

### 5.2 `files`

Every regular file in the bundle except `manifest.json`, hidden files (any
path segment starting with `.`) and symlinks. Each entry has exactly `path`,
`sha256`, `sizeBytes`. Entries are sorted by `path` (byte order of the UTF-8
string). A zero-byte file is refused: a writer MUST NOT write it and a
validator reports `E-ZERO-BYTE`.

This inventory is of the disk, not of `files`. A validator walks the bundle:
`W-UNCLASSIFIED` and `E-ZERO-BYTE` apply to a file in the inventory whether or not
`files` lists it, and neither applies to a hidden file. A file on disk that
`files` doesn't list doesn't change `manifestChecksum`, which is computed from
`files`.

**Bundle paths.** Every path recorded in a manifest (`files`, `assets`,
`derivedFrom`, `provenance.references`) is relative to the bundle, with `/` as
its only separator. It is `E-PATH` when it:

- starts with `/`, or has a `:` in its first segment (`C:/x`, `file:///x`), which
  makes it absolute;
- contains a `\`;
- has an empty, `.` or `..` segment (`images//x.png`, `../x`). An empty path is
  an empty segment.

### 5.3 `manifestChecksum`

The SHA-256 of the `files` entries' `sha256` strings, **sorted** (byte order)
and concatenated with no separator, as UTF-8. This is SwiftAcervo's
`CDNManifest.computeChecksum`.

Worked example. Two files:

| path | content | sha256 |
|------|---------|--------|
| `CHARACTER.md` | `# CHARACTER\n` (12 bytes) | `bc987259bf9c3924d17ebcd78cde56315bc965eacc7f8070184b88d35fc845c6` |
| `voice/samples.yaml` | `hello\n` (6 bytes) | `5891b5b522d5df086d0ff0b110fbd9d21bb4fc7163af34d08286a2e846f6be03` |

Sorted, `5891…` comes before `bc98…`, so the input is
`5891b5…6be03bc9872…845c6` (128 characters) and
`manifestChecksum` = `a27ac1c9afbdeb3708fd6b86b90977f80d3b01d31bc65a7acb84585c74a30980`.

(Version 1 manifests concatenate in `files` order instead; Appendix A.)

### 5.4 `assets`

A list. Each entry describes one file in `files`, and `path` is unique in the
list. An asset whose `path` has no `files` entry is `E-ASSET-NO-FILE`.

| Key | Required | Type | Meaning |
|-----|----------|------|---------|
| `path` | yes | path | The file. |
| `kind` | yes | kind (§8) | What it is. |
| `status` | yes | `selected` \| `candidate` \| `rejected` | At most one `selected` per `kind` + `variant`, and for `voiceSample` per `kind` + `variant` + `model` (`E-MULTI-SELECTED`). Selecting one demotes the previous selection of that same combination to `candidate`. Nothing is ever deleted implicitly. [DF-26] |
| `variant` | when the kind has variants | string | §8.1. |
| `label` | no | string | Display text. Never a key; never parsed. |
| `createdAt` | yes | timestamp | When the file was made (a generator's own time where known), not when it was added. |
| `provenance` | yes | object (§6) | How it was made. |
| `derivedFrom` | on derived kinds | array (§7) | Its inputs. |
| `review` | no | object | `{passed: [id], failed: [id], notes, reviewedAt}`; IDs from [`data/review.json`](../data/review.json). Advisory: never blocks selection. |
| `model` | `voiceSample` | `1.7b`, `0.6b`, … | The model size the sample was rendered with. |
| `language` | no | BCP 47 | On a `voiceSample`. Default: the character's first `languages` entry. |
| `sampleText` | `voiceSample` | string | The words spoken. |
| `lora` | `lora` | object | §8.4. |
| `training` | `training` | object | §8.4. |

Unknown asset keys MUST be preserved by writers and MAY be ignored by readers.

### 5.5 `prompts` [D3]

| Key | Type | Meaning |
|-----|------|---------|
| `identity` | string | Who the character is, visually: build, face, hair, skin, signature features and wardrobe-or-state, ending with what is absent ("no tattoos, no jewelry, no glasses"). No framing, expression, gaze or pose. Every `view` and `expression` prompt is built from it. |
| `portrait` | string | The working portrait prompt. The prompt actually sent for the selected portrait is its `provenance.prompt`. |
| `subject` | `man` \| `woman` \| `boy` \| `girl` \| `person` | The noun prompts use for the character. |

A reader's "identity prompt" is `prompts.identity`. How prompts are composed
is the generating tool's.

### 5.6 Writes [DF-29, DF-30]

Write to a temporary file in the bundle, replace `manifest.json` with it,
re-read it, and verify it parses and matches what was written. Only a
conforming writer changes `manifest.json`. Other tools MAY put files in the
bundle (a voice tool writing `voice/<CHARACTER>.vox`); they are unclassified
until a writer's *refresh* adopts them by these rules. An adopted asset has
`status: candidate`.

- `voice/<CHARACTER>.vox` → `vox`.
- `voice/sample-<name>.m4a` → `voiceSample`. If `<name>` ends in `-` followed by a
  size the selected `vox` holds (§8.3), that is the `model` and the rest is the
  `variant`. Otherwise `<name>` is the `variant`, and `model` is the first size in
  the selected `vox`'s `provenance.models`, as a lowercase size (`1.7b`).
- A sample is adopted only when there is a selected `vox`, which gives its
  `derivedFrom`, and `voice/samples.yaml` has an entry for that `variant` and
  `model` (an entry with no `model` matches any), which gives its `sampleText`.
  Otherwise the file stays unclassified and the writer reports why.

## 6. Provenance [DF-28]

`provenance` records how a file was made, well enough to make it again.
Every key except `provider` is optional; producers record what they know.
Unknown keys are preserved.

| Key | Kinds | Type | Meaning |
|-----|-------|------|---------|
| `provider` | all | string | `vinetas`, `echada`, `diga`, `personaje`, `manual`, `import`, … `import` means an existing file brought in. |
| `tool` | all | `{name, version?, binary?}` | The program actually run. `binary` is informational and MUST NOT be relied on. |
| `model` | generated | string | As the tool reports it. Not normalized. |
| `models` | `vox` | array of string | The models the `.vox` holds, as the tool reports them. |
| `prompt` | images | string | The prompt sent, before style is applied. |
| `composedPrompt` | images | string | Style and prompt as the engine received them. |
| `style` | images | string | The full style string sent. |
| `artStyle` | images | string | The character's `artStyle` (§9.1) when the image was made: the staleness key (§7). |
| `negative` | images | string | |
| `negativeApplied` | images | boolean | `false` when the engine ignored `negative`. |
| `seed`, `steps` | images | integer | |
| `guidance` | images | number | |
| `width`, `height` | images | integer | The output size in pixels. |
| `engine`, `mode` | images | string | e.g. `flux2`, `textToImage` / `imageToImage`. |
| `durationSeconds` | generated | number | |
| `loras` | images | `[{path, scale, activationKeyword}]` | `path` is a bundle path when it is this character's `lora` asset. |
| `references` | images | array (below) | Every reference image sent. |
| `round` | `portrait` | string | The prompt round (`v3`, `v3-ref`), which a content-hash file name no longer carries. |
| `box` | `face` | `{x, y, width, height}` | A hand-set **face** box (§8.5), not the crop, in source pixels, origin top-left. Absent when detected. |
| `voicePrompt` | `vox` | string | The voice-design prompt. |
| `copiedFrom` | `vox` | project-relative path | Set when an existing `.vox` was brought in unchanged. |
| `instruct` | `voiceSample` | string | The delivery instruction sent. |
| `instructApplied` | `voiceSample` | `yes` \| `no` \| `unverified` | |
| `source` | `voiceSample` | string | Where the line comes from: project-relative `file:line[-line]`, or `sampleLine`. |
| `gateOverridden` | any | string | A producing tool's process gate that was skipped. |
| `notes` | any | string | Free text. |

**`references`** [D8]: one entry per image sent, in the order sent.

| Key | Required | Meaning |
|-----|----------|---------|
| `sha256` | yes | The bytes sent. |
| `path` | when known | The bundle path of the asset with that `sha256` at the time of writing. Never an absolute path. |
| `role` | no | Why it was sent: `portrait`, `face`, `view:<variant>`, `expression:<variant>`, or a tool's own word. |
| `originalWidth`, `originalHeight`, `effectiveWidth`, `effectiveHeight` | no | As the engine reports them. |

## 7. `derivedFrom` and staleness [DF-27, DF-46, D4]

`derivedFrom` is an array of input records. Each is one of:

| Shape | Used for |
|-------|----------|
| `{"role": "<role>", "path": "<bundle path>", "sha256": "<hash>"}` | An asset in the bundle. Roles: `portrait`, `face`, `vox`, `description`. |
| `{"role": "castMember", "sha256": "<hash>"}` | The `CAST.md` member, hashed as its canonical JSON (below). |
| `{"role": "bundle", "sha256": "<hash>"}` | The `manifestChecksum` computed over every file except the page itself. |
| `{"role": "template", "version": "<v>", "sha256": "<hash>"}` | The page template. |

| Kind | `derivedFrom` MUST include |
|------|----------------------------|
| `face` | `portrait` |
| `view` | `portrait`, and `face` when it was sent |
| `expression` | `face`, `portrait` |
| `voiceSample` | `vox` |
| `dossier` | `description`, `castMember`, `bundle`, `template` |

**The hash of a member** is the SHA-256 of the canonical JSON of its normal form,
so it doesn't depend on how `CAST.md` is written, or change when a writer
normalizes the file.

**Normal form** of a member:

- A legacy `voiceDescription` is dropped. If `voicePrompt` is absent or null, its
  value first becomes `voicePrompt`.
- `voices` is always present, `{}` when the member has none. Provider keys are
  lowercased. A single string becomes a one-element array. A value that is
  neither a string nor an array of strings is dropped.
- `character`, `role`, `actor`, `gender`, `language`, `voicePrompt` and `manifest`
  are absent when their value is null.
- Every other key is kept with its value, including null.
- **Values.** `character`, `role`, `actor`, `gender`, `language`, `voicePrompt`,
  `manifest` and everything in `voices` are strings, written as their text in
  `CAST.md` (`language: no` is `"no"`). In any other key, at any depth, a plain
  (unquoted) YAML scalar is:
  - null when it is empty, `~`, or `null`, `Null` or `NULL`;
  - a boolean when it is `true`, `True`, `TRUE`, `false`, `False` or `FALSE`;
  - an integer when it matches `-?(0|[1-9][0-9]*)` and fits in a signed 64-bit
    integer;
  - otherwise a string, as written (`1.5`, `0755`, `yes`, `2026-08-01`).

  A quoted scalar is always a string. A writer that keeps these values keeps the
  hash.

**Canonical JSON:** UTF-8, with object keys sorted at every level by the byte
order of their UTF-8 form and no whitespace outside strings. Inside strings the
only escapes are `\"`, `\\`, `\b`, `\t`, `\n`, `\f` and `\r`, and for any other
character below U+0020, `\u00` and two lowercase hex digits. `/` and non-ASCII
characters are written as themselves. An integer is written in decimal.

```yaml
- character: INÉS
  voiceDescription: A low voice.
  voices: {VoxAlta: a/b.vox}
  bio: null
```

has the canonical JSON

```json
{"bio":null,"character":"INÉS","voicePrompt":"A low voice.","voices":{"voxalta":["a/b.vox"]}}
```

and the hash `bf956f8fe4278f30b800f8899b3a634ef1ac15ad101796b31e9d592fa0b73168`.

A `selected` asset is **stale** when any input's `sha256` differs from the current
selected asset of that role, read from its `files` entry (or the current member,
bundle, template), or when that role has no selected asset. A `candidate` or `rejected` asset is never reported.
The current template is defined in §11. Changing the character's `artStyle` (§9.1)
also makes its images stale: a selected image with a `provenance.artStyle` that differs from the current
front-matter `artStyle` is stale. An image with no `provenance.artStyle` isn't
compared. No other character is affected. Stale assets are
flagged (`W-STALE`), never deleted or demoted.

## 8. Kinds

### 8.1 Kinds and variants [DF-32 to DF-34]

| `kind` | `variant` | Shape | Notes |
|--------|-----------|-------|-------|
| `description` | — | `CHARACTER.md` | Always at path `CHARACTER.md`. |
| `portrait` | — | 9:16 | Head to mid-chest, three-quarter. The anchor; it *is* the three-quarter view. |
| `face` | — | square | §8.5. Stands for the neutral expression. |
| `view` | `front` \| `profile` \| `back` | 9:16 | Framed like the portrait. Profile faces screen-left. |
| `expression` | `happy` \| `sad` \| `frightened` \| `mad` | square | Framed like the face. Another variant is allowed with `W-VARIANT` (character-specific expressions come after v2). |
| `vox` | — | `.vox` | Always at `voice/<CHARACTER>.vox`. |
| `voiceSample` | `neutral`, or any register name | `.m4a` | §8.2. |
| `dossier` | — | HTML | Always at `<CHARACTER>-dossier.html`. |
| `sourcePhoto` | — | image | A real photo the character is based on. |
| `lora` | — | `.safetensors` | §8.4. |
| `training` | — | image | §8.4. |
| `crowdRef` | — | image | A reference for a background character. |

**Shapes** are width to height, in pixels as stored in the file. For each
`selected` `portrait`, `view`, `face` and `expression`, let *r* be width ÷ height
and *t* be 9 ÷ 16 or 1. It is `W-SHAPE` when |*r* − *t*| ÷ *t* is over 0.01, computed
in exact or 64-bit arithmetic, or when a file that exists has no readable
dimensions. A missing file is only `E-FILE-MISSING`. 179×320 passes and 178×320 doesn't.

**Retired kinds** (`turnaround`, `faceSheet`, `expressions`, `wardrobe`,
`palette`): a version 1 reader recognizes them; a writer MUST NOT produce
them. Wardrobe and palette are a project's scene style, not a character's.

**The lookup.** "The selected asset for (kind, variant)" is the asset with
that `kind`, that `variant` (or no `variant`, when none is asked for) and
`status: selected`. Readers find assets this way, never by file name.

### 8.2 Voice [DF-38, D5]

- **Which voice to play** is `CAST.md` `voices.voxalta`: every audio tool
  reads it; its paths are relative to the directory holding `CAST.md`. **What's
  in the bundle** is the manifest. When the member's
  `voices.voxalta` has no entry that resolves as in §3 to the bundle's selected
  `vox`, the validator
  reports `W-VOICE-ELSEWHERE`; when `voicePrompt` differs from the selected
  vox's `provenance.voicePrompt`, `W-VOICE-PROMPT`.
- The sizes a `.vox` holds are in `provenance.models`; the file itself
  (vox-format) is authoritative.
- **Samples:** a `neutral` read for each model size the tier requires, plus
  three or more range samples from the character's own lines. Range variants
  are any names except `neutral`. Each sample records `model` and `sampleText`,
  and `language` when it isn't the default (§5.4).

### 8.3 Tiers [DF-35 to DF-37]

Tiers: `lead`, `supporting`, `guest`, `narrator`, `costar`, `underfive`,
`background`. **Major** tiers: `lead`, `supporting`, `guest`, `narrator`.

What each tier needs is [`data/tiers.json`](../data/tiers.json). Each row is
either an **asset** row (a selected asset of a kind, optionally a count of
variants) or a **check** row (a named test, defined below). Each cell is
`required`, `recommended` or `none`. **Complete** means every `required` row
for the tier is satisfied. Implementations read the table; they don't
restate it.

A character's tier is its `CAST.md` member's `role`. The manifest's `role` is only
a copy and doesn't supply one: a member with no `role` is `W-ROLE`, and its
completeness isn't defined.

| Check ID | Satisfied when |
|----------|----------------|
| `description.full` | `CHARACTER.md` is selected and has every full section (§9.2). |
| `description.short` | `CHARACTER.md` is selected and has Logline, Appearance, Voice & Speech. |
| `voicePrompt` | The `CAST.md` member has a non-empty `voicePrompt`. |
| `vox.1.7b`, `vox.0.6b` | The selected `vox` holds that size: an entry of its `provenance.models` contains the size, compared case-insensitively (`Qwen3-TTS-12Hz-1.7B-Base-bf16` holds `1.7b`). |
| `sample.neutral.1.7b`, `sample.neutral.0.6b` | A selected `voiceSample` with variant `neutral` and that `model`. |
| `sample.range` | Three or more selected `voiceSample`s with variants other than `neutral`. |
| `pronunciation` | `CHARACTER.md` has a non-empty Pronunciation section. |
| `training.withLora` | When a `lora` is selected, at least one `training` asset exists. |

### 8.4 LoRA and training [D7]

`lora` assets live at `lora/<CHARACTER>-v<N>.safetensors`; the selected one
is the character's adapter. Its `lora` object:

| Key | Type |
|-----|------|
| `triggerWord` | string. Authoritative for this character; a tool's own default (such as a slug) does not apply to a character with a dossier. |
| `baseModel` | string |
| `version` | integer `N` |
| `rank`, `steps` | integer |
| `defaultScale` | number |
| `trainedAt` | timestamp |
| `compatibleEngines` | array of string |

`training` assets carry `training: {caption, view, isSynthetic}`.

### 8.5 The face crop [DF-41]

A square centred on the largest detected face in the selected portrait, never
upscaled, saved as PNG. A hand-set face box replaces the detected one and is
recorded as `provenance.box`. How a face is detected is the implementation's.

For a face box `(x, y, w, h)` in an image `W` × `H`, origin top-left, with
values rounded half away from zero:

1. `side` = round(min(1.8 × max(w, h), W, H))
2. `left` = round(min(max(x + w/2 − side/2, 0), W − side))
3. `top` = round(min(max(y + h/2 − side/2, 0), H − side))

A crop that would pass an edge moves inward; it shrinks only when it is larger
than the image.

Worked example. Face box `(50, 60, 80, 100)` in a 180 × 320 portrait:
`side` = min(180, 180, 320) = 180, `left` = min(max(0, 0), 0) = 0,
`top` = min(max(20, 0), 140) = 20. The crop is 180 × 180 at (0, 20).

## 9. CHARACTER.md [DF-39, DF-40, D9]

UTF-8 Markdown with YAML front matter.

### 9.1 Front matter

| Key | Required | Type | Meaning |
|-----|----------|------|---------|
| `type` | yes | `character` | |
| `character` | yes | string | The canonical name. |
| `role` | no | tier | A copy; `CAST.md` wins. |
| `aliases` | no | array of string | Other names the script uses. |
| `age` | no | string | Free text: `39`, `late 20s`, `unknown`. |
| `pronouns` | no | string | |
| `occupation` | no | string | |
| `languages` | no | array of BCP 47 | First is primary. |
| `artStyle` | no | string | The character's art style, sent with every image prompt for this character. A producing tool starts a new character with the project default; a character may differ from the rest of the cast (Personaje APP-UI UD20). |
| `sampleLine` | no | string | One of the character's own lines, word for word: the neutral sample's text. |
| `draft` | no | object | `generatedBy`, `generatedAt` (timestamp or date string), `sources` (array), `reviewedAt` (date string), `generated` (array of section names or front-matter keys still as generated; a writer removes an entry when a person edits it). |

Dates in front matter are quoted strings. Unknown keys are preserved, and a
writer preserves the text of keys it doesn't change. **No data lives in
YAML comments;** comments may be lost by any writer.

### 9.2 Body

`##` sections, in this order:

1. Logline
2. Appearance
3. Personality
4. Backstory
5. Arc
6. Relationships
7. Voice & Speech
8. Pronunciation
9. Wardrobe
10. Canon & Guardrails
11. Open Questions

A heading matches a section by its name, optionally followed by a space and
a parenthetical (`## Arc (Season 1)`). **Full** (major tiers) has 1–9;
**short** (`costar`, `underfive`) has Logline, Appearance, and Voice &
Speech. Canon & Guardrails and Open Questions are optional in both.

**Open Questions** uses `###` groups. The standard groups are
`Needed before Portrait / Views`, `Needed for Voice`, `Optional` and
`Deferred`; others are allowed. A producing tool MAY gate image generation
on the first being empty.

**Other characters** are named by their exact canonical name, and SHOULD be
in bold (`**SHANE**`) so a reader can find them. They are plain text, never
links (§11).

### 9.3 Footnotes and claims

Every claim about the character SHOULD be footnoted. A footnote is
`[^<label>]` in the text and `[^<label>]: <class>. <text>` at the end, with
`<class>` one of:

- **Stated.** The script or bible says it; cite `file:line`.
- **Inferred.** Reasoned from the material; give the reasoning.
- **Author.** The author said so; give the date.

Every reference MUST have a definition and every definition MUST be
referenced (`W-FOOTNOTE`). Labels are free; `e<episode>-<line>`,
`pm-<line>`, `inf-<slug>`, `a-<slug>` are the recommended conventions.

## 10. `samples.yaml` [D6]

Optional. The lines a voice tool renders as samples, and why each was
chosen. A YAML list; schema [`schemas/samples.schema.json`](../schemas/samples.schema.json).

| Key | Required | Meaning |
|-----|----------|---------|
| `variant` | yes | The sample's variant (§8.2). |
| `text` | yes | The words, exactly as spoken. |
| `model` | no | Model size; default the `.vox`'s default. |
| `language` | no | BCP 47; default the character's primary language. |
| `instruct` | no | Delivery instruction. |
| `source` | no | Project-relative `file:line[-line]`, or `sampleLine`. |

It is a known file without an asset entry.

## 11. The dossier page [DF-42 to DF-53]

`<CHARACTER>-dossier.html` is the only HTML file in the bundle and is
registered as `kind: dossier`.

- **Self-contained.** Styles, scripts, fonts, images and samples are
  embedded as `data:` URIs or inline. No network request, no reference to
  another file.
- **Page copies, not originals:** portrait and views as JPEG 720×1280, face
  and expressions as JPEG 512×512, quality 80. Samples and subset fonts as
  they are. Copies are not stored.
- **The record** is embedded as
  `<script type="application/json" id="character-record">`, matching
  [`schemas/record.schema.json`](../schemas/record.schema.json):
  `{formatVersion, character, castMember, frontMatter, body, manifest}`.
  Every `<` in the JSON is written `\u003c`, so the text can't close the script.
- **The embedded manifest is the manifest without the page,** since a file
  can't contain its own hash: no `files` or `assets` entry for the page, and
  `manifestChecksum` computed over the remaining files, which is the value of
  the page's `bundle` input (§7). Its `updatedAt` is the latest `createdAt` of
  its assets, not the last write, so rendering twice gives the same bytes. It
  otherwise matches `manifest.json`.
- **Template:** `<meta name="dossier-template" content="<version> <sha256>">`,
  with the same values as the page's `template` input (§7). The **current
  template** is the one the validator or renderer carries, by the version and
  `sha256` published with it. The page is stale (`W-STALE`) when the `sha256` in
  either place differs from the current template's; versions aren't ordered, so
  an older template is stale too. A validator that carries no template makes no
  template comparison.
- **Stable output:** the same inputs and template give the same bytes, per
  implementation. A renderer MUST NOT write the render time.
- **Content:** only `selected` assets; missing required rows listed by name;
  an integrity banner for errors and stale selections; a provenance line per
  tab; the footnotes as a sources list in citation order. Other characters
  are plain text. The tabs and fields are `data/fields.json` (to be written
  with the template; REQUIREMENTS §13).
- A complete lead's page should be about 3 MB; over 10,000,000 bytes is
  `W-PAGE-SIZE`.

**`W-PAGE-EXTERNAL`.** A validator reads the page as HTML. Comments, text and the
contents of `<script>` elements are not searched. The page's references are:

- the attributes `src`, `srcset` (each candidate, parsed as HTML parses it, so a
  comma inside a `data:` URI doesn't split one), `href`, `xlink:href`, `poster`,
  `data`, `action`, `formaction` and `background`, on any element;
- every `url(...)` and `@import` in `<style>` elements and `style` attributes.

A reference is allowed when, after trimming whitespace, it is empty, starts with
`#`, or starts with `data:` (in any case). So is the `href` of an `<a>` element
with the scheme `http`, `https` or `mailto`: nothing loads unless the reader
follows it, and a source can be cited by its address. Anything else is
`W-PAGE-EXTERNAL`, including a relative `<a href>`. A script that makes a request
can't be detected this way, and is still forbidden.

## 12. Hosting [DF-58 to DF-63]

A host (a project browser, a scene tool's cast view) presents a `.dossier`
as one item, finds the page and the face through a reader's lookup (§8.1),
shows the page read-only with the bundle as its base, and shows the
validator's finding in place of the page when there is one. It never edits,
repairs or deletes a bundle, and a bundle found on disk is not a cast member
unless `CAST.md` says so.

## 13. Identity across tools

**A file's identity is its SHA-256.** File names change when content changes
(§4), so a tool that records which dossier files it used (a storyboard panel
recording its references) records their `sha256`, and finds them again by
`sha256` through the manifest.

## 14. Validation [DF-54 to DF-57]

A validator never changes anything. Each finding has a stable code. A fault
that a specific code below names may also break the schema; the specific code
MUST be reported and `E-SCHEMA` MAY be reported with it.

| Code | Level | Finding |
|------|-------|---------|
| `E-VERSION` | error | Unknown `manifestVersion` |
| `E-NAME` | error | Name invalid (§2) |
| `E-NAME-MISMATCH` | error | Bundle name, manifest `character`, `CAST.md` member and `CHARACTER.md` disagree (§3) |
| `E-CAST` | error | `CAST.md` can't be read: its YAML doesn't parse, or a member has no `character`, a `role` that isn't a tier (§8.3), a `gender` other than `M`, `F`, `NB` or `NS`, or a `voices` that isn't a map. No other check is possible. |
| `E-MANIFEST` | error | A directory a member points at has no `manifest.json`, or it isn't a JSON object. No other check of that bundle is possible. |
| `E-NOT-BUNDLE` | error | A version 2 manifest in a directory without `.dossier` |
| `E-PATH` | error | A path in the manifest breaks §5.2's rules |
| `E-FILE-MISSING` | error | A `files` entry has no file |
| `E-FILE-HASH` | error | A file's hash or size doesn't match its entry |
| `E-ZERO-BYTE` | error | A zero-byte file |
| `E-CHECKSUM` | error | `manifestChecksum` doesn't match |
| `E-ASSET-NO-FILE` | error | An asset with no `files` entry |
| `E-ASSET-DUPLICATE` | error | Two assets with the same `path` |
| `E-MULTI-SELECTED` | error | More than one `selected` for a `kind` + `variant` (`voiceSample`: + `model`) |
| `E-KIND-RETIRED` | error | A retired kind in a version 2 manifest |
| `E-SCHEMA` | error | The manifest fails its schema |
| `W-UNCLASSIFIED` | warning | A file with no asset entry |
| `W-STALE` | warning | A derived asset's inputs changed |
| `W-SHAPE` | warning | Wrong aspect ratio for the kind (§8.1) |
| `W-VARIANT` | warning | An `expression` or `view` variant outside the standard set |
| `W-SIDECAR` | warning | A `.json` sidecar in `images/` |
| `W-ORPHAN` | warning | No `CAST.md` member points at the bundle |
| `W-POINTER` | warning | The member's `manifest:` doesn't point at this bundle (§3) |
| `W-ROLE` | warning | A member with a `manifest:` has no `role` |
| `W-VOICE-ELSEWHERE` | warning | `voices.voxalta` doesn't name the selected `vox` |
| `W-VOICE-PROMPT` | warning | `voicePrompt` differs from the vox's |
| `W-FOOTNOTE` | warning | An undefined or unused footnote |
| `W-PAGE-SIZE` | warning | The page is over 10,000,000 bytes |
| `W-PAGE-EXTERNAL` | warning | The page references something outside itself (§11) |
| `W-INCOMPLETE` | warning | A required tier row is missing (listed by row ID) |
| `W-V1` | warning | A version 1 manifest (readable; migrate it) |

**Report:** the findings, and completeness against the tier: every row with
its state.

## 15. Versions

The format version is `manifestVersion`. A change that makes a valid bundle
invalid is a new version. The template is versioned separately. Changes are
listed in `CHANGELOG.md`.

---

## Appendix A. Version 1 [D2]

A reader MAY read version 1; a writer MUST NOT write it. Two shapes exist:

1. **Version 1 as specified** (SwiftSemblanzas §5): `characters/<CHARACTER>/`,
   `dossier.html`.
2. **Version 1 contents in a `.dossier` directory** (the shape of every
   bundle produced by Personaje's pilot tools as of 2026-10-07): a v1
   manifest, v1 kinds, sidecars and free-form names, inside
   `<CHARACTER>.dossier/`. Valid as version 1, reported `W-V1`.

Schema: [`schemas/manifest-v1.schema.json`](../schemas/manifest-v1.schema.json).
A validator reports `W-V1` and doesn't apply what only version 2 requires: the
differences below, completeness and staleness.
Differences from version 2:

| Version 1 | Version 2 |
|-----------|-----------|
| `manifestChecksum` concatenates `sha256` strings in `files` (path) order | sorted by hash (§5.3) |
| Kinds `turnaround`, `faceSheet`, `expressions`, `wardrobe`, `palette` | `view`, `face`, `expression`; the last two removed |
| View and expression variant in `label` (`front`, `happy`) | in `variant` |
| `derivedFrom` a path string (samples) or an object `{CHARACTER.md, castMember, assetsChecksum}` (page) | an array (§7) |
| `provenance.references` absent, or path strings | `[{sha256, path, role}]` |
| `provenance.tool` a string | an object |
| Candidates and their sidecars inside `images/` | in `.generations/` |
| Free-form image names (`portrait-v3-photo-s133.png`, `face.png`, `view-front-s21.png`) | `<kind>[-<variant>]-<sha8>.png` |
| `dossier.html`, relative links | `<CHARACTER>-dossier.html`, self-contained |
| `createdAt` sometimes absent | required |

**Migration** is an implementation's tool. So that every migrator produces the
same bundle, it takes these steps, in this order:

1. Rename `<CHARACTER>/` to `<CHARACTER>.dossier/` if needed.
2. Fold each sidecar into its asset's provenance, mapping `references[].source`
   to bundle paths by `sha256` and dropping the absolute path. Record the round
   and seed from the old file name in `provenance.round` and `provenance.seed`.
3. Move candidates and sidecars to `.generations/<CHARACTER>/`.
4. Map retired kinds: `turnaround` + `label` → `view` + `variant`, `expressions`
   + `label` → `expression` + `variant`, `faceSheet` → `face`.
5. Rename selected images to content names.
6. Rewrite `derivedFrom` in the §7 shape.
7. Update `CAST.md` pointers through its writer.
8. Write the version 2 manifest.
9. Render the new page, which hashes the manifest's files, and delete
   `dossier.html`.
10. Validate.

**An asset step 4 can't map** is a `turnaround` or `expressions` with no `label`,
or a `wardrobe` or `palette`, which have no version 2 kind. The migrator MUST NOT
guess: it drops the asset entry, leaves the file where it is under its old name,
and reports it. The file stays in `files` and is `W-UNCLASSIFIED`.
