---
type: doc
state: draft
updated: 2026-10-19
---

# Property inventory

Every property the `.dossier` bundle has, or that some tool needs it to have,
collected from the five places the format is described and from the tools that
read and write it. This is the input to `docs/DOSSIER-FORMAT.md`: nothing goes
into the specification that isn't accounted for here, and nothing here is
dropped without a decision.

## Sources

| Key | Source | What it is |
|-----|--------|------------|
| **DF** | `REQUIREMENTS.md` (this repo, `development`) | The intended standard, DF-1 to DF-63 |
| **B** | Personaje `docs/REQUIREMENTS-DOSSIER-BUNDLE.md` | The draft DF was split from |
| **S** | SwiftSemblanzas `REQUIREMENTS.md` §5, worktree branch `requirements/personaje` (`739720b`, unpushed) | Version 1 of the record. Not on SwiftSemblanzas `main`. |
| **SD** | SwiftDossier `REQUIREMENTS.md` §7 (draft, 2026-10-19) | Proposed additions FA-1 to FA-3 |
| **CC** | Personaje `docs/CHARACTER_CREATION.md`, `RUNBOOK.md`, `REQUIREMENTS.md`, `REQUIREMENTS-APP-UI.md` | The process: what each step records |
| **G** | Granville's nine bundles (`podcasts/granville/characters/*.dossier`) and CAST.md | What actually exists |
| **T** | Personaje `tools/*.py`, `face_crop.swift` | What the pilot tools write and read |

**Consumers** (who reads or writes bundle data): Personaje app and CLI
(writer); SwiftDossier (writer, reader, validator, renderer); Vinetas app
(reader, `DossierCore`); SwiftVinetas (provenance producer); storyboard-flipbook
skill (reader); SwiftEchada (puts `.vox` and samples in the bundle; EC-23 to
EC-30, spec only); SwiftSemblanzas (`lora`, `training`; spec only);
SwiftReparto (CAST.md; 0.2.0 spec only); SwiftProyecto ProjectBrowser (host);
Produciesta and diga (voices, through CAST.md only); SwiftCompartido (cast
discovery, names).

Status column: **in DF** = DF covers it as is · **gap** = needed, DF silent ·
**conflict** = sources disagree · **drop?** = present somewhere, proposed to
remove. "→" is the proposed resolution, for review.

---

## 1. Names and layout

| Property | Values | Sources | Readers / writers | Status → proposal |
|----------|--------|---------|-------------------|-------------------|
| Canonical name | uppercase cue, NFC, spaces kept, no slugs | DF-1–6; S; Reparto RQ-22 | all | **conflict:** SwiftCompartido cuts at `(` and strips `^` but not `@`, no NFC; Reparto's merge key lowercases; SwiftVinetas engine uses `sks_<slug>`. → DF-2 stands; record the others as non-conforming. |
| Bundle directory | `<C>.dossier/` | DF-8; B; G (all 9) | all | **conflict:** S, CC, EC-23, Semblanzas, flipbook docs say `characters/<C>/`; Reparto RQ-21 checks `…/<character>/manifest.json`. → DF-8; Reparto drops RQ-21 (Personaje OQ-3). |
| Parent directory | `charactersDir` (default `characters`) | S; PROJECT.md `personaje.charactersDir`; EC-23 | Personaje, Echada | in DF as convention only → keep it out of the format (discovery is via `manifest:`). |
| Discovery | CAST.md `manifest:`, relative to CAST.md | DF-7; S; G (9 members) | all readers | in DF. |
| Orphans, adoption | report; exact-name adoption only | DF-10, DF-11; SD-11 | validator, `refresh` | in DF. |
| Page file | `<C>-dossier.html` | DF; B | Vinetas, ProjectBrowser, cast pages | **conflict:** G and T use `dossier.html`; ProjectBrowser README too. → DF; hosts find it through the manifest (DF-59); migration renames. |
| Image file names | `images/<kind>[-<variant>]-<sha8>.png` | DF-14; B; SD-6 | writer | **conflict:** G uses meaningful names (`portrait-v3-photo-s133`, `view-front-s21`, `face.png`); T derives labels from the name. → DF-14; the seed, round and variant move into fields (`variant`, `provenance.seed`, `provenance.round`) before renaming. Also define: extension list (`png` only in v2?), `<sha8>` lowercase hex. |
| Voice file names | `voice/<C>.vox`, `voice/sample-<variant>.m4a` | DF-15; G; EC-24, EC-28 | Echada, diga | in DF. **gap:** sample names carry neither model size nor language (see §5). |
| `samples.yaml` | `voice/samples.yaml` | DF-38 (named only); B; G (SHANE only) | Personaje `samples` | **gap:** no schema, no owner, no asset kind; EC-28 doesn't use it (takes `sampleLine`, returns `sampleText`). → decision D6. |
| `source/ references/ training/ lora/` | Semblanzas folders | S; DF-20 (`lora/` only) | Semblanzas, Vinetas (`lora`) | **gap:** naming inside them; DF-14 covers `images/` only. → `lora/<C>-v<N>.safetensors` (S, Vinetas); training names free, listed by asset. |
| Sidecar `.json` | forbidden in the bundle | DF-16; B; SD-7 | — | **conflict:** G has 67 sidecars in `images/`; SwiftVinetas always writes one. → DF-16; `add` and `migrate` fold them in (§4). |
| Candidates | `<charactersDir>/.generations/<C>/` | DF-17; B; G | Personaje, flipbook (`.generations/scenes/`) | in DF. Note flipbook also uses `.generations/scenes/`, which would collide with a character named SCENES. → reserve lowercase names in `.generations/` for non-character use. |
| Type identifier | `io.intrusive-memory.dossier`, conforms to `com.apple.package` | B; DF-19, Q6 | ProjectBrowser (uses the extension today) | open (DF Q6). |
| Hidden files | excluded from `files` | DF-21; S; T | writer | in DF (`.DS_Store` present in G, correctly excluded). |

## 2. Manifest, top level

| Property | Type | Sources | Readers / writers | Status → proposal |
|----------|------|---------|-------------------|-------------------|
| `manifestVersion` | int, required | DF-25; G (all `1`) | all | in DF. All nine G bundles are v1: a v2-only reader rejects them until migrated. |
| `character` | string, required | DF-24; G | all | in DF. |
| `role` | tier, optional; CAST.md wins | DF-24; S; G (4/9) | renderer, Vinetas | in DF. |
| `updatedAt` | timestamp, required | DF-24; G | — | **gap:** format. → RFC 3339, UTC, `Z`, whole seconds (what T writes). Same rule for every timestamp. |
| `generator` | `{name, version}` | DF-24; G | renderer footer | in DF. |
| `files` | array | DF-21; G | all | in DF. |
| `assets` | **list** of objects | DF-23 ("keyed by path"); G (list); flipbook reads `assets[].path` | all | **gap:** list or map never stated. → a list; `path` unique within it. |
| `manifestChecksum` | sha256 hex | DF-22; G | validator | **gap:** hex case, separator. → lowercase hex, sorted by path, concatenated with no separator (what T does); a worked example in the spec. |
| `prompts` | `{identity, portrait, subject}` | SD FA-1; Vinetas `identityPrompt`; B (`identityPrompt`) | Personaje (writes), Vinetas (reads `identity`) | **gap.** → add (decided 2026-10-19: prompts live in the manifest). See D3 for shape. |
| Write rules | atomic, sorted keys, pretty, verified | DF-29; S; SD-5 | writer | in DF. |

## 3. `files[]`

| Property | Sources | Status |
|----------|---------|--------|
| exactly `path`, `sha256`, `sizeBytes` | DF-21; S; G (178 entries) | in DF |
| sorted by path; zero-byte refused; leading `/` stripped; `.`/`..`/empty segments rejected | DF-21; S | in DF |
| excluded: `manifest.json`, hidden files, symlinks, non-regular files | DF-21; S; T | in DF |

## 4. `assets[]`

### 4.1 Fields on every asset

| Field | Type | Sources | Status → proposal |
|-------|------|---------|-------------------|
| `path` | string, unique | DF-23; G | in DF |
| `kind` | enum (§6) | DF; G | in DF (G uses retired kinds; §6) |
| `status` | `selected`, `candidate`, `rejected` | DF-26; G (selected, candidate) | in DF. G keeps 16 non-selected portraits as `candidate` inside the bundle, which DF-17 and B Q4 forbid for new work. → migration moves them to `.generations/`. |
| `variant` | string | DF; G (voiceSample only) | in DF. **gap:** T never writes `variant` on images; G stores view/expression variant in `label`. → required on `view`, `expression`, `voiceSample`; vocabularies in §6. |
| `label` | string | DF; G (free text) | in DF (display only, never a key). |
| `createdAt` | timestamp | DF (listed); G (35/36, not ARCHER's description) | **gap:** required or not. → required; from the generator's own time where known (sidecar `generatedAt`). |
| `provenance` | object (§4.2) | DF-28 | gap in content (§4.2) |
| `review` | object | DF (named); S (`{passed:[ids], notes}`); G (ARCHER vox only); CC, APP (checklists without IDs) | **gap:** shape. → `{passed: [id], failed: [id], notes, reviewedAt}`, with checklist IDs defined per kind in a data file (`data/review.json`). |
| `derivedFrom` | — | DF-27 ("sha256 of every input"); S and CC (a path string); G voiceSample (path string), dossier (object `{CHARACTER.md, castMember, assetsChecksum}`) | **conflict.** → decision D4. |
| `sampleText` | string | DF; G; EC-28 | in DF (voiceSample) |
| `lora` | object | DF (named); S `{triggerWord, rank, steps, defaultScale, baseModel}`; Semblanzas SwiftData adds `checksum, version, compatibleEngines, trainedAt`; SwiftVinetas `LoRAMetadata{path, scale, version, trainedAt, trainingSteps, compatibleEngines}` | **gap.** → `{triggerWord, baseModel, rank, steps, defaultScale, version, trainedAt, compatibleEngines}`. `triggerWord` decision D7. |
| `training` fields | `caption`, `view`, `isSynthetic` per image | Semblanzas `TrainingImage` | **gap** → add to the `training` kind. |
| Extension fields | — | G has hand-written keys no doc defines | **gap.** → unknown asset and provenance keys MUST be preserved by writers and MAY be ignored by readers (mirrors DF-40 for CHARACTER.md). |

### 4.2 `provenance`

DF-28 has five keys. Everything below is written by some producer today or
required by a step ("enough to recreate it exactly", CC 4.4).

| Key | Kinds | Producer | Sources | Status → proposal |
|-----|-------|----------|---------|-------------------|
| `provider` | all | all (`vinetas`, `echada`, `diga`, `personaje`, `manual`, `import`) | DF-28; G | in DF. Define the vocabulary as open, with `import` reserved. |
| `model` | all generated | SwiftVinetas, diga | DF-28; G (`klein4b`, `flux2-klein-4b`, `1.7b`) | in DF. **conflict:** two spellings for the same model in G. → record what the tool reports; no normalization in the format. |
| `models` | vox | echada | G (Qwen3 repo ids) | gap → add for `vox` (the sizes the file holds). |
| `prompt` | images, vox (`voicePrompt`) | all | DF-28; G | in DF (the text actually sent, before style). |
| `composedPrompt` | images | SwiftVinetas | G (42 sidecars) | gap → add (style + prompt as the engine received it). |
| `style` | images | SwiftVinetas, `--style` | G | gap → add (the full string sent). Staleness uses `artStyle` (below). |
| `artStyle` | images | Personaje | UD20 | gap → add: the character's art style at generation; changing the character's `artStyle` makes the image stale. |
| `negative`, `negativeApplied` | images | SwiftVinetas `PanelMetadata`; G (ARCHER, by hand) | — | gap → add both; FLUX ignores the negative, so `negativeApplied` is what tells a reader. |
| `seed`, `steps`, `guidance`, `width`, `height` | images | SwiftVinetas | G; CC 4.4 | `seed` in DF; others gap → add. |
| `engine`, `mode` | images | SwiftVinetas (`flux2`, `imageToImage`) | G | gap → add. |
| `durationSeconds` | generated | SwiftVinetas | G (`0` in old portraits) | gap → optional. |
| `generatedAt` | generated | SwiftVinetas | G sidecars | → becomes the asset's `createdAt`; not repeated in provenance. |
| `loras` | images | SwiftVinetas `[{path, scale, activationKeyword}]` | G (empty lists) | gap → add; `path` mapped to a bundle path when it's the character's own `lora`. |
| `references` | images | SwiftVinetas `[{source, sha256, originalWidth, originalHeight, effectiveWidth, effectiveHeight}]` | DF-28 `{path, sha256}`; S (path strings); G sidecars | **conflict** on shape, and G's `source` is an **absolute machine path** (the App Group staging copy). → `[{path, sha256, role, originalWidth?, …}]`: `path` is the bundle path of the asset with that sha256, never an absolute path; `role` is decision D8. |
| `round` | portrait | Personaje | G (in file names only: `v3`, `ref`) | gap → optional; keeps the information the sha8 rename would lose. |
| `tool` | all generated | Personaje, echada, diga | G (string); SD FA-2 (object) | **conflict** → object `{name, version, binary?}`; `binary` optional and never required (machine paths). |
| `copiedFrom` | vox (adopted) | Personaje `voice adopt` | G (5/9); SD FA-3 | gap → add; project-relative path. |
| `voicePrompt` | vox | echada | G (7/7) | gap → add. CAST.md `voicePrompt` must equal it (validation warning, §9). |
| `instruct`, `instructApplied` | voiceSample | diga | G (8/12, `unverified`) | gap → add; `instructApplied`: `yes`, `no`, `unverified`. |
| `source` | voiceSample | Personaje | G (`file:line` or `sampleLine (front matter)`) | gap → add (project-relative `file:line`, or `sampleLine`). |
| `notes` | any | hand | G | gap → add (free text). |
| `box` | face | Personaje, SwiftDossier | DF-41 ("recorded in provenance", no key) | gap → `{x, y, width, height}` in source-image pixels, origin top-left. |
| `derivedFrom` inputs for `dossier` | dossier | renderer | DF-46 | see D4. |
| `gateOverridden` | any | Personaje `--force` | SwiftPersonaje spec | gap → optional. |
| Audition history, review answers | vox, description | Personaje | CC 8.3, 2b.4 | → not in the manifest; auditions stay in `.generations/`. |

## 5. Voice

| Property | Sources | Consumers | Status → proposal |
|----------|---------|-----------|-------------------|
| `.vox` holds 1.7B and 0.6B | S tier table (two rows); T reads zip entries `embeddings/qwen3-tts/<size>/clone-prompt.bin` | renderer, Personaje | **gap:** how a reader knows the sizes without opening the zip. → `provenance.models` (§4.2); the zip is authoritative, vox-format owns it. |
| Neutral sample on each model size | DF-38; G `neutral`, `neutral-0.6b` | renderer, Personaje | **gap:** encoding. → a `model` field on `voiceSample` (`1.7b`, `0.6b`); variant stays `neutral`; file name `sample-neutral-0.6b.m4a` kept as the convention for the non-default size. |
| Language of a sample | CHARACTER.md `languages`; CAST.md `language`; G `sample-spanish` | Produciesta, Personaje | **gap** → a `language` field (BCP 47) on `voiceSample`, default the character's first language. |
| Range variants | DF-38 (any ≥3); EC-28 (`neutral|angry|quiet|joyful`); G (`guarded`, `open`, `building`, `easy`, …) | Echada, renderer | **conflict:** EC-28's fixed list. → DF-38; EC-28 accepts any name. |
| Which voice is authoritative | EC-25: CAST.md `voices.voxalta`; DF-30: the manifest inventories; G: CLARK, HUNTER point outside the bundle | Produciesta, diga, skills (CAST.md); renderer (manifest) | **conflict.** → decision D5. |

## 6. Kinds, variants, shapes

| Kind | Variants | Shape | Derived from | Status |
|------|----------|-------|--------------|--------|
| `description` | `full`, `short`? | CHARACTER.md | — | **gap:** full and short share a kind; the tier table needs to tell them apart. → no variant; "full" vs "short" is a property of the sections present (DF-39). |
| `portrait` | — | 9:16, ¾, head to mid-chest; adults shirtless, standard pose (decided 2026-10-19) | anchor | in DF; the pose standard is Personaje's, not the format's. |
| `face` | — | square; DF-41 crop | portrait | in DF; tier row open (DF Q3). |
| `view` | `front`, `profile`, `back` | 9:16 | portrait, face | **conflict:** SwiftVinetas engine store and vinetas-cli use `front/left/right/back` by filename. → DF-32; the engine store is outside the format. |
| `expression` | `happy`, `sad`, `frightened`, `mad` | square | face, portrait | in DF. Open: is another variant an error or a warning? → warning (character-specific expressions after 1.0). |
| `vox` | — | `.vox` | — | in DF. |
| `voiceSample` | `neutral` or a register name | `.m4a` | vox | in DF; add `model`, `language` (§5). |
| `dossier` | — | the page | D4 | in DF. |
| `sourcePhoto`, `lora`, `training`, `crowdRef` | — | — | — | "unchanged from v1" → write them out (no reference to v1 text). |
| retired: `turnaround`, `faceSheet`, `expressions`, `wardrobe`, `palette` | — | — | — | DF-34. G has 48 assets of retired kinds; T still writes them. Migration maps `turnaround`+label → `view`+variant, `expressions`+label → `expression`+variant, `faceSheet` → `face`. |

## 7. Tiers (`data/tiers.json`)

The v1 table (S §5.4) with DF-37's changes. Rows that aren't asset kinds are
the problem: DF-36 says the table is checked against selected assets, but four
rows aren't assets.

| Row | Kind or check | Status → proposal |
|-----|---------------|-------------------|
| CHARACTER.md full / short | `description` + sections present | → a **check** row (`description.full`, `description.short`) |
| Portrait | `portrait` | asset row |
| View set | `view` front, profile, back | asset row (replaces turnaround) |
| Face | `face` | open (DF Q3) → required wherever portrait is |
| Expressions | `expression` × 4 | asset row; lead ✅, supporting/guest ◐ |
| Source photo, LoRA, training, crowd ref | kinds | asset rows (training required when `lora` is) → a `requires` column |
| Voice prompt | CAST.md `voicePrompt` | → a **check** row, not an asset |
| `.vox` 1.7B, 0.6B | one `vox` asset, two sizes | → **check** rows against `provenance.models` |
| Neutral sample (per size), range ≥ 3 | `voiceSample` | → check rows with counts; underfive: neutral on 1.7B only (fixes the 0.6B contradiction) |
| Pronunciation | CHARACTER.md section | → **check** row |
| Dossier | `dossier` | asset row |

→ `tiers.json` rows have a `type` (`asset` or `check`) and a stable ID; a
validator implements each check ID as the spec defines it.

## 8. CHARACTER.md

| Property | Sources | Consumers | Status → proposal |
|----------|---------|-----------|-------------------|
| Front matter `type`, `character`, `role`, `age`, `pronouns`, `occupation` | DF-39; S; G | renderer, Vinetas, cast page | in DF. **gap:** `age` is int or string in G (`39`, `late 20s`, `unknown`). → string. `role: unconfirmed` in G (5/9). → CAST.md wins; front-matter `role` is a copy, may be absent. |
| `aliases` (list), `languages` (list, BCP 47), `sampleLine` | CC; G (9/9) | Personaje, renderer, EC-28 (`sampleLine`) | **gap** → add. |
| `draft: {generatedBy, generatedAt, sources[], reviewedAt}` | CC; G (9/9; `reviewedAt` 4/9) | Personaje gates | **gap** → add as optional; dates as quoted strings (G writes unquoted YAML dates). |
| `artStyle` | Vinetas integration (:64); Personaje APP-UI UD20 (2026-10-18) | Vinetas, Personaje | *Decided by the user 2026-10-18 (UD20, BUNDLE D15):* a CHARACTER.md front-matter key; `personaje.artStyle` is the default for new characters. Images record it as `provenance.artStyle` for staleness. (This row first proposed project-wide; corrected 2026-10-19.) |
| Body sections in order: Logline, Appearance, Personality, Backstory, Arc, Relationships, Voice & Speech, Pronunciation, Wardrobe | DF-39; S; G | renderer, flipbook (Appearance, Wardrobe), cast page (Logline) | in DF. **gap:** heading matching (G: `## Arc (Season 1)`). → a section matches by its name, optionally followed by a parenthetical. |
| `## Canon & Guardrails` | CC; G (9/9) | flipbook, renderer | **gap** → add as a standard section after Wardrobe. |
| `## Open Questions` with `### Needed before Portrait / Views`, `### Needed for Voice`, `### Optional`, `### Deferred` | CC; G (plus `Tier` 5/9, `Continuity` 5/9) | Personaje gates | **gap** → add, with the four standard groups; other groups allowed. |
| Footnotes `[^id]`, definitions starting `Stated.`, `Inferred.`, `Author.` | CC; G (536 defs, all classed) | renderer (sources list), Personaje `check` | **gap** (DF Q5) → add: syntax, the three classes, every reference defined and every definition used. Label conventions (`e101-23`, `pm-12`) are recommendations, not rules. |
| Other characters by exact name, in bold | DF-40 (exact name); CC (bold) | renderer, app | **gap:** bold → recommended, not required. |
| Canon facts `{fact, quote}`, relationships `{with, nature}`, "generated" marking | APP §11.4 | Personaje app | **gap** (DF Q5) → decision D9. |
| YAML comments carrying data (`# CYRUS's only name for him`, `# suggested: supporting`) | G | — | **drop?** Comments don't survive a parse-and-write. → writers must preserve the front-matter text they don't change; data must not live in comments (spec says so). |
| Unknown front-matter keys preserved | DF-40 | writer | in DF. |

## 9. CAST.md fields the format reads

| Field | Sources | Status → proposal |
|-------|---------|-------------------|
| `character`, `role`, `manifest`, `voicePrompt`, `voices.voxalta` | DF-12; G | in DF. |
| `language` | Echada, Produciesta | gap → add to DF-12 (sample language default). |
| `actor` | CC; T (page "Played by") | gap → add to DF-12 as optional (none in G). |
| Path base | CAST.md-relative (Reparto, EC-25, DF-7) vs PROJECT.md-relative (Produciesta today) vs cwd (diga) | conflict outside the format → DF-7 stands; Produciesta PD-16/17 already plans CAST.md-relative. |
| Validation warnings from the pilot banner: no `role`; `voicePrompt` differs from the selected vox's; `voices.voxalta` points elsewhere | T; CC 10 | gap → add to DF-55. |

## 10. The dossier page

| Property | Sources | Status → proposal |
|----------|---------|-------------------|
| Self-contained, page copies, sizes | DF-42, DF-43; B | in DF. G pages link by relative path (v1). |
| Embedded record `#character-record` | DF-44 (no shape); B (CHARACTER.md, manifest, member); T `{character, castMember, frontMatter, manifest}` | **gap** → schema in `schemas/`: `{formatVersion, character, castMember, frontMatter, body, manifest}` (body included, so a page alone carries the text). |
| Determinism | B D11 (must); DF-45 (should); T stamps "Generated {now}" | conflict → DF-45 (per implementation); renderers MUST NOT stamp render time. |
| `<meta>` for template version and hash | DF-46 (no name) | gap → `<meta name="dossier-template" content="<version> <sha256>">`. |
| Sources list, provenance lines, completeness, integrity banner | SD §4 parity; T; DF-52 | gap in `fields.json` → add the sources list and per-tab provenance line as page elements. |
| Host hand-off URL | Vinetas `personaje://open?bundle=&field=` | gap → out of the format (DF-51 covers the message handler); app-to-app scheme is Personaje's. |

## 11. Cross-tool identity

| Property | Sources | Status → proposal |
|----------|---------|-------------------|
| sha256 is how other tools refer to a dossier file | Vinetas panels store image and LoRA sha256s; Granville storyboards' references only link back by sha256 | **gap** → state it: file names change (DF-14); sha256 is the durable identity; readers look up by sha256. |
| "Selected asset for (kind, variant)" is the normative lookup | Vinetas, flipbook, app | **gap** → define it, including a variant-less lookup (returns the selected asset with no variant). |
| Reference roles (what a tool sends as references) | flipbook: portrait only; Vinetas: face + front view, expression swapped in | → decision D8. |

---

## Decisions (all accepted 2026-10-19 as recommended)

| # | Decision | Options | Recommendation |
|---|----------|---------|----------------|
| D1 | **Reparto's manifest path check (RQ-21)** | keep and change to `<C>.dossier/manifest.json`; drop it | Drop it (Personaje OQ-3): the validator checks the bundle; Reparto stays ignorant of dossiers. |
| D2 | **Version 1 support** | readers must read v1; v1 only through `migrate` | Readers MAY read v1 (DF-25); SwiftDossier reads it so Granville works before migration; the v1 appendix describes Granville's hybrid (v1 manifest in a `.dossier` folder). |
| D3 | **`prompts` shape** | flat `{identity, portrait, subject}`; structured portrait blocks (`framing, identity, expression, wardrobe, signature, backdrop, style`) | Flat now, with `identity` required for view and expression generation. Blocks are a Personaje composition detail. |
| D4 | **`derivedFrom` shape** | list of sha256; map role → sha256; list of `{path, sha256}` | A list of `{path, sha256, role}` for assets, plus `{template: {version, sha256}}` on `dossier`, `{castMember: sha256}` for the CAST.md entry. One shape, readable, and stale detection compares sha256s. |
| D5 | **Which file is authoritative for the voice** | CAST.md `voices.voxalta` (EC-25, what Produciesta reads); the manifest | CAST.md for *which voice to play* (every audio tool reads it); the manifest for *what's in the bundle*. A mismatch is a validation warning, and `voice` commands update both. |
| D6 | **`samples.yaml`** | standardize (schema, owner: the writer); drop it (EC-28 style: one sample per call, `sampleText` in the manifest) | Keep it as an optional, standardized file: it's the only record of *why* each line was chosen (`source`, `instruct`). Not an asset kind; listed in `files`. |
| D7 | **Where the LoRA trigger word lives** | manifest `lora.triggerWord`; SwiftVinetas engine YAML (`sks_<slug>`); both | The manifest is authoritative for a character with a dossier (DF-20); SwiftVinetas reads it from there. No slug default in the format. |
| D8 | **Reference roles** | none (each tool decides); named roles in provenance (`portrait`, `face`, `view:front`, `expression:<v>`) | Name the roles in `references[].role` so a panel records *why* each image was sent; reference policies stay with the tools. |
| D9 | **Canon facts, structured relationships, "generated" marking** | in CHARACTER.md (footnotes + front matter); in a separate data file; not in v2 | In CHARACTER.md: facts are footnoted claims (the three classes already exist); "generated" is `draft.generated: [<section or field>]`, a front-matter list a writer removes an entry from when a person edits it (no data in comments, §8). Structured `relationships` stay prose in v2. |
| D10 | **Extension keys** | forbidden; allowed and preserved | Allowed in `assets[]`, `provenance` and CHARACTER.md front matter; writers preserve them; readers ignore what they don't know. |
