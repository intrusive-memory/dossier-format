---
type: doc
title: dossier-format — Agent Instructions
updated: 2026-10-03
---

# AGENTS.md

Canonical project context for AI agents (Claude, Gemini, Codex) working in
dossier-format. `CLAUDE.md` and `GEMINI.md` are symlinks to this file: there is
one document, not three copies to keep in sync.

## Purpose

A dramatic character's assets (a written description, a portrait, views,
expressions, a voice) are made by several tools and read by several more. If
each tool keeps its own idea of where those files go and what they're called,
every tool has to know every other tool's layout, and a character can't leave
the app that made it.

dossier-format is the one definition they all share: a `.dossier` bundle, the
manifest that inventories it, and a self-contained HTML page that presents it.

## Goal

**A reader written from this repository alone, in any language, opens every
valid bundle and rejects every invalid one.**

That sentence decides what belongs here. If an implementer would have to read
another project's source to get something right, the standard is incomplete.

## What this repository is

The standard, and only the standard:

- the specification (`docs/`)
- JSON Schemas for the manifest and the other structured files (`schemas/`)
- data files that implementations read rather than restate: the tier
  requirements, the page's field list, the design tokens (`data/`)
- the dossier page template (`template/`)
- conformance fixtures: valid bundles, and one invalid bundle per error and
  warning code (`examples/`)

## What this repository is not

- **Not an implementation.** No reader, writer, validator or renderer lives
  here. The Swift implementation is SwiftDossier. Reference code in any
  language goes in that language's own repository.
- **Not a generator.** How an image or a voice is made, and by which model, is
  outside the standard.
- **Not the owner of neighbouring formats.** `CAST.md` belongs to SwiftReparto
  and `.vox` to vox-format. The standard says which of their fields it reads
  and nothing more.

## Status

Draft. [REQUIREMENTS.md](REQUIREMENTS.md) is the only content so far: what the
standard must say (DF-1 to DF-57), the deliverables, and the open questions.
The specification, schemas, data files, template and fixtures are not written.

## Rules for working here

1. **This repository is public.** Nothing from a private repository goes in:
   no character images, descriptions, voices or screenplay text from a real
   production. Fixtures use invented characters (REQUIREMENTS Q2).
2. **Everything here is CC0 1.0** ([LICENSE](LICENSE)), the same as
   vox-format. Don't copy in material that can't be released that way. The one
   exception is fonts in the template, which must be under the OFL and keep
   that license.
3. **Language-agnostic.** No requirement may name a programming language, a
   framework or an API. "The implementation detects the largest face" is a
   rule; "use Vision" is not.
4. **State every algorithm in full,** with a worked example. Never "as
   SwiftAcervo does it" or "see the Swift code".
5. **Requirement IDs are permanent.** `DF-n` numbers are never reused or
   renumbered. A withdrawn requirement keeps its number and is marked
   withdrawn.
6. **Use MUST, SHOULD and MAY** as in RFC 2119, in the specification.
7. **Breaking changes are format versions.** A change that makes an existing
   valid bundle invalid raises `manifestVersion`. The template has its own
   version. Both are recorded in `CHANGELOG.md`.
8. **Every Markdown file starts with YAML front matter** that has a `type:`
   line.
9. **A change to the standard updates its fixtures and schemas in the same pull
   request.** A rule with no fixture isn't testable.

## Branches and pull requests

- **`development`** is the default branch. All work lands here, directly or
  from a short-lived branch.
- **`main`** is what implementations pin to. It changes only by a pull request
  from `development`. Direct pushes are blocked.
- A merge to `main` that changes the format or the template is tagged with the
  version it defines.

## Related repositories

| Repository | Relation |
|------------|----------|
| SwiftDossier | The Swift implementation of this standard (planned). |
| [vox-format](https://github.com/intrusive-memory/vox-format) | The voice file a dossier carries. The model for how this repository is laid out. |
| [SwiftReparto](https://github.com/intrusive-memory/SwiftReparto) | Owns `CAST.md`, where discovery starts, and implements the name canonicalization rule in Swift. |
| Personaje | The app that builds dossiers. The first source of these requirements. |
