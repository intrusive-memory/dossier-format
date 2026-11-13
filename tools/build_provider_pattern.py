#!/usr/bin/env python3
"""Regenerate the `provider` pattern in schemas/manifest-v2.schema.json.

DOSSIER-FORMAT §7 (DF-93): a `voice` record's `provider` is lowercase, which means that
Unicode's default full lowercase mapping leaves it unchanged. JSON Schema patterns have no
portable way to say that (`\\p{Changes_When_Lowercased}` isn't supported everywhere), so the
schema spells it out: a negated character class of every code point that lowercasing
changes, in the Unicode version below. A code point assigned in a later version is covered
by the text, not by this pattern (the text wins: §0).

    python3 tools/build_provider_pattern.py          # rewrite the schema's pattern
    python3 tools/build_provider_pattern.py --check  # exit 1 if it is out of date

This is a generator for the schema, not an implementation of the format.
"""
import json
import sys
import unicodedata
from pathlib import Path

UNICODE = "17.0.0"
ROOT = Path(__file__).resolve().parent.parent
SCHEMA = ROOT / "schemas/manifest-v2.schema.json"


def changes_when_lowercased():
    return [cp for cp in range(0x110000)
            if not 0xD800 <= cp <= 0xDFFF and chr(cp).lower() != chr(cp)]


def ranges(points):
    out = []
    for cp in points:
        if out and out[-1][1] == cp - 1:
            out[-1][1] = cp
        else:
            out.append([cp, cp])
    return out


def escape(cp):
    # Astral code points are written as themselves: an escape for them differs between
    # regular expression dialects, and the character itself means the same in each that
    # reads patterns as code points (ECMA-262 with the u flag, Python, ICU).
    return f"\\u{cp:04X}" if cp <= 0xFFFF else chr(cp)


def pattern():
    if unicodedata.unidata_version != UNICODE:
        sys.exit(f"needs Unicode {UNICODE}; this Python has {unicodedata.unidata_version}")
    parts = []
    for low, high in ranges(changes_when_lowercased()):
        parts.append(escape(low) if low == high else escape(low) + ("" if high == low + 1 else "-") + escape(high))
    return "^[^" + "".join(parts) + "]+$"


def provider(schema):
    for item in schema["properties"]["assets"]["items"]["properties"]["derivedFrom"]["items"]["oneOf"]:
        if item["properties"]["role"].get("const") == "voice":
            return item["properties"]["provider"]
    raise KeyError("voice record")


def main():
    text = SCHEMA.read_text(encoding="utf-8")
    schema = json.loads(text)
    want = pattern()
    node = provider(schema)
    if "--check" in sys.argv:
        sys.exit(0 if node["pattern"] == want else 1)
    node["pattern"] = want
    SCHEMA.write_text(json.dumps(schema, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{len(want)} characters")


if __name__ == "__main__":
    main()
