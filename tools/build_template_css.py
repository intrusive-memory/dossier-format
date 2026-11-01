#!/usr/bin/env python3
"""Generate template/dossier.css and template/fonts.css from data/tokens.json.

    python3 tools/build_template_css.py          # writes both
    python3 tools/build_template_css.py --check  # exits 1 when a file on disk differs

Colors, type, sizes, spacing and radii come from the tokens. The rules below say
where each token goes, with a few structural constants of their own (a hidden
label's clipping, the footnote mark's size). Output is byte-stable. Standard
library only.
"""
import base64
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "template"

# Colors the tokens keep for an application's own chrome, not the page (tokens.json $comment).
APP_ONLY_COLORS = re.compile(r"^(toolbar|controlShadow)")
# Layout values that are counts, not lengths.
COUNT_KEY = re.compile(r"(Columns|TextSpan|^column|^columns)$")

LATIN = "U+0020-007E, U+00A0-00FF, U+0100-017F, U+2013-2014, U+2018-201D, U+2022, U+2026"
PLEX_SANS_LATIN1 = "U+0000, U+000D, U+0020-007E, U+00A0-00FF, U+0131, U+0152-0153, U+02C6, U+02DA, U+02DC, U+2013-2014, U+2018-201A, U+201C-201E, U+2020-2022, U+2026, U+2030, U+2039-203A, U+2044, U+20AC, U+2122, U+2212, U+FB01-FB02"
PLEX_MONO_LATIN1 = PLEX_SANS_LATIN1.replace("U+0000, U+000D, ", "")
PLEX_LATIN2 = "U+0100-0101, U+0104-0130, U+0132-0151, U+0154-017F, U+018F, U+0192, U+01A0-01A1, U+01AF-01B0, U+01FA-01FF, U+0218-021B, U+0237, U+0259, U+1E80-1E85, U+1E9E, U+20A1, U+20A4, U+20A6, U+20A8-20AA, U+20AD-20AE, U+20B1-20B2, U+20B4-20B5, U+20B8-20BA, U+20BD, U+20BF"
PLEX_LATIN3 = "U+0102-0103, U+01CD-01DC, U+1EA0-1EF9, U+20AB"
# Token font, weight, file, the characters in the file (IBM's own for its split files).
FACES = [
    ("serif", 400, "instrument-serif/InstrumentSerif-Regular-Latin.woff2", LATIN),
    ("sans", 400, "ibm-plex-sans/IBMPlexSans-Regular-Latin1.woff2", PLEX_SANS_LATIN1),
    ("sans", 400, "ibm-plex-sans/IBMPlexSans-Regular-Latin2.woff2", PLEX_LATIN2),
    ("sans", 400, "ibm-plex-sans/IBMPlexSans-Regular-Latin3.woff2", PLEX_LATIN3),
    ("sans", 600, "ibm-plex-sans/IBMPlexSans-SemiBold-Latin1.woff2", PLEX_SANS_LATIN1),
    ("sans", 600, "ibm-plex-sans/IBMPlexSans-SemiBold-Latin2.woff2", PLEX_LATIN2),
    ("sans", 600, "ibm-plex-sans/IBMPlexSans-SemiBold-Latin3.woff2", PLEX_LATIN3),
    ("mono", 400, "ibm-plex-mono/IBMPlexMono-Regular-Latin1.woff2", PLEX_MONO_LATIN1),
    ("mono", 400, "ibm-plex-mono/IBMPlexMono-Regular-Latin2.woff2", PLEX_LATIN2),
    ("mono", 400, "ibm-plex-mono/IBMPlexMono-Regular-Latin3.woff2", PLEX_LATIN3),
]


def px(value):
    return f"{value:g}px"


def length(value):
    return px(value) if isinstance(value, (int, float)) else str(value)


def page_colors(colors):
    return {name: value for name, value in colors.items() if not APP_ONLY_COLORS.match(name)}


def layout_vars(tokens):
    """The narrow and wide values of a layout: same names, swapped at the breakpoint."""
    out = {}
    for name, value in tokens.items():
        if isinstance(value, list) and name == "headerPadding":
            top, side, bottom = value
            value = f"{px(top)} {px(side)} {px(bottom)}"
        elif isinstance(value, list):
            value = " ".join(f"minmax(0,{part})" for part in value)
        elif COUNT_KEY.search(name):
            value = f"{value:g}"
        else:
            value = length(value)
        out[f"--layout-{name}"] = value
    return out


def nested_vars(prefix, tokens):
    out = {}
    for name, value in tokens.items():
        if isinstance(value, dict):
            out.update(nested_vars(f"{prefix}-{name}", value))
        elif COUNT_KEY.search(name):
            out[f"{prefix}-{name}"] = f"{value:g}"
        else:
            out[f"{prefix}-{name}"] = length(value)
    return out


def component_vars(tokens):
    colors = set(tokens["color"]["light"])
    out = {}
    for component, values in tokens["component"].items():
        for name, value in values.items():
            if name == "radius":
                value = f"var(--radius-{value})"
            elif isinstance(value, str) and value in colors:
                value = f"var(--color-{value})"
            out[f"--{component}-{name}"] = length(value)
    return out


def declarations(style):
    """The declarations of a data/tokens.json 'type' entry."""
    size = style["size"]
    parts = [f"font-family:var(--font-{style['font']})",
             "font-size:var(--type-name-size)" if isinstance(size, dict) else f"font-size:{px(size)}",
             f"font-weight:{style['weight']}"]
    if "lineHeight" in style:
        parts.append(f"line-height:{style['lineHeight']:g}")
    parts.append(f"color:var(--color-{style['color']})")
    if "letterSpacing" in style:
        parts.append(f"letter-spacing:{style['letterSpacing']:g}em")
    if "textTransform" in style:
        parts.append(f"text-transform:{style['textTransform']}")
    return ";".join(parts)


def block(selector, variables):
    return selector + "{\n" + "".join(f"  {name}:{value};\n" for name, value in variables.items()) + "}\n"


def build_css(tokens):
    types = tokens["type"]
    layout = tokens["layout"]
    root = {}
    root.update({f"--color-{name}": value for name, value in page_colors(tokens["color"]["light"]).items()})
    for name, font in tokens["font"].items():
        root[f"--font-{name}"] = f'"{font["family"]}",{font["fallback"]}'
    root["--type-name-size"] = px(types["name"]["size"]["narrow"])
    root.update({f"--space-{value:g}": px(value) for value in tokens["space"]})
    root.update({f"--radius-{name}": length(value) for name, value in tokens["radius"].items()})
    root.update({f"--border-{name}": length(value) for name, value in tokens["border"].items()})
    root.update({f"--aspect-{name}": value for name, value in tokens["aspect"].items()})
    root.update(layout_vars(layout["narrow"]))
    root.update(nested_vars("--profile", layout["profile"]))
    root.update(nested_vars("--shared", layout["shared"]))
    root.update(component_vars(tokens))

    wide = {"--type-name-size": px(types["name"]["size"]["wide"])}
    wide.update(layout_vars(layout["wide"]))
    dark = {f"--color-{name}": value for name, value in page_colors(tokens["color"]["dark"]).items()}

    type_classes = "".join(f".t-{name}{{{declarations(style)}}}\n" for name, style in types.items())

    # Selectors name the field keys of data/fields.json.
    rules = """
*,*::before,*::after{box-sizing:border-box}
html{color-scheme:light dark;-webkit-text-size-adjust:100%}
body{margin:0;background:var(--color-background);color:var(--color-text);font-family:var(--font-sans)}
dossier-tabs,dossier-field,dossier-image-set,dossier-audio{display:block}
[data-state="absent"]{display:none}
dossier-field:target{outline:var(--border-selected) solid var(--color-accent);outline-offset:var(--border-selected)}
a{color:var(--link-color)}
a:hover{color:var(--link-hover)}
.field-label{display:block;margin-bottom:var(--profile-fieldGap)}
.field-label.is-hidden{position:absolute;width:1px;height:1px;margin:-1px;padding:0;overflow:hidden;clip-path:inset(50%);white-space:nowrap;border:0}
.field-value p{margin:0}
.field-value p+p,.field-value p+ul,.field-value ul+p{margin-top:var(--space-6)}
.field-value ul{margin:0;padding-left:var(--space-18)}
.field-value h4{margin:var(--space-6) 0 var(--space-2);font:inherit;font-weight:600}
dossier-field[data-kind="list"]>.field-value>ul{list-style:none;padding:0}
[data-state="empty"]>.field-value{color:var(--color-textMuted)}
dossier-field[data-key="page.sources"]>.field-value>ul{list-style:decimal;padding-left:var(--space-18)}
.mark{font-size:0.75em;line-height:0}
.mark a{text-decoration:none}
.parenthetical{margin:0 0 var(--space-4)}

/* Header: one grid, no wrappers, so the field order stays fields.json's. */
.page-before{display:grid;grid-template-columns:auto auto minmax(0,1fr);align-items:center;column-gap:var(--shared-nameRowGap);row-gap:var(--shared-headerTextGap);padding:var(--layout-headerPadding)}
[data-key="page.integrity"]{grid-column:1/-1;grid-row:1;margin-bottom:var(--space-12);background:var(--banner-background);color:var(--banner-color);border:var(--border-hairline) solid var(--banner-border);border-radius:var(--banner-radius);padding:var(--banner-paddingBlock) var(--banner-paddingInline)}
[data-key="page.integrity"] .field-value{color:inherit}
[data-key="page.face"]{grid-column:1;grid-row:2/span 3;width:var(--layout-faceSize);margin-right:calc(var(--shared-headerGap) - var(--shared-nameRowGap))}
[data-key="page.face"] .image-frame{aspect-ratio:var(--aspect-square);background:var(--faceImage-background);border-radius:var(--faceImage-radius)}
[data-key="page.name"]{grid-column:2/-1;grid-row:2;min-width:0}
[data-key="page.tier"]{grid-column:2;grid-row:3}
[data-key="page.tier"] .field-value{display:inline-block;background:var(--badge-background);padding:var(--badge-paddingBlock) var(--badge-paddingInline);border-radius:var(--badge-radius)}
[data-key="page.completeness"]{grid-column:3;grid-row:3}
[data-key="page.facts"]{grid-column:2/-1;grid-row:4}
[data-key="page.missing"]{grid-column:1/-1;grid-row:5;margin-top:var(--space-8)}

/* Tabs. Without script every panel shows, stacked; a selected panel is screen-only. */
.tab-list{display:flex;flex-wrap:wrap;gap:0 var(--shared-tabGap);padding:0 var(--layout-sidePadding);border-bottom:var(--border-hairline) solid var(--tabs-divider)}
.tab-link{display:inline-flex;align-items:center;height:var(--shared-tabHeight);padding:0 var(--shared-tabPadding);text-decoration:none}
.tab-link:hover{color:var(--color-text)}
.tab-link[aria-selected="true"]{TAB_SELECTED;box-shadow:inset 0 calc(-1*var(--border-tabIndicator)) 0 var(--tabs-indicator)}
.tab-panel{padding:var(--shared-bodyPaddingTop) var(--layout-sidePadding) var(--shared-bodyPaddingBottom)}
.tab-panel+.tab-panel{border-top:var(--border-hairline) solid var(--tabs-divider)}
.tab-heading{margin:0 0 var(--shared-bodyGap)}
.tab-body{display:flex;flex-direction:column;gap:var(--shared-bodyGap)}
.page-after{padding:0 var(--layout-sidePadding) var(--shared-bodyPaddingBottom)}
.play-button{display:flex;align-items:center;justify-content:center;flex-shrink:0;width:var(--playButton-size);height:var(--playButton-size);padding:0;border:0;border-radius:var(--playButton-radius);background:var(--playButton-background);color:var(--playButton-color);cursor:pointer}
html[data-script] dossier-tabs:not([data-enhanced])>.tab-panel:not(:first-of-type){display:none}
@media screen{
  dossier-tabs[data-enhanced]>.tab-panel:not([data-active]){display:none}
  dossier-tabs[data-enhanced]>.tab-panel{border-top:0}
  dossier-tabs[data-enhanced] .tab-heading{position:absolute;width:1px;height:1px;margin:-1px;overflow:hidden;clip-path:inset(50%);white-space:nowrap}
}
[data-key$=".provenance"]{border-top:var(--border-hairline) solid var(--provenance-divider);padding-top:var(--shared-provenancePaddingTop);overflow-wrap:anywhere}

/* Profile */
#profile>.tab-body{display:grid;grid-template-columns:var(--layout-profileColumns);gap:var(--profile-rowGap) var(--profile-columnGap);align-items:start}
.field-group{display:flex;flex-direction:column;gap:var(--profile-groupGap);min-width:0}
.field-group[data-group="facts"]{display:grid;grid-template-columns:repeat(var(--profile-facts-columns),minmax(0,1fr));gap:var(--profile-facts-rowGap) var(--profile-facts-columnGap)}
[data-key="profile.provenance"]{grid-column:1/-1}
[data-key="profile.canon"] li{display:flex;gap:var(--canonItem-gap);align-items:flex-start;margin-top:var(--space-6);padding:var(--canonItem-paddingBlock) var(--canonItem-paddingInline);background:var(--canonItem-background);border:var(--border-hairline) solid var(--canonItem-border);border-radius:var(--canonItem-radius)}
.canon-claim{flex-grow:1}
.canon-source{flex-shrink:0}

/* Images */
figure.image{display:flex;flex-direction:column;gap:var(--shared-figureGap);margin:0}
.image-frame{position:relative;overflow:hidden;aspect-ratio:var(--aspect-portrait);background:var(--imageFrame-background);border-radius:var(--imageFrame-radius)}
.image-frame img{display:block;width:100%;height:100%;object-fit:cover}
[data-state="empty"] .image-frame{display:flex;align-items:center;justify-content:center;background:var(--imageMissing-background);border:var(--border-hairline) var(--imageMissing-borderStyle) var(--imageMissing-border);border-radius:var(--imageMissing-radius)}
.image-missing{VIEW_MISSING}
.image-caption{overflow-wrap:anywhere}
.item-caption{display:flex;flex-direction:column;gap:var(--space-2)}
.image-grid{display:grid;grid-template-columns:repeat(var(--layout-viewColumns),minmax(0,1fr));gap:var(--shared-imageGridGap)}
[data-key="views.threeQuarter"] .image-frame{outline:var(--primaryView-outlineWidth) solid var(--primaryView-outline);outline-offset:var(--primaryView-outlineOffset)}
#expressions .image-grid{grid-template-columns:repeat(var(--layout-expressionColumns),minmax(0,1fr));gap:var(--shared-expressionGridGap)}
#expressions figure.image{gap:var(--shared-expressionFigureGap)}
#expressions .image-frame{aspect-ratio:var(--aspect-square)}
#expressions .image-missing{EXPRESSION_MISSING}
html[data-script] dossier-field[data-kind="image"] img{cursor:zoom-in}
.lightbox{max-width:100vw;max-height:100vh;padding:0;border:0;background:transparent;cursor:zoom-out}
.lightbox::backdrop{background:var(--color-cropScrim)}
.lightbox img{display:block;max-width:96vw;max-height:96vh;width:auto;height:auto}

/* Portrait */
#portrait>.tab-body{display:grid;grid-template-columns:repeat(var(--layout-portraitColumns),minmax(0,1fr));grid-template-rows:auto 1fr;gap:var(--shared-imageGridGap)}
[data-key="portrait.image"]{grid-column:1;grid-row:1/span 2}
[data-key="portrait.prompt"],[data-key="portrait.artStyle"]{grid-column:2/span var(--layout-portraitTextSpan)}
[data-key="portrait.provenance"]{grid-column:1/-1}

/* Face */
#face>.tab-body{flex-direction:row;flex-wrap:wrap;align-items:flex-start;gap:var(--shared-faceGap)}
[data-key="face.portrait"]{width:var(--shared-facePortraitWidth);flex-shrink:0}
[data-key="face.crop"]{width:var(--shared-faceCropSize)}
[data-key="face.crop"] .image-frame{aspect-ratio:var(--aspect-square);background:var(--faceCrop-background);border-radius:var(--faceCrop-radius)}
[data-key="face.provenance"]{flex-basis:100%}
.crop-overlay{position:absolute;aspect-ratio:var(--aspect-square);border:var(--cropOverlay-borderWidth) var(--cropOverlay-borderStyle) var(--cropOverlay-color);box-shadow:0 0 0 999px var(--cropOverlay-scrim)}

/* Voice */
#voice>.tab-body{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:var(--shared-voiceFactsRowGap) var(--shared-voiceFactsColumnGap);max-width:var(--shared-voiceMaxWidth)}
[data-key="voice.prompt"],[data-key="voice.pronunciation"],[data-key="voice.provenance"]{grid-column:1/-1}
[data-key="voice.vox"] .field-value{overflow-wrap:anywhere}

/* Samples */
#samples>.tab-body{max-width:var(--shared-samplesMaxWidth)}
dossier-audio{display:flex;flex-direction:column;gap:var(--shared-samplesGap)}
.sample-row{display:flex;flex-wrap:wrap;gap:var(--sampleRow-gap);align-items:center;background:var(--sampleRow-background);border:var(--border-hairline) solid var(--sampleRow-border);border-radius:var(--sampleRow-radius);padding:var(--sampleRow-paddingBlock) var(--sampleRow-paddingInline)}
.sample-row audio{max-width:100%}
html[data-script] .sample-row{flex-wrap:nowrap}
html[data-script] .sample-row audio:not([controls]){display:none}
.sample-text{display:flex;flex-direction:column;gap:var(--sampleRow-textGap);flex:1 1 12em;min-width:0}

@media print{
  .tab-list,.play-button,.sample-row audio{display:none}
  .tab-panel,.image-frame,.sample-row,figure.image{break-inside:avoid}
  #profile.tab-panel{break-inside:auto}
  html{color-scheme:light;print-color-adjust:exact;-webkit-print-color-adjust:exact}
}
""".replace("TAB_SELECTED", declarations(types["tabSelected"])) \
        .replace("VIEW_MISSING", declarations(types["viewMissing"])) \
        .replace("EXPRESSION_MISSING", declarations(types["expressionMissing"]))

    wide_rules = f"""@media screen and (min-width:{px(layout["wideMinWidth"])}){{
{block(":root", wide)}  .page-before{{grid-template-columns:auto minmax(0,max-content) auto minmax(0,1fr)}}
  [data-key="page.face"]{{grid-row:2/span 2}}
  [data-key="page.name"]{{grid-column:2}}
  [data-key="page.tier"]{{grid-column:3;grid-row:2}}
  [data-key="page.completeness"]{{grid-column:4;grid-row:2}}
  [data-key="page.facts"]{{grid-row:3}}
  [data-key="page.missing"]{{grid-row:4}}
  .field-group[data-group="facts"],.field-group[data-group="summary"]{{grid-column:1}}
  .field-group[data-group="sections"]{{grid-column:2;grid-row:1/span 3}}
  #profile>.tab-body{{grid-template-rows:auto auto 1fr}}
  [data-key="profile.provenance"]{{grid-row:4}}
}}
"""
    dark_rules = "@media screen and (prefers-color-scheme:dark){\n" + block(":root", dark) + "}\n"
    css = ("/* Generated by tools/build_template_css.py from data/tokens.json. Don't edit. */\n"
           + block(":root", root) + dark_rules + type_classes + rules.lstrip("\n") + wide_rules)

    defined = {name for variables in (root, wide, dark) for name in variables}
    used = set(re.findall(r"var\((--[A-Za-z0-9-]+)\)", css))
    undefined = used - defined
    if undefined:
        raise SystemExit(f"rules use variables the tokens don't define: {sorted(undefined)}")
    return css


def build_fonts(tokens, template=TEMPLATE):
    faces = {(font, weight) for font, weight, _, _ in FACES}
    for name, font in tokens["font"].items():
        for weight in font["weights"]:
            if (name, weight) not in faces:
                raise SystemExit(f"tokens ask for {name} {weight}: no face in FACES")
    out = ["/* Generated by tools/build_template_css.py from data/tokens.json and template/fonts/. Don't edit. Fonts: SIL OFL 1.1, see template/fonts/. */\n"]
    for font, weight, path, ranges in FACES:
        data = base64.b64encode((template / "fonts" / path).read_bytes()).decode()
        family = tokens["font"][font]["family"]
        out.append(f'@font-face{{font-family:"{family}";font-style:normal;font-weight:{weight};font-display:block;'
                   f'src:url(data:font/woff2;base64,{data}) format("woff2");unicode-range:{ranges}}}\n')
    return "".join(out)


def main():
    tokens = json.loads((ROOT / "data/tokens.json").read_text(encoding="utf-8"))
    outputs = {TEMPLATE / "dossier.css": build_css(tokens), TEMPLATE / "fonts.css": build_fonts(tokens)}
    if "--check" in sys.argv[1:]:
        stale = [path.name for path, text in outputs.items()
                 if not path.exists() or path.read_text(encoding="utf-8") != text]
        if stale:
            print(f"out of date with data/tokens.json: {', '.join(stale)}")
            return 1
        print("ok: dossier.css and fonts.css agree with data/tokens.json")
        return 0
    for path, text in outputs.items():
        path.write_text(text, encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)}: {len(text.encode())} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
