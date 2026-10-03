---
type: doc
updated: 2026-10-03
status: draft
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
```

> **Status: draft.** This repository holds the requirements for the standard
> ([REQUIREMENTS.md](REQUIREMENTS.md)). The specification, schemas, page
> template and conformance fixtures are not written yet.

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
| SwiftDossier | Swift | planned |

## Related formats

- [vox-format](https://github.com/intrusive-memory/vox-format): the voice
  identity file a dossier carries in `voice/`.
- `CAST.md` ([SwiftReparto](https://github.com/intrusive-memory/SwiftReparto)):
  the cast list. Dossiers are found through it, never by scanning directories.

## Contributing

Work lands on `development`, the default branch. `main` changes only by a pull
request from `development`, and is what implementations pin to. See
[AGENTS.md](AGENTS.md) for the rules.

## License

Not chosen yet. Until a license file is added, all rights are reserved.
