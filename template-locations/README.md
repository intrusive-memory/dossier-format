---
type: doc
title: The LOCATIONS page template
updated: 2026-11-12
---

# The LOCATIONS page template

The template for a project's LOCATIONS page (DOSSIER-FORMAT §16.6, REQUIREMENTS DF-97 to
DF-99). Template version: see [`VERSION.json`](VERSION.json). It is versioned and hashed
apart from the dossier page template in [`../template/`](../template), so that a change to
one never makes the other's output stale.

It is a template of its own, not a part of `template/`, for two reasons. The dossier
template's hash covers every file under `template/` (its rule 1), so a locations file there
would change that hash and make every character page in every project stale, with nothing
on those pages changed. And the page has no tabs and no field list: `data/fields.json` and
`dossier.js` are about a character.

It looks like a dossier page because it carries the dossier template's own stylesheet and
fonts, `template/dossier.css` and `template/fonts.css`, unchanged, and adds a small
stylesheet that uses only their custom properties and classes. So it follows
`data/tokens.json`, the dark mode and the print rule.

Everything here is CC0 1.0. The fonts it carries keep the SIL Open Font License, as in
`template/`.

| File | Contents |
|------|----------|
| `skeleton.html` | The page, with the placeholders below. |
| `fragments.html` | One piece of markup per thing a renderer stamps out. |
| `locations.css` | The page's own layout. Written by hand. |
| `page-copies.json` | The image copies' sizes and quality, in one place. |
| `VERSION.json` | `version` and `sha256`. |
| `example/` | The stored page of `examples/valid/locations-page-current`. Not hashed. |

Checks: `python3 tools/check_template.py`, which also runs `tools/template_version.py --check`
for both templates.

## How a renderer fills the template

**Substitution and escaping** are `template/README.md`'s: a placeholder is `{{name}}`,
replaced left to right in one pass, with replacement text not scanned again. *Text* is
HTML-escaped (`&`, `<`, `>`, `"`, `'`). *Markup* comes only from this template or from
the rules here.

### `skeleton.html`

| Placeholder | Value | Type |
|-------------|-------|------|
| `{{template.version}}`, `{{template.sha256}}` | From this directory's `VERSION.json` | Text |
| `{{key}}` | The page's key (§16.6) | Text |
| `{{title}}` | `PROJECT.md`'s `title`, then ` · Locations`; `Locations` when there is no title | Text |
| `{{include:fonts.css}}`, `{{include:dossier.css}}` | `template/fonts.css` and `template/dossier.css`, as they are | Markup |
| `{{include:locations.css}}` | This directory's `locations.css`, as it is | Markup |
| `{{project}}` | A `project` fragment with the title as `{{text}}`, or nothing when there is no title | Markup |
| `{{count}}` | The number of entries in the index, then ` location`, or ` locations` for any number but 1 | Text |
| `{{locations}}` | A `location` fragment per entry of the index, in its order, joined by one LF | Markup |

### `location`

| Placeholder | Value |
|-------------|-------|
| `{{id}}` | An `id` fragment whose `{{id}}` is `location-` and the first 8 hexadecimal characters of the SHA-256 of the entry's `location` as UTF-8. Nothing when an earlier entry has the same `location`. |
| `{{name}}` | The entry's `location`. Text. |
| `{{heading}}` | The bundle's `location.name` when it is a non-empty string, otherwise the entry's `location`. Text. |
| `{{content}}` | Below. Markup. |

**`{{content}}`,** when the entry has no `manifest:`, is a `missing` fragment with the text
`No bundle yet.` When the pointer doesn't reach a location bundle that can be shown (§16.6),
it is a `missing` fragment with the text `This location's bundle can't be shown.` Otherwise
it is these, in order, each left out when it is empty:

1. a `description` fragment, whose `{{markup}}` is `LOCATION.md`'s body by rule 2;
2. a `sources` fragment, with a `sourceItem` per footnote definition by rule 3;
3. a `plates` fragment, with an `imageItem` per selected plate, in the order §16.6 gives;
4. a `views` fragment, with an `imageItem` per selected view, in the byte order of `variant`.

An `imageItem`'s `{{label}}` is the asset's `variant` (Text), and its `{{img}}` an `img`
fragment: `{{label}}` the same, `{{src}}` the copy (rule 4) as a `data:` URI, and
`{{width}}` and `{{height}}` the copy's size.

## Template rules

These rules are normative: DOSSIER-FORMAT §16.6 makes them part of the format.

1. **The template's `sha256`.** List every regular file under `template-locations/` except
   `VERSION.json`, `README.md`, anything under `example/`, and any path with a segment
   beginning with `.`, and add `template/dossier.css` and `template/fonts.css`. Write each
   path relative to the repository root, with `/` (`template-locations/skeleton.html`).
   Sort them by the byte order of their UTF-8 form, and hash with SHA-256 the concatenation,
   for each file, of its path, one NUL byte and its bytes. This is `template/README.md`'s rule
   1 over a different list, and a change to either of the two shared files changes this hash
   as well as the dossier template's.
2. **Markdown.** `LOCATION.md`'s body, which is everything after the line that closes its
   front matter, is read by `template/README.md`'s rule 3, with these changes, made line by
   line before it:
   - A line that starts with `# ` is read as a blank line: the section's heading already
     names the location.
   - A line that starts with `## ` is read as `### ` and the same text, so it is an `<h4>`.
   - **Tables.** A line whose first non-space character is `|`, directly followed by a
     **delimiter row**, starts a table, wherever it is, and ends the paragraph, list item or
     quote before it. A row's cells are found by trimming the line, removing its first `|`
     and, if there is one, its last `|`, splitting the rest at each `|`, and trimming each
     cell. A delimiter row is a row every cell of which matches `:?-+:?`. The table runs
     over each following line whose first non-space character is `|`. It is written
     `<table><thead><tr>` with a `<th>` per cell of the first row, `</tr></thead><tbody>`, a
     `<tr>` per row after the delimiter with a `<td>` per cell, and `</tbody></table>`. Every
     row has as many cells as the first: extra cells are dropped and missing ones are empty.
     A `|` can't be escaped. Cells take inline markup.
   - **Code spans.** A run of text between two backticks on one line, with at least one
     character and no backtick between them, is written `<code>`, the text, `</code>`. Its
     text is escaped and takes no other inline markup, and `**` and `*` don't span it.
   - Inline markup is `**bold**`, `*emphasis*`, code spans and marks (rule 3), in that
     template's order: escape, then code spans, then bold, then emphasis, then marks.
3. **Footnotes** are `template/README.md`'s field rule 2 within one location: definitions are
   taken out of the body, each reference with a definition is a `mark` fragment numbered by
   citation order, two marks with nothing between them have a `markSeparator` fragment
   between them, and a reference with no definition stays as plain text. The definitions are
   the `sourceItem`s, in that order, each with its text (Text). Marks aren't links: the page
   has one Sources list per location, and an anchor couldn't say which.
4. **Image copies** are JPEG at the quality in `page-copies.json`. A plate is scaled to
   cover 1280×720 and cropped at the centre, as `template/README.md`'s rule 5 says. A view is
   scaled, up or down, to the largest size that fits inside 1280×720 keeping its shape: the
   scale is the smaller of 1280 ÷ width and 720 ÷ height, and each side is rounded half up,
   and is at least 1. A view of a location is often a drawing of another shape, and cropping
   it would cut off part of what was drawn.
5. **No script.** The page carries none. It has no tabs, nothing to play and no host
   handler, and it shows the same with script on or off.
6. **Print is always light,** by `template/dossier.css`'s print rule.

## The example

`example/LOCATIONS.html` is the stored page of `examples/valid/locations-page-current`, byte
for byte. No tool writes it. `tools/build_examples.py` fills this template for that fixture,
which is test data, not a renderer (AGENTS.md). After a change to this template, or to
`template/dossier.css` or `template/fonts.css`, regenerate the fixtures and copy that page
over this one; `tools/check_template.py` fails until it is current.
