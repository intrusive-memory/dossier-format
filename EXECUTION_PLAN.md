---
type: execution-plan
feature_name: OPERATION PAPER DOLL
mission_branch: mission/paper-doll/01
iteration: 1
starting_point_commit: 22ba6e8
---

# EXECUTION_PLAN.md — dossier-format page template

## Terminology

> **Mission** — A definable, testable scope of work.

> **Sortie** — An atomic, testable unit of work executed by a single autonomous AI agent in one dispatch.

> **Work Unit** — A grouping of sorties.

## Scope

REQUIREMENTS DF-42 to DF-53 and §14 acceptance 3 and 4: `data/fields.json`, `data/tokens.json`, `template/`. Nothing else. `docs/DOSSIER-FORMAT.md`, `schemas/`, `examples/` and `tools/build_examples.py` are not changed. A gap is reported.

The design source is the latest "Personaje mockups" claude.ai artifact, `project/DossierPanel.dc.html` and `project/Dossier.dc.html`. It holds private character text and images, none of which enters this CC0 repository.

## Work Units

| Work Unit | Directory | Sorties | Layer | Dependencies |
|-----------|-----------|---------|-------|--------------|
| Page template | . | 2 | 1 | none |

### Sortie 1: Field list and tokens

**Entry criteria**:
- [ ] On `mission/paper-doll/01` in a clone, not in `~/Projects/dossier-format`.

**Tasks**:
1. `data/fields.json` per DF-47: seven tabs and, per tab, every field in order, each with key, label, kind, empty text.
2. `data/tokens.json` per DF-48, light and dark.

**Exit criteria**:
- [ ] Both parse, with seven tabs in DF-47's order.
- [ ] `git diff --stat 22ba6e8 -- docs schemas examples tools` is empty.

### Sortie 2: Template

**Entry criteria**:
- [ ] Sortie 1 exit criteria hold.

**Tasks**:
1. `template/`: skeleton, generated stylesheet, custom elements `<dossier-tabs>`, `<dossier-field>`, `<dossier-image-set>`, `<dossier-audio>`, subset OFL fonts with licences, version and hash metadata.
2. `tools/` generator for the stylesheet, added without changing existing tools.
3. A hand-filled page from a synthetic character for acceptance 3, with a check script.
4. `CHANGELOG.md` entry for the template version.

**Exit criteria**:
- [ ] The check script passes: no external reference by §11's rule, all seven tabs in document order with script off, every `fields.json` key on the page and no other.
- [ ] A headless browser run confirms all seven tabs show with script off and no network request is made.

## Open Questions

_No blocking open questions identified during breakdown._
