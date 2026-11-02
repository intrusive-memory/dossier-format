#!/usr/bin/env python3
"""Check template/ and its hand-filled example against the standard.

    python3 tools/check_template.py [PAGE]

PAGE defaults to the page in template/example/. Standard library only; when the
jsonschema package is importable the record is also validated in full, manifest
included, and the output says which of the two ran. Exits 1 on any failure.

This checks a template and a page. It isn't a validator of bundles; that's an
implementation's job.
"""
import base64
import hashlib
import json
import re
import struct
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "template"

ATTRIBUTES = {"src", "srcset", "href", "xlink:href", "poster", "data", "action", "formaction", "background"}
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
ELEMENT_FOR_KIND = {"text": "dossier-field", "longText": "dossier-field", "list": "dossier-field",
                    "image": "dossier-field", "imageSet": "dossier-image-set", "audio": "dossier-audio"}
SKELETON_PLACEHOLDERS = {"lang", "character", "template.version", "template.sha256", "include:fonts.css",
                         "include:dossier.css", "include:dossier.js", "page.before", "tab.links", "tab.panels",
                         "page.after", "record"}
REQUEST_APIS = ("fetch(", "XMLHttpRequest", "WebSocket", "EventSource", "sendBeacon", "import(", "importScripts", "new Worker")

failures = []


def check(condition, message):
    if not condition:
        failures.append(message)
    return condition


class Page(HTMLParser):
    """The page as HTML: its elements, its text in style elements, its record."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.elements = []  # (tag, attrs, ancestors)
        self.stack = []
        self.styles = []
        self.record_text = []
        self.scripts = []
        self.in_style = self.in_record = self.in_script = False
        self.nesting_errors = []
        self.markup_text = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        self.elements.append((tag, attributes, tuple(self.stack)))
        if tag == "style":
            self.in_style = True
        if tag == "script":
            self.in_script = True
            self.in_record = attributes.get("id") == "character-record"
            self.scripts.append("")
        if tag not in VOID:
            self.stack.append(tag)

    def handle_startendtag(self, tag, attrs):
        self.elements.append((tag, dict(attrs), tuple(self.stack)))

    def handle_endtag(self, tag):
        if tag == "style":
            self.in_style = False
        if tag == "script":
            self.in_script = self.in_record = False
        if tag in VOID:
            return
        if not self.stack or self.stack[-1] != tag:
            self.nesting_errors.append(f"</{tag}> closes {self.stack[-1] if self.stack else 'nothing'}")
            return
        self.stack.pop()

    def handle_data(self, data):
        if self.in_style:
            self.styles.append(data)
        elif self.in_record:
            self.record_text.append(data)
        elif self.in_script:
            self.scripts[-1] += data
        else:
            self.markup_text.append(data)


def parse(text):
    page = Page()
    page.feed(text)
    page.close()
    return page


def srcset_candidates(value):
    """The URLs of a srcset, as HTML parses it: a comma inside a URL doesn't split one."""
    urls = []
    position = 0
    while True:
        while position < len(value) and (value[position].isspace() or value[position] == ","):
            position += 1
        if position >= len(value):
            return urls
        start = position
        while position < len(value) and not value[position].isspace():
            position += 1
        url = value[start:position]
        if url.endswith(","):
            urls.append(url.rstrip(","))
            continue
        urls.append(url)
        depth = 0
        while position < len(value):  # The descriptor runs to a comma outside parentheses.
            char = value[position]
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
            elif char == "," and depth <= 0:
                break
            position += 1


def css_references(css):
    found = [m.group(2) for m in re.finditer(r"url\(\s*(['\"]?)(.*?)\1\s*\)", css, re.I | re.S)]
    found += [m.group(1) for m in re.finditer(r"@import\s+['\"]([^'\"]*)['\"]", css, re.I)]
    return found


def external_references(page):
    """§11's W-PAGE-EXTERNAL: everything the page references that isn't allowed."""
    bad = []

    def consider(reference, tag=None):
        reference = reference.strip()
        if not reference or reference.startswith("#") or reference.lower().startswith("data:"):
            return
        if tag == "a" and re.match(r"(https?|mailto):", reference, re.I):
            return
        bad.append(reference[:120])

    for tag, attributes, _ in page.elements:
        for name, value in attributes.items():
            if value is None:
                continue
            if name in ATTRIBUTES:
                if name == "srcset":
                    for url in srcset_candidates(value):
                        consider(url)
                else:
                    consider(value, tag)
            if name == "style":
                for reference in css_references(value):
                    consider(reference)
    for css in page.styles:
        for reference in css_references(css):
            consider(reference)
    return bad


def check_rule_against_fixtures():
    """The rule itself, on the fixtures that state the answer (examples/conformance.json)."""
    fixtures = json.loads((ROOT / "examples/conformance.json").read_text(encoding="utf-8"))["fixtures"]
    tested = 0
    for fixture in fixtures:
        path = fixture["path"]
        flagged = "W-PAGE-EXTERNAL" in fixture.get("codes", [])
        if not flagged and path not in ("valid/page-allowed-references", "valid/complete-lead"):
            continue
        bundle = ROOT / "examples" / path / fixture["bundle"]
        for candidate in bundle.glob("*-dossier.html"):
            found = external_references(parse(candidate.read_text(encoding="utf-8")))
            check(bool(found) == flagged, f"W-PAGE-EXTERNAL on fixture {path}: expected {flagged}, found {found}")
            tested += 1
    check(tested >= 8, f"only {tested} W-PAGE-EXTERNAL fixtures were tested")
    return tested


def expected_keys(fields):
    """Every key of data/fields.json, in document order: page.before, tabs, page.after."""
    keys = []

    def add(field):
        keys.append(field["key"])
        for item in field.get("items", []):
            keys.append(item["key"])

    for field in fields["page"]["before"]:
        add(field)
    for tab in fields["tabs"]:
        keys.append(tab["key"])
        for field in tab["fields"]:
            add(field)
    for field in fields["page"]["after"]:
        add(field)
    return keys


def check_keys(page, fields):
    expected = expected_keys(fields)
    keyed = [(tag, attrs) for tag, attrs, _ in page.elements if "data-key" in attrs]
    found = [attrs["data-key"] for _, attrs in keyed]
    check(found == expected, "keys on the page differ from data/fields.json: "
          f"missing {sorted(set(expected) - set(found))}, extra {sorted(set(found) - set(expected))}"
          + ("" if sorted(found) != sorted(expected) else ", or the order differs"))
    for tag, attrs in keyed:
        check(attrs.get("id") == attrs["data-key"], f"{attrs['data-key']}: id is {attrs.get('id')!r}")
    ids = [attrs["id"] for _, attrs, _ in page.elements if "id" in attrs]
    other = set(ids) - set(expected) - {"character-record"}
    check(not other, f"ids that aren't keys: {sorted(other)}")
    check(len(ids) == len(set(ids)), "duplicate ids")

    by_key = {attrs["data-key"]: (tag, attrs) for tag, attrs in keyed}

    def kinds(field, kind):
        if field["key"] in by_key:
            tag, attrs = by_key[field["key"]]
            check(attrs.get("data-kind") == kind, f"{field['key']}: data-kind {attrs.get('data-kind')!r}, not {kind!r}")
            check(tag == ELEMENT_FOR_KIND[kind], f"{field['key']}: <{tag}>, not <{ELEMENT_FOR_KIND[kind]}>")

    for field in fields["page"]["before"] + fields["page"]["after"] + [f for t in fields["tabs"] for f in t["fields"]]:
        kinds(field, field["kind"])
        for item in field.get("items", []):
            kinds(item, "image")
    return len(expected)


def check_tabs(page, fields):
    """Seven tabs, in order, in the DOM as it is with no script run."""
    expected = [tab["key"] for tab in fields["tabs"]]
    check(len(expected) == 7, f"fields.json has {len(expected)} tabs")
    panels = [(attrs.get("id"), attrs, ancestors) for tag, attrs, ancestors in page.elements
              if tag == "section" and attrs.get("data-kind") == "tab"]
    check([panel[0] for panel in panels] == expected, f"tab panels are {[panel[0] for panel in panels]}")
    for key, attrs, ancestors in panels:
        check("hidden" not in attrs and "style" not in attrs, f"tab {key} is hidden in the markup")
        check(ancestors[-1:] == ("dossier-tabs",), f"tab {key} isn't a child of <dossier-tabs>")
    links = [attrs["data-tab-link"] for tag, attrs, _ in page.elements if tag == "a" and "data-tab-link" in attrs]
    check(links == expected, f"tab links are {links}")
    check(not any(tag == "noscript" for tag, _, _ in page.elements), "the page relies on <noscript>")
    for tag, attrs, _ in page.elements:
        check(not (tag in ELEMENT_FOR_KIND.values() and "hidden" in attrs), f"{attrs.get('id')} is hidden in the markup")


def check_sources(page, fields):
    """Sources is a field of the Profile tab, once, and every mark leads to it (rule 4, rule 10)."""
    profile = next(tab for tab in fields["tabs"] if tab["key"] == "profile")
    check(any(field["key"] == "page.sources" for field in profile["fields"]), "fields.json: page.sources isn't on the Profile tab")
    tab = None
    placed = []
    for tag, attrs, _ in page.elements:
        if tag == "section" and attrs.get("data-kind") == "tab":
            tab = attrs.get("id")
        if attrs.get("id") == "page.sources":
            placed.append(tab)
    check(placed == ["profile"], f"page.sources is on {placed}, not once on the Profile tab")
    hrefs = {attrs.get("href") for tag, attrs, ancestors in page.elements if tag == "a" and "sup" in ancestors}
    check(hrefs <= {"#page.sources"}, f"marks lead to {sorted(hrefs)}")


def check_record_shape(record):
    schema = json.loads((ROOT / "schemas/record.schema.json").read_text(encoding="utf-8"))
    python_types = {"object": dict, "string": str, "null": type(None)}
    for key in schema["required"]:
        check(key in record, f"record: no {key}")
    for key, rule in schema["properties"].items():
        if key not in record:
            continue
        if "const" in rule:
            check(record[key] == rule["const"], f"record.{key} is {record[key]!r}")
        if "type" in rule:
            allowed = rule["type"] if isinstance(rule["type"], list) else [rule["type"]]
            check(isinstance(record[key], tuple(python_types[name] for name in allowed)), f"record.{key}: not {allowed}")
    manifest_schema = json.loads((ROOT / "schemas/manifest-v2.schema.json").read_text(encoding="utf-8"))
    manifest = record.get("manifest", {})
    for key in manifest_schema.get("required", []):
        check(key in manifest, f"record.manifest: no {key}")
    try:
        import jsonschema
        from referencing import Registry, Resource
    except ImportError:
        return "shape only (required keys, types, const; jsonschema isn't installed)"
    resource = Resource.from_contents(manifest_schema)
    registry = Registry().with_resource(schema["$id"].replace("record.schema.json", "manifest-v2.schema.json"), resource)
    errors = list(jsonschema.Draft202012Validator(schema, registry=registry).iter_errors(record))
    check(not errors, f"record fails schemas/record.schema.json: {[error.message[:120] for error in errors[:3]]}")
    return "full (jsonschema, with schemas/manifest-v2.schema.json)"


def check_record(page):
    check(not page.nesting_errors, f"HTML nesting: {page.nesting_errors[:3]}")
    text = "".join(page.record_text)
    if not check(bool(text), "no character-record"):
        return None
    check("<" not in text, "a raw < in the record (§11 writes it \\u003c)")
    record = json.loads(text)
    how = check_record_shape(record)
    manifest = record["manifest"]
    check(not any(asset["kind"] == "dossier" for asset in manifest["assets"]), "the embedded manifest lists the page")
    check(not any(entry["path"].endswith("-dossier.html") for entry in manifest["files"]), "the embedded manifest lists the page's file")
    check(manifest["updatedAt"] == max(asset["createdAt"] for asset in manifest["assets"]),
          "embedded updatedAt isn't the latest createdAt")
    checksum = hashlib.sha256("".join(sorted(entry["sha256"] for entry in manifest["files"])).encode()).hexdigest()
    check(manifest["manifestChecksum"] == checksum, "embedded manifestChecksum doesn't match its files (§5.3)")
    return how


def jpeg_size(data):
    position = 2
    while position < len(data):
        marker = data[position + 1]
        length = struct.unpack(">H", data[position + 2:position + 4])[0]
        if marker in (0xC0, 0xC1, 0xC2):
            height, width = struct.unpack(">HH", data[position + 5:position + 9])
            return width, height
        position += 2 + length
    return None


def asset_kind(field):
    source = field.get("source", {})
    return source.get("kind")


def check_media(page, fields):
    """Images are JPEG page copies at the sizes in page-copies.json; audio is a data: URI."""
    sizes = json.loads((TEMPLATE / "page-copies.json").read_text(encoding="utf-8"))["sizes"]
    wanted = {}
    for field in fields["page"]["before"] + [f for t in fields["tabs"] for f in t["fields"]]:
        for candidate in [field] + field.get("items", []):
            if asset_kind(candidate) in sizes:
                wanted[candidate["key"]] = sizes[asset_kind(candidate)]
    keys = []
    count = 0
    for tag, attrs, _ in page.elements:
        if "data-key" in attrs:
            keys.append((attrs["data-key"], attrs))
        if tag == "img":
            count += 1
            src = attrs.get("src", "")
            if not check(src.startswith("data:image/jpeg;base64,"), f"an image isn't a JPEG data: URI: {src[:40]}"):
                continue
            owner = keys[-1][0]
            if owner in wanted:
                size = jpeg_size(base64.b64decode(src.split(",", 1)[1]))
                check(size == (wanted[owner]["width"], wanted[owner]["height"]), f"{owner}: image is {size}")
                check(attrs.get("width") == str(wanted[owner]["width"]), f"{owner}: width attribute")
        if tag == "audio":
            check(attrs.get("src", "").startswith("data:audio/"), "an audio element isn't a data: URI")
            check("autoplay" not in attrs, "autoplay (DF-50)")
    return count


def check_page(path, version):
    text = path.read_text(encoding="utf-8")
    page = parse(text)
    fields = json.loads((ROOT / "data/fields.json").read_text(encoding="utf-8"))

    external = external_references(page)
    check(not external, f"W-PAGE-EXTERNAL: {external[:5]}")
    keys = check_keys(page, fields)
    check_tabs(page, fields)
    check_sources(page, fields)
    how = check_record(page)
    images = check_media(page, fields)

    metas = [attrs.get("content") for tag, attrs, _ in page.elements if tag == "meta" and attrs.get("name") == "dossier-template"]
    check(metas == [f"{version['version']} {version['sha256']}"], f"dossier-template meta is {metas}")
    for name, chunks in (("fonts.css", page.styles), ("dossier.css", page.styles)):
        check((TEMPLATE / name).read_text(encoding="utf-8") in chunks, f"the page doesn't carry template/{name} as it is")
    check((TEMPLATE / "dossier.js").read_text(encoding="utf-8") in page.scripts, "the page doesn't carry template/dossier.js as it is")
    check("{{" not in "".join(page.markup_text), "a placeholder was left in the page's text")
    for tag, attrs, _ in page.elements:
        check(not any(value and "{{" in value for value in attrs.values()), f"a placeholder was left in <{tag}>")
    size = path.stat().st_size
    check(size <= 10_000_000, f"W-PAGE-SIZE: {size} bytes")
    return {"keys": keys, "images": images, "record": how, "bytes": size}


def check_template_files():
    skeleton = (TEMPLATE / "skeleton.html").read_text(encoding="utf-8")
    placeholders = set(re.findall(r"\{\{([^{}]+)\}\}", skeleton))
    check(placeholders == SKELETON_PLACEHOLDERS, f"skeleton placeholders differ: {sorted(placeholders ^ SKELETON_PLACEHOLDERS)}")
    script = (TEMPLATE / "dossier.js").read_text(encoding="utf-8")
    check("</script" not in script.lower(), "dossier.js can't sit inside a script element")
    for api in REQUEST_APIS:
        check(api not in script, f"dossier.js names a request API: {api}")
    for name in ("dossier.css", "fonts.css"):
        check("</style" not in (TEMPLATE / name).read_text(encoding="utf-8").lower(), f"{name} can't sit inside a style element")
    for directory in (TEMPLATE / "fonts").iterdir():
        if directory.is_dir():
            check((directory / "OFL.txt").is_file(), f"{directory.name}: no OFL.txt")
            check(any(directory.glob("*.woff2")), f"{directory.name}: no font")
    for command in (["build_template_css.py", "--check"], ["template_version.py", "--check"]):
        result = subprocess.run([sys.executable, str(ROOT / "tools" / command[0]), *command[1:]], capture_output=True, text=True)
        check(result.returncode == 0, result.stdout.strip() or result.stderr.strip())
        print(f"  {command[0]} --check: {result.stdout.strip()}")


def main():
    pages = [Path(arg) for arg in sys.argv[1:]] or sorted((TEMPLATE / "example").glob("*-dossier.html"))
    check(bool(pages), "no page to check")
    version = json.loads((TEMPLATE / "VERSION.json").read_text(encoding="utf-8"))
    print(f"template {version['version']} {version['sha256']}")
    check_template_files()
    tested = check_rule_against_fixtures()
    print(f"  W-PAGE-EXTERNAL rule against fixtures: {tested} pages")
    for path in pages:
        result = check_page(path, version)
        print(f"  {path.name}: {result['bytes']} bytes, {result['keys']} keys, {result['images']} images; record schema: {result['record']}")
    if failures:
        print(f"FAILED ({len(failures)}):")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print("ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
