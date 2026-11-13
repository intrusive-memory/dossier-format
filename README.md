---
type: doc
updated: 2026-11-12
status: released
---

# dossier-format

**A character, as a folder.** `dossier-format` is an open, language-agnostic
standard for a character dossier: one `.dossier` bundle holding everything a
dramatic character needs, plus one self-contained HTML page that presents it.

```
characters/THE PRACTITIONER.dossier/
  manifest.json                    the inventory, with hashes
  CHARACTER.md                     the written description
  THE PRACTITIONER-dossier.html    the dossier page: one file, everything embedded
  images/                          portrait, face crop, views, expressions
  voice/                           the .vox voice and playable samples
  .preview/                        hidden: the page as a viewer last built it, outside the manifest
```

A tool showing a dossier doesn't need the page to exist or to be current: it builds a
**preview** from the bundle as it is on disk, stores it in `.preview/` under a key that
changes when the manifest does, and shows the stored one while the key still matches
([§11.1](docs/DOSSIER-FORMAT.md#111-the-preview-df-68-to-df-74)).

> **Status: 2.1.0, released 2026-11-12.** Implementations pin the tag `v2.1.0`; what
> changed in each release is in [CHANGELOG.md](CHANGELOG.md). 2.1.0
> adds **location bundles**: a place's description and its plates, declared in `PROJECT.md`,
> indexed in `LOCATIONS.md` and shown together on one synthesized LOCATIONS page
> ([§16](docs/DOSSIER-FORMAT.md#16-location-bundles-df-79-to-df-84-df-96-to-df-99)). The specification is
> [docs/DOSSIER-FORMAT.md](docs/DOSSIER-FORMAT.md) (format version 2), with
> JSON Schemas in [schemas/](schemas) and the tier table in
> [data/tiers.json](data/tiers.json). Conformance fixtures are in
> [examples/](examples). Every property and the decision behind it is in
> [docs/PROPERTY-INVENTORY.md](docs/PROPERTY-INVENTORY.md). The page template is in
> [template/](template), and the LOCATIONS page template in [template-locations/](template-locations);
> the field list and design tokens are in [data/](data). Requirements:
> [REQUIREMENTS.md](REQUIREMENTS.md).

## Purpose

A character's assets are made by several tools and read by several more: one
writes the description, one renders the images, one builds the voice, and
others use all of it to make scenes and audio. Without a shared definition,
every tool has to know every other tool's layout, and a character can't leave
the app that made it.

dossier-format is that shared definition.

## Goal

A reader written from this repository alone, in any language, opens every
valid bundle and rejects every invalid one.

## What this repository is

The standard, and only the standard:

- the bundle layout and how files in it are named
- the manifest schema and its integrity rules
- the asset kinds, and which ones each casting tier requires
- the `CHARACTER.md` structure
- what a conforming dossier page contains, and the template it's built from
- what a validator must report
- fixtures any implementation can test against

It contains no implementation. A reader, writer or renderer in any language
can conform to it.

## Implementations

| Implementation | Language | Status |
|----------------|----------|--------|
| [SwiftDossier](https://github.com/intrusive-memory/SwiftDossier) | Swift | Reader, writer, validator and viewer |

## Related formats

- [vox-format](https://github.com/intrusive-memory/vox-format): the voice
  identity file a dossier carries in `voice/`.
- `CAST.md` ([SwiftReparto](https://github.com/intrusive-memory/SwiftReparto)):
  the cast list. Dossiers are found through it, never by scanning directories.

## Contributing

Work lands on `development`, the default branch. `main` changes only by a pull
request from `development`, and is what implementations pin to: each release is
a tag on `main` with a GitHub release. See
[AGENTS.md](AGENTS.md) for the rules.

## License

[CC0 1.0 Universal](LICENSE): public domain, the same as vox-format. It covers
the specification, schemas, data files, examples and the page template. Fonts
embedded in the template keep their own license (SIL Open Font License).
