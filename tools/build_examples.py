#!/usr/bin/env python3
"""Regenerate examples/ (the conformance fixtures) from nothing.

This builds test data. It is not a reader, writer, validator or renderer of
the format, and no implementation may treat it as one: it deliberately writes
broken bundles, and it hard-codes what each one should report. It fills
template/ for its own fixture pages, as far as those pages need and no further.

    python3 -m venv /tmp/df && /tmp/df/bin/pip install -r tools/requirements.txt
    /tmp/df/bin/python tools/build_examples.py

Everything is invented. No character, image, voice or line here comes from a
real production (AGENTS.md rule 1).
"""
import base64
import copy
import hashlib
import html as html_text
import io
import json
import os
import re
import shutil
import struct
import unicodedata
import uuid
import zipfile
from pathlib import Path

import yaml
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "examples"
SILENCE = (ROOT / "tools/assets/silence.m4a").read_bytes()

NOW = "2026-10-31T12:00:00Z"
MADE = "2026-10-31T11:00:00Z"
ART = "flat placeholder shapes"
TEMPLATE = ROOT / "template"
_VERSION = json.loads((TEMPLATE / "VERSION.json").read_text(encoding="utf-8"))
TEMPLATE_VERSION, TEMPLATE_SHA = _VERSION["version"], _VERSION["sha256"]
FIELDS = json.loads((ROOT / "data/fields.json").read_text(encoding="utf-8"))
TIERS = json.loads((ROOT / "data/tiers.json").read_text(encoding="utf-8"))
COPIES = json.loads((TEMPLATE / "page-copies.json").read_text(encoding="utf-8"))
FRAGMENTS = {chunk.split(" -->\n", 1)[0]: chunk.split(" -->\n", 1)[1].rstrip("\n")
             for chunk in re.split(r"^<!-- fragment: ", (TEMPLATE / "fragments.html").read_text(encoding="utf-8"), flags=re.M)[1:]}
FULL_SECTIONS = ("Logline", "Appearance", "Personality", "Backstory", "Arc", "Relationships", "Voice & Speech", "Pronunciation", "Wardrobe")
SHORT_SECTIONS = ("Logline", "Appearance", "Voice & Speech")
MODELS = ["Qwen3-TTS-12Hz-1.7B-Base-bf16", "Qwen3-TTS-12Hz-0.6B-Base-bf16"]
VOICE_PROMPT = "A clear, unhurried alto with a dry edge."
PELL = "PELL ARDEN"
FIXTURES = []
CODES = sorted(re.findall(r"^\| `([EW]-[A-Z0-9-]+)` \|", (ROOT / "docs/DOSSIER-FORMAT.md").read_text(encoding="utf-8"), re.M), key=len, reverse=True)


def sha(data):
    return hashlib.sha256(data).hexdigest()


# --- bytes -------------------------------------------------------------------

def png(width, height, seed, head=(50, 60, 80, 100)):
    """A flat image with a head-shaped ellipse. The colors come from `seed`."""
    digest = hashlib.sha256(seed.encode()).digest()
    image = Image.new("RGB", (width, height), tuple(digest[:3]))
    x, y, w, h = head
    ImageDraw.Draw(image).ellipse((x, y, x + w, y + h), fill=tuple(digest[3:6]))
    buffer = io.BytesIO()
    image.save(buffer, "PNG", optimize=False, compress_level=9)
    return buffer.getvalue()


def face_crop(portrait):
    """§8.5's worked example: face box (50, 60, 80, 100) in a 180×320 portrait."""
    image = Image.open(io.BytesIO(portrait)).crop((0, 20, 180, 200))
    buffer = io.BytesIO()
    image.save(buffer, "PNG", optimize=False, compress_level=9)
    return buffer.getvalue()


def jpeg_copy(data, size):
    """The template's rule 5: scale to cover and crop the centre."""
    image = Image.open(io.BytesIO(data)).convert("RGB")
    scale = max(size[0] / image.width, size[1] / image.height)
    width, height = size[0] / scale, size[1] / scale
    left, top = (image.width - width) / 2, (image.height - height) / 2
    image = image.resize(size, box=(left, top, left + width, top + height))
    buffer = io.BytesIO()
    image.save(buffer, "JPEG", quality=COPIES["quality"], optimize=False)
    return buffer.getvalue()


def vox(name, models=2):
    """A vox-format archive with placeholder embeddings: no usable voice."""
    embeddings = {}
    blobs = {}
    for model, size in list(zip(MODELS, ("1.7b", "0.6b")))[:models]:
        path = f"embeddings/qwen3-tts/{size}/clone-prompt.bin"
        embeddings[f"qwen3-tts-{size}"] = {"model": model, "engine": "qwen3-tts", "file": path, "format": "bin"}
        blobs[path] = hashlib.sha256((name + size).encode()).digest()
    manifest = {
        "vox_version": "0.4.0",
        "id": str(uuid.UUID(bytes=hashlib.md5(name.encode()).digest(), version=4)),
        "created": MADE,
        "voice": {"name": name, "description": VOICE_PROMPT},
        "embeddings": embeddings,
        "provenance": {"method": "synthesized", "license": "CC0-1.0", "notes": "Placeholder fixture; the embeddings are not usable."},
    }
    blobs["manifest.json"] = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_STORED) as archive:
        for path in sorted(blobs):
            info = zipfile.ZipInfo(path, (2026, 10, 31, 0, 0, 0))
            archive.writestr(info, blobs[path])
    return buffer.getvalue()


def front_matter(fields):
    return "---\n" + yaml.safe_dump(fields, sort_keys=False, allow_unicode=True) + "---\n"


def short_description(name, role=None, art=ART, extra=""):
    fields = {"type": "character", "character": name}
    if role:
        fields["role"] = role
    fields["artStyle"] = art
    return (front_matter(fields) + f"""
## Logline

{name} is an invented character who exists only in these fixtures.[^a-fixture]

## Appearance

Tall, grey-eyed, with a long grey coat and no jewelry.[^a-fixture]

## Voice & Speech

Unhurried, dry, and exact about small things.[^a-fixture]
{extra}
[^a-fixture]: Author. Invented for the dossier-format fixtures, 2026-10-31.
""").encode()


def full_description(name, role):
    fields = {
        "type": "character", "character": name, "role": role,
        "aliases": ["WREN", "MISS HALLOWAY"],
        "age": "39", "pronouns": "she/her", "occupation": "Radio operator",
        "languages": ["en-US"], "artStyle": ART,
        "sampleLine": "Say it once, say it slowly, and I'll write it down.",
        "draft": {"generatedBy": "fixture", "generatedAt": "2026-10-31", "sources": ["episodes/fixture.fountain"],
                  "reviewedAt": "2026-10-31", "generated": []},
        "unknownKeyIsPreserved": "yes",
    }
    return (front_matter(fields) + f"""
## Logline

A lighthouse keeper's daughter runs the last radio station on the coast.[^e1-12]

## Appearance

Tall and spare, grey eyes, a long grey coat, no jewelry, no glasses.[^e1-12]

## Personality

Patient with machines and short with people who hurry them.[^inf-patience]

## Backstory

Learned code from her father during the long winters.[^a-backstory]

## Arc (Season 1)

From keeping the station alive to choosing who may use it.[^a-backstory]

## Relationships

Trades weather reports with **THE LAMPLIGHTER**, whom she has never met.[^e1-12]

## Voice & Speech

Unhurried, dry, and exact about small things.[^inf-patience]

## Pronunciation

Halloway: HAL-oh-way.[^a-backstory]

## Wardrobe

The grey coat, always.[^e1-12]

## Canon & Guardrails

She never leaves the station during a storm.[^a-backstory]

## Open Questions

### Needed before Portrait / Views

### Optional

- What the station's call sign is.

[^e1-12]: Stated. episodes/fixture.fountain:12.
[^inf-patience]: Inferred. She repairs the transmitter twice without comment.
[^a-backstory]: Author. Invented for the dossier-format fixtures, 2026-10-31.
""").encode()


# --- bundles -----------------------------------------------------------------

def checksum(entries):
    return sha("".join(sorted(entry["sha256"] for entry in entries)).encode())


class Bundle:
    def __init__(self, name, role=None, dirname=None, parent="characters"):
        self.name = name
        self.role = role
        self.dir = f"{parent}/{dirname or name + '.dossier'}"
        self.files = {}
        self.assets = []
        self.prompts = None
        self.extra_top = {}
        self.disk = {}       # bytes on disk that differ from what the manifest records
        self.missing = set()  # recorded in the manifest, never written
        self.loose = {}      # on disk, never recorded
        self.mutate = None
        self.manifest_bytes = b""   # replaces manifest.json; set, with no_manifest, to break it
        self.no_manifest = False
        self.links = {}      # symlinks: path to target

    def put(self, path, data, kind=None, status="selected", variant=None, provenance=None, created=MADE, **extra):
        self.files[path] = data
        if kind:
            asset = {"path": path, "kind": kind, "status": status, "createdAt": created,
                     "provenance": provenance or {"provider": "manual"}}
            if variant:
                asset["variant"] = variant
            asset.update(extra)
            self.assets.append(asset)
        return path

    def image(self, kind, data, variant=None, status="selected", provenance=None, **extra):
        stem = kind + (f"-{variant}" if variant else "")
        prov = {"provider": "vinetas", "engine": "fixture", "artStyle": ART}
        prov.update(provenance or {})
        return self.put(f"images/{stem}-{sha(data)[:8]}.png", data, kind, status, variant, prov, **extra)

    def selected(self, kind, variant=None):
        for asset in self.assets:
            if asset["kind"] == kind and asset.get("variant") == variant and asset["status"] == "selected":
                return asset
        raise KeyError((kind, variant))

    def input(self, role, kind=None):
        asset = self.selected(kind or role)
        return {"role": role, "path": asset["path"], "sha256": sha(self.files[asset["path"]])}

    def entries(self, without=()):
        return [{"path": path, "sha256": sha(self.files[path]), "sizeBytes": len(self.files[path])}
                for path in sorted(self.files, key=lambda p: p.encode()) if path not in without]

    def manifest(self):
        top = {"manifestVersion": 2, "character": self.name, "updatedAt": NOW,
               "generator": {"name": "dossier-format fixtures", "version": "1"},
               "files": self.entries(), "assets": sorted(self.assets, key=lambda a: a["path"].encode())}
        top["manifestChecksum"] = checksum(top["files"])
        if self.role:
            top["role"] = self.role
        if self.prompts:
            top["prompts"] = self.prompts
        top.update(self.extra_top)
        if self.mutate:
            self.mutate(top)
        return top

    def page(self, member, body_extra="", padding=0, template_sha=TEMPLATE_SHA, findings=()):
        """The template, filled for this bundle. `body_extra` and `padding` add the faults page fixtures test.

        `findings` is what the banner lists. This isn't a validator, so a fixture says what its
        bundle has without the page; none has anything yet, as every page fault is in the page.
        """
        path = f"{self.name}-dossier.html"
        description = self.selected("description")
        embedded = {"manifestVersion": 2, "character": self.name,
                    "updatedAt": max(a["createdAt"] for a in self.assets),
                    "generator": {"name": "dossier-format fixtures", "version": "1"},
                    "files": self.entries(), "assets": sorted(self.assets, key=lambda a: a["path"].encode())}
        embedded["manifestChecksum"] = checksum(embedded["files"])
        if self.role:
            embedded["role"] = self.role
        if self.prompts:
            embedded["prompts"] = self.prompts
        embedded.update(self.extra_top)
        text = self.files[description["path"]].decode()
        _, fm, body = text.split("---\n", 2)
        record = {"formatVersion": 2, "character": self.name, "castMember": normal_form(member),
                  "frontMatter": yaml.safe_load(fm), "body": body, "manifest": embedded}
        filled = FilledPage(self, record, findings).html(TEMPLATE_VERSION, template_sha)
        if body_extra:
            marker = '<script type="application/json" id="character-record">'
            assert filled.count(marker) == 1
            filled = filled.replace(marker, body_extra.lstrip("\n") + "\n" + marker)
        html = filled.encode()
        if padding:
            html += b"<!--" + b" " * (padding - len(html) - 8) + b"-->\n"
        derived = [self.input("description"),
                   {"role": "castMember", "sha256": sha(canonical_json(normal_form(member)).encode())},
                   {"role": "bundle", "sha256": embedded["manifestChecksum"]},
                   {"role": "template", "version": TEMPLATE_VERSION, "sha256": template_sha}]
        self.put(path, html, "dossier", provenance={"provider": "dossier-format fixtures", "notes": "Filled from template/ by tools/build_examples.py."}, created=NOW, derivedFrom=derived)

    def write(self, project):
        root = project / self.dir
        root.mkdir(parents=True)
        for path, data in {**self.files, **self.disk, **self.loose}.items():
            if path in self.missing:
                continue
            target = root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        for path, link in self.links.items():
            target = root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            os.symlink(link, target)
        if self.no_manifest:
            return
        if self.manifest_bytes:
            (root / "manifest.json").write_bytes(self.manifest_bytes)
            return
        (root / "manifest.json").write_text(json.dumps(self.manifest(), indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def member(bundle, role=None, voice=None, prompt=None, language=None):
    entry = {"character": bundle.name}
    if role or bundle.role:
        entry["role"] = role or bundle.role
    if language:
        entry["language"] = language
    if prompt:
        entry["voicePrompt"] = prompt
    entry["voices"] = {"voxalta": [voice]} if voice else {}
    entry["manifest"] = f"{bundle.dir}/manifest.json"
    return entry


def normal_form(entry):
    """§7: what a member's hash is taken over."""
    entry = copy.deepcopy(entry)
    legacy = entry.pop("voiceDescription", None)
    if entry.get("voicePrompt") is None and legacy is not None:
        entry["voicePrompt"] = legacy
    voices = {}
    for provider, value in (entry.get("voices") or {}).items():
        if isinstance(value, str):
            voices[provider.lower()] = [value]
        elif isinstance(value, list) and all(isinstance(item, str) for item in value):
            voices[provider.lower()] = value
    entry["voices"] = voices
    for key in ("character", "role", "actor", "gender", "language", "voicePrompt", "manifest"):
        if key in entry and entry[key] is None:
            del entry[key]
    return entry


def canonical_json(value):
    """§7."""
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


# --- the page ----------------------------------------------------------------

def substitute(text, values):
    """template/README.md: one pass, left to right; replacement text isn't scanned again."""
    return re.sub(r"\{\{([^{}]+)\}\}", lambda match: values[match.group(1)], text)


def fragment(name, **values):
    return substitute(FRAGMENTS[name], values)


def esc(text):
    return html_text.escape(str(text), quote=True)


def plain(value):
    """A value as text: lists joined by ', ', and empty as None."""
    if isinstance(value, list):
        value = ", ".join(str(item) for item in value)
    return None if value is None or value == "" else str(value)


class FilledPage:
    """data/fields.json walked over one bundle, as template/README.md says, for these fixtures' pages."""

    def __init__(self, bundle, record, findings):
        self.bundle = bundle
        self.record = record
        self.findings = findings
        self.front = record["frontMatter"]
        self.member = record["castMember"] or {}
        self.assets = record["manifest"]["assets"]
        body = record["body"]
        self.notes = dict(re.findall(r"^\[\^([^\]]+)\]: *(.*)$", body, re.M))
        body = re.sub(r"^\[\^[^\]]+\]:.*$", "", body, flags=re.M)
        self.sections = []  # (heading, lines)
        for line in body.split("\n"):
            if line.startswith("## "):
                self.sections.append((line[3:].strip(), []))
            elif self.sections:
                self.sections[-1][1].append(line)
        # Field rule 2: cited ones in citation order, then the rest in file order. `notes` keeps file order.
        referenced = list(dict.fromkeys(re.findall(r"\[\^([^\]]+)\]", body)))
        self.cited = [label for label in referenced if label in self.notes]
        self.cited += [label for label in self.notes if label not in referenced]

    # What's selected, and what a row asks (§8.1, §8.3).

    def selected(self, kind, variant=None):
        return next((a for a in self.assets if a["kind"] == kind and a.get("variant") == variant and a["status"] == "selected"), None)

    def matching(self, section):
        """§9.2's rule: the name, optionally with a space and a parenthetical."""
        return [(h, lines) for h, lines in self.sections if h == section or (h.startswith(section + " (") and h.endswith(")"))]

    def satisfied(self, row):
        name = row["id"]
        if name == "dossier":
            return True  # This page is that asset, and the embedded manifest leaves it out (§11).
        if row["type"] == "asset":
            return all(self.selected(row["kind"], v) for v in row["variants"]) if row.get("variants") else bool(self.selected(row["kind"]))
        vox = self.selected("vox")
        models = vox["provenance"].get("models", []) if vox else []
        samples = [a for a in self.assets if a["kind"] == "voiceSample" and a["status"] == "selected"]
        if name in ("description.full", "description.short"):
            wanted = FULL_SECTIONS if name.endswith("full") else SHORT_SECTIONS
            return bool(self.selected("description")) and all(self.matching(s) for s in wanted)
        if name == "voicePrompt":
            return bool(self.member.get("voicePrompt"))
        if name.startswith("vox."):
            return any(name[4:] in m.lower() for m in models)
        if name.startswith("sample.neutral."):
            return any(a["variant"] == "neutral" and a["model"] == name[15:] for a in samples)
        if name == "sample.range":
            return sum(a["variant"] != "neutral" for a in samples) >= 3
        if name == "pronunciation":
            return any("".join(lines).strip() for _, lines in self.matching("Pronunciation"))
        if name == "training.withLora":
            return not self.selected("lora") or any(a["kind"] == "training" for a in self.assets)
        raise KeyError(name)

    def required_rows(self):
        role = self.member.get("role")
        return [row for row in TIERS["rows"] if row["levels"][role] == "required"] if role else None

    # Values.

    def asset_value(self, asset, name):
        if name.startswith("provenance."):
            return asset["provenance"].get(name[11:])
        return {"path": asset["path"], "file": asset["path"].rsplit("/", 1)[-1], "date": asset["createdAt"][:10],
                "variant": asset.get("variant"), "model": asset.get("model"), "sampleText": asset.get("sampleText")}[name]

    def front_value(self, dotted):
        value = self.front
        for key in dotted.split("."):
            value = value.get(key) if isinstance(value, dict) else None
        return value

    def part(self, part, asset=None):
        if "literal" in part:
            return part["literal"]
        if "whenPresent" in part:
            return part["whenPresent"] if self.asset_value(asset, part["value"]) is not None else part["whenAbsent"]
        if "derivedFrom" in part:
            record = next((r for r in asset.get("derivedFrom", []) if r["role"] == part["derivedFrom"]), None)
            value = record["path"].rsplit("/", 1)[-1] if record else None
        elif "frontMatter" in part or part.get("from") == "frontMatter":
            value = self.front_value(part.get("frontMatter") or part["key"])
        else:
            value = self.asset_value(asset, part["value"])
        value = plain(value)
        return part.get("prefix", "") + value if value is not None else None

    def joined(self, parts, separator, asset=None):
        return separator.join(p for p in (self.part(part, asset) for part in parts) if p is not None) or None

    def source_asset(self, source):
        return self.selected(source["kind"], source.get("variant"))

    def raw(self, source):
        """What a text, list or plain long-text field holds. None when it's empty."""
        origin = source["from"]
        if origin == "record":
            return self.record.get(source["key"])
        if origin == "frontMatter":
            return self.front.get(source["key"])
        if origin == "castMember":
            return self.member.get(source["key"])
        if origin == "asset":
            asset = self.source_asset(source)
            return self.asset_value(asset, source["value"]) if asset else None
        if origin == "join":
            return self.joined(source["parts"], source["separator"])
        if origin == "provenance":
            lines = [self.joined(source["parts"], " · ", a) for a in self.assets if a["kind"] in source["kinds"] and a["status"] == "selected"]
            return "; ".join(line for line in lines if line) or None
        if origin == "tiers":
            rows = self.required_rows()
            if rows is None:
                return None
            if source["show"] == "count":
                return f"{sum(self.satisfied(row) for row in rows)}/{len(rows)}"
            return [row["label"] for row in rows if not self.satisfied(row)] or None
        if origin == "findings":
            return list(self.findings) or None
        if origin == "footnotes":
            return [self.notes[label] for label in self.cited] or None
        raise KeyError(origin)

    # Markdown: the template's rule 3.

    def inline(self, text):
        text = esc(text)
        text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
        text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
        def mark(match):
            # Field rule 2: a mark with no definition stays as plain text.
            return fragment("mark", number=str(self.cited.index(match.group(1)) + 1)) if match.group(1) in self.notes else match.group(0)
        return re.sub(r"\[\^([^\]]+)\]", mark, text)

    @staticmethod
    def blocks(lines):
        """(kind, text) for each heading, list item and paragraph."""
        found = []
        paragraph = []

        def flush():
            if paragraph:
                found.append(("p", "\n".join(paragraph)))
                paragraph.clear()
        for line in lines:
            if line.startswith("### "):
                flush()
                found.append(("h4", line[4:].strip()))
            elif line.startswith("- "):
                flush()
                found.append(("li", line[2:].strip()))
            elif line.strip():
                paragraph.append(line.strip())
            else:
                flush()
        flush()
        return found

    def markdown(self, lines):
        out = []
        in_list = False
        for kind, text in self.blocks(lines):
            if kind == "li" and not in_list:
                out.append("<ul>")
            if kind != "li" and in_list:
                out.append("</ul>")
            in_list = kind == "li"
            out.append(f"<{kind}>{self.inline(text)}</{kind}>")
        if in_list:
            out.append("</ul>")
        return "".join(out)

    def section_markup(self, section):
        """Every matching heading, in body order, its parenthetical above its body."""
        out = []
        matched = self.matching(section)
        if not any("".join(lines).strip() for _, lines in matched):
            return None
        for heading, lines in matched:
            if heading != section:
                out.append(fragment("parenthetical", text=esc(heading[len(section):].strip())))
            out.append(self.markdown(lines))
        return "".join(out)

    def canon_items(self, source):
        items = []
        for _, lines in self.matching(source["section"]):
            for kind, text in self.blocks(lines):
                if kind in ("p", "li"):
                    classes = [self.notes[label].split(".", 1)[0] for label in re.findall(r"\[\^([^\]]+)\]", text) if label in self.notes]
                    items.append(fragment("canonItem", text=self.inline(text), source=esc(", ".join(classes))))
        return "".join(items) or None

    # Stamping (template/README.md).

    def media(self, asset, kind):
        size = COPIES["sizes"][kind]
        data = jpeg_copy(self.bundle.files[asset["path"]], (size["width"], size["height"]))
        return f"data:image/jpeg;base64,{base64.b64encode(data).decode()}", size

    def img(self, label, source):
        asset = self.source_asset(source)
        if not asset:
            return None
        src, size = self.media(asset, source["kind"])
        return fragment("img", label=esc(label), src=src, width=str(size["width"]), height=str(size["height"]))

    def overlay(self, field):
        source = field["overlay"]["source"]
        face = self.source_asset(source)
        box = self.asset_value(face, source["value"]) if face else None
        portrait = self.source_asset(field["source"])
        if not box or not portrait:
            return ""
        width, height = Image.open(io.BytesIO(self.bundle.files[portrait["path"]])).size
        half_up = lambda value: int(value + 0.5)  # Every value here is positive (§8.5).
        side = half_up(min(1.8 * max(box["width"], box["height"]), width, height))
        left = half_up(min(max(box["x"] + box["width"] / 2 - side / 2, 0), width - side))
        top = half_up(min(max(box["y"] + box["height"] / 2 - side / 2, 0), height - side))
        decimal = lambda value: f"{value:.4f}".rstrip("0").rstrip(".")
        return fragment("overlay", left=decimal(100 * left / width), top=decimal(100 * top / height), size=decimal(100 * side / width))

    def stamp(self, field):
        kind = field["kind"]
        empty = esc(field["emptyText"]) if field.get("emptyText") else ""
        common = {"key": field["key"], "kind": kind, "label": esc(field["label"]), "labelStyle": field.get("labelStyle", "label"),
                  "labelHidden": "" if field.get("labelVisible", True) else " is-hidden", "textStyle": field.get("textStyle", "body")}

        def state(value):
            return "filled" if value is not None else ("absent" if field.get("emptyText") is None else "empty")
        if kind == "image":
            value = self.img(field["label"], field["source"])
            caption = ""
            if value is not None:
                if "overlay" in field:
                    value += self.overlay(field)
                if "caption" in field:
                    text = self.joined(field["caption"]["parts"], field["caption"]["separator"], self.source_asset(field["source"]))
                    caption = fragment("caption", text=esc(text)) if text else ""
            shown = value if value is not None else (fragment("imageMissing", text=empty) if empty else "")
            return fragment("image", **common, state=state(value), value=shown, caption=caption)
        if kind == "imageSet":
            items = []
            for item in field["items"]:
                value = self.img(item["label"], item["source"])
                note = fragment("itemNote", text=esc(item["note"])) if item.get("note") else ""
                items.append(fragment("imageItem", key=item["key"], label=esc(item["label"]), state="filled" if value is not None else "empty",
                                      value=value if value is not None else fragment("imageMissing", text=esc(item["emptyText"])), note=note))
            return fragment("imageSet", **common, state="filled", items="".join(items))
        if kind == "audio":
            value = self.audio_rows(field)
            shown = value if value is not None else fragment("audioEmpty", text=empty)
            return fragment("audio", **common, state=state(value), value=shown)
        source = field["source"]
        if kind == "longText":
            if source["from"] == "section":
                value = self.section_markup(source["section"])
            else:
                text = plain(self.raw(source))
                value = f"<p>{esc(text)}</p>" if text is not None else None
        elif kind == "list":
            if source["from"] == "section":
                items = self.canon_items(source)
            else:
                raw = self.raw(source)
                items = "".join(fragment("listItem", text=esc(item)) for item in raw) if raw else None
            value = fragment("list", items=items) if items else None
        else:
            text = plain(self.raw(source))
            wrap = field.get("wrap", ("", ""))
            value = esc(wrap[0] + text + wrap[1]) if text is not None else None
        return fragment("field", **common, state=state(value), value=value if value is not None else empty)

    def audio_rows(self, field):
        samples = [a for a in self.assets if a["kind"] == field["source"]["kind"] and a["status"] == "selected"]
        samples.sort(key=lambda a: a.get("variant") != "neutral")  # Stable: otherwise the manifest's order.
        row = field["row"]
        rows = []
        for asset in samples:
            note = self.joined(row["note"]["parts"], row["note"]["separator"], asset)
            data = base64.b64encode(self.bundle.files[asset["path"]]).decode()
            rows.append(fragment("audioRow", title=esc(self.asset_value(asset, row["title"])), note=esc("· " + (note or "")),
                                 src=f"data:audio/mp4;base64,{data}", text=esc(self.asset_value(asset, row["text"]))))
        return "".join(rows) or None

    def stamp_fields(self, fields):
        out = []
        index = 0
        while index < len(fields):
            group = fields[index].get("group")
            end = index + 1
            while group and end < len(fields) and fields[end].get("group") == group:
                end += 1
            stamped = "".join(self.stamp(field) for field in fields[index:end])
            out.append(fragment("group", group=group, fields=stamped) if group else stamped)
            index = end
        return "".join(out)

    def html(self, version, template_sha):
        languages = self.front.get("languages") or ["und"]
        include = lambda name: (TEMPLATE / name).read_text(encoding="utf-8")
        return substitute(include("skeleton.html"), {
            "lang": esc(languages[0]), "character": esc(self.record["character"]),
            "template.version": esc(version), "template.sha256": esc(template_sha),
            "include:fonts.css": include("fonts.css"), "include:dossier.css": include("dossier.css"), "include:dossier.js": include("dossier.js"),
            "page.before": "".join(self.stamp(field) for field in FIELDS["page"]["before"]),
            "tab.links": "".join(fragment("tabLink", key=tab["key"], label=esc(tab["label"])) for tab in FIELDS["tabs"]),
            "tab.panels": "\n".join(fragment("tab", key=tab["key"], label=esc(tab["label"]), fields=self.stamp_fields(tab["fields"])) for tab in FIELDS["tabs"]),
            "page.after": "".join(self.stamp(field) for field in FIELDS["page"]["after"]),
            "record": canonical_json(self.record).replace("<", "\\u003c"),
        })


def code_for(name):
    return next(code for code in CODES if name == code or name.startswith(code + "-"))


def fixture(group, name, bundles, members, codes=(), may_also=(), complete=None, missing=None, note="", cast_text=None, bundle_path=None, update_status=None):
    project = OUT / group / name
    project.mkdir(parents=True)
    cast = cast_text or front_matter({"type": "cast", "schemaVersion": 1, "cast": members}) + "# Cast\n\nSynthetic data only.\n"
    (project / "CAST.md").write_text(cast, encoding="utf-8")
    for bundle in bundles:
        bundle.write(project)
    entry = {"path": f"{group}/{name}", "bundle": bundle_path or bundles[0].dir, "verdict": {"valid": "valid", "warnings": "warnings", "errors": "invalid"}[group],
             "codes": sorted(codes), "mayAlso": sorted(may_also)}
    if complete is not None:
        entry["complete"] = complete
        entry["missingRequired"] = missing or []
    if update_status is not None:
        entry["updateStatus"] = update_status
    if note:
        entry["note"] = note
    FIXTURES.append(entry)


# --- shared shapes -----------------------------------------------------------

def base(name=PELL, role="background", dirname=None, parent="characters", description=None):
    """A background character: nothing is required, so only the fault under test is reported."""
    b = Bundle(name, role, dirname, parent)
    b.put("CHARACTER.md", description or short_description(name, role), "description")
    portrait = png(180, 320, name + "portrait")
    b.image("portrait", portrait)
    b.image("face", face_crop(portrait), derivedFrom=[b.input("portrait")],
            provenance={"provider": "personaje", "box": {"x": 50, "y": 60, "width": 80, "height": 100}})
    return b


def add_voice(b, models=2):
    voice = f"voice/{b.name}.vox"
    b.put(voice, vox(b.name, models), "vox",
          provenance={"provider": "echada", "models": MODELS[:models], "voicePrompt": VOICE_PROMPT})
    return f"{b.dir}/{voice}"


def add_sample(b, variant, model, text, suffix=False):
    path = f"voice/sample-{variant}{'-' + model if suffix else ''}.m4a"
    b.put(path, SILENCE, "voiceSample", variant=variant, provenance={"provider": "diga", "instructApplied": "unverified", "source": "sampleLine"},
          derivedFrom=[b.input("vox")], model=model, language="en-US", sampleText=text)


def add_visuals(b):
    portrait = png(180, 320, b.name + "portrait")
    b.image("portrait", portrait, provenance={"seed": 7, "steps": 4, "width": 180, "height": 320, "round": "v1", "prompt": "A tall woman in a grey coat."})
    b.image("face", face_crop(portrait), derivedFrom=[b.input("portrait")],
            provenance={"provider": "personaje", "box": {"x": 50, "y": 60, "width": 80, "height": 100}})


# --- valid -------------------------------------------------------------------

def valid():
    # Everything the format has, in one bundle.
    name = "WREN HALLOWAY"
    b = Bundle(name, "lead")
    b.prompts = {"identity": "A tall woman, grey eyes, long grey coat, no jewelry, no glasses.", "portrait": "A tall woman in a grey coat.", "subject": "woman"}
    b.extra_top = {"unknownTopLevelKeyIsPreserved": {"kept": True}}
    b.put("CHARACTER.md", full_description(name, "lead"), "description", label="The description")
    add_visuals(b)
    derived = lambda: [b.input("portrait"), b.input("face")]
    for variant in ("front", "profile", "back"):
        b.image("view", png(180, 320, name + variant), variant, derivedFrom=derived(),
                provenance={"references": [{"sha256": sha(b.files[b.selected("portrait")["path"]]), "path": b.selected("portrait")["path"], "role": "portrait"}]})
    for variant in ("happy", "sad", "frightened", "mad"):
        b.image("expression", png(128, 128, name + variant, (30, 25, 68, 85)), variant, derivedFrom=[b.input("face"), b.input("portrait")],
                review={"passed": ["asked", "consistent"], "failed": [], "notes": "", "reviewedAt": "2026-10-31"})
    b.image("portrait", png(180, 320, name + "candidate"), status="candidate", unknownAssetKeyIsPreserved=1)
    b.image("portrait", png(180, 320, name + "rejected"), status="rejected")
    b.put("source/reference-sketch.png", png(90, 90, name + "source", (20, 20, 50, 50)), "sourcePhoto", provenance={"provider": "import"})
    b.put(f"lora/{name}-v1.safetensors", struct.pack("<Q", 2) + b"{}", "lora", provenance={"provider": "manual"},
          lora={"triggerWord": "wrenh", "baseModel": "fixture", "version": 1, "rank": 8, "steps": 1, "defaultScale": 0.8, "trainedAt": MADE, "compatibleEngines": ["fixture"]})
    b.put("training/wren-01.png", png(64, 64, name + "training", (10, 10, 40, 40)), "training", provenance={"provider": "manual"},
          training={"caption": "wrenh, a tall woman", "view": "front", "isSynthetic": True})
    voice = add_voice(b)
    add_sample(b, "neutral", "1.7b", "Say it once, say it slowly, and I'll write it down.")
    add_sample(b, "neutral", "0.6b", "Say it once, say it slowly, and I'll write it down.", suffix=True)
    add_sample(b, "wry", "1.7b", "The storm has been very punctual.")
    add_sample(b, "urgent", "1.7b", "Get off this frequency, now.")
    add_sample(b, "hushed", "1.7b", "Nobody out there is listening. Keep talking.")
    b.put("voice/samples.yaml", yaml.safe_dump([
        {"variant": "neutral", "text": "Say it once, say it slowly, and I'll write it down.", "source": "sampleLine"},
        {"variant": "wry", "text": "The storm has been very punctual.", "model": "1.7b", "language": "en-US",
         "instruct": "Dry.", "source": "episodes/fixture.fountain:30"},
    ], sort_keys=False, allow_unicode=True).encode())
    m = member(b, voice=voice, prompt=VOICE_PROMPT, language="en-US")
    b.page(m)
    b.loose[".hidden-note"] = b"Hidden files are not inventoried (5.2).\n"
    fixture("valid", "complete-lead", [b], [m, {"character": "COUNTER CLERK", "role": "background", "voices": {}}], complete=True,
            note="Every kind but crowdRef, a candidate, a rejected asset, unknown keys, a hidden file, and a member with no dossier.")

    # The short description, with both voice sizes.
    name = "THE LAMPLIGHTER"
    b = Bundle(name, "costar")
    b.put("CHARACTER.md", short_description(name, "costar"), "description")
    add_visuals(b)
    voice = add_voice(b)
    add_sample(b, "neutral", "1.7b", "The light goes on at dusk.")
    add_sample(b, "neutral", "0.6b", "The light goes on at dusk.", suffix=True)
    m = member(b, voice=voice, prompt=VOICE_PROMPT)
    b.page(m)
    fixture("valid", "complete-costar", [b], [m], complete=True)

    # A non-ASCII name in NFC, on the smallest voiced tier.
    name = "INÉS"
    b = Bundle(name, "underfive")
    b.put("CHARACTER.md", short_description(name, "underfive"), "description")
    voice = add_voice(b, models=1)
    add_sample(b, "neutral", "1.7b", "Por aquí.")
    m = member(b, voice=voice, prompt=VOICE_PROMPT, language="es-MX")
    b.page(m)
    fixture("valid", "non-ascii-underfive", [b], [m], complete=True, note="The castMember hash has a non-ASCII character and a '/': see §7's canonical JSON.")

    # The smallest valid bundle: no files at all.
    b = Bundle("BYSTANDER #2", "background")
    fixture("valid", "empty-background", [b], [member(b)], complete=True, note="No files and no assets; manifestChecksum is the SHA-256 of the empty string. A check reports C-NO-DESCRIPTION (§14), outside these results.")

    # Update markers (5.7), all judged at the same fixed time.
    def marker(expires_at):
        return json.dumps({"writer": "fixture-writer", "startedAt": "2026-10-19T16:55:00Z", "expiresAt": expires_at}, indent=2).encode() + b"\n"

    update_at = "2026-10-19T17:00:00Z"
    b = Bundle("BYSTANDER #3", "background")
    b.loose[".update-old.json"] = marker("2026-10-19T16:59:59Z")
    b.loose[".update-live.json"] = marker("2026-10-19T18:00:00Z")
    fixture("valid", "update-active", [b], [member(b)], complete=True, update_status={"at": update_at, "updating": True},
            note="One marker exactly at the 3600-second limit is enough, beside an expired one. A validator reports neither.")

    b = Bundle("BYSTANDER #4", "background")
    b.loose[".update-expired.json"] = marker("2026-10-19T17:00:00Z")
    b.loose[".update-too-far.json"] = marker("2026-10-19T18:00:01Z")
    b.loose[".update-offset.json"] = marker("2026-10-19T12:30:00+05:00")
    b.loose[".update-not-json.json"] = b"{ not json\n"
    b.loose[".update-not-object.json"] = b"[]\n"
    b.loose[".update-empty.json"] = b""
    b.loose[".update-temp.json.tmp"] = marker("2026-10-19T17:05:00Z")
    b.loose[".update-bad_id.json"] = marker("2026-10-19T17:05:00Z")
    fixture("valid", "update-not-active", [b], [member(b)], complete=True, update_status={"at": update_at, "updating": False},
            note="Expired, too far ahead, a time zone offset, unreadable, a zero-byte hidden file, and names that aren't markers: none counts, and a validator reports none.")

    # A hand-edited member: the hash is over its normal form (§7), so it isn't stale.
    b = base("THE FERRYMAN")
    voice = add_voice(b)
    m = {"character": b.name, "role": "background", "voiceDescription": VOICE_PROMPT, "voices": {"VoxAlta": voice}, "bio": None,
         "manifest": f"{b.dir}/manifest.json"}
    b.page(m)
    fixture("valid", "hand-edited-member", [b], [m], complete=True,
            note="A legacy voiceDescription, a scalar voices value, a mixed-case provider and an undeclared null. §7's normal form gives the hash.")

    # A pointer that isn't written the short way, but resolves to the bundle (§3).
    b = base("THE PILOT")
    fixture("valid", "pointer-not-normalized", [b], [{**member(b), "manifest": f"./characters/../{b.dir}/manifest.json"}], complete=True)

    # Just inside §8.1's tolerance.
    b = Bundle("THE COOPER", "background")
    b.put("CHARACTER.md", short_description(b.name, "background"), "description")
    b.image("portrait", png(179, 320, b.name))
    fixture("valid", "shape-within-tolerance", [b], [member(b)], complete=True, note="179×320: 0.56% from 9:16.")

    # Every kind of reference §11 allows, and things that look like references and aren't.
    b = base("THE CARTOGRAPHER")
    m = member(b)
    b.page(m, body_extra="""
<style>h1 { background: url(data:image/gif;base64,R0lGODlhAQABAAAAACw=); } h2 { mask: url(#shape); }</style>
<!-- <img src="comment.png"> is not a reference -->
<p style="background: URL('DATA:image/gif;base64,R0lGODlhAQABAAAAACw=')">src="text.png" is text.</p>
<img alt="one candidate with a comma" srcset="data:image/gif;base64,R0lGODlhAQABAAAAACw= 1x">
<a href="#sources">Sources</a> <a href="https://example.org/source">A cited source</a> <a href="mailto:author@example.org">The author</a>
<script>const notAReference = '<img src="script.png">';</script>""")
    fixture("valid", "page-allowed-references", [b], [m], complete=True)

    # voicePrompt: null doesn't hide the legacy key (§7).
    b = base("THE BELL RINGER")
    voice = add_voice(b)
    m = {"character": b.name, "role": "background", "voicePrompt": None, "voiceDescription": VOICE_PROMPT, "voices": {"voxalta": [voice]},
         "manifest": f"{b.dir}/manifest.json"}
    b.page(m)
    fixture("valid", "null-voice-prompt", [b], [m], complete=True)

    # How each YAML scalar is read (§7), and a multi-line value (the escapes). Hand-written YAML.
    b = base("THE ARCHIVIST")
    read = {"character": b.name, "role": "background", "actor": "5", "language": "no", "voices": {},
            "manifest": f"{b.dir}/manifest.json",
            "aFloat": "1.5", "anOctal": "0755", "aDate": "2026-08-01", "aYes": "yes", "aTrue": True, "aFalse": False,
            "anInt": 5, "aNegative": -5, "aZero": 0, "tooBig": "99999999999999999999", "leadingZero": "007", "plusSign": "+5",
            "aTilde": None, "anEmpty": None, "aNull": None, "quotedInt": "5", "quotedTrue": "true",
            "aList": [1, True, "x", None, "1.5"], "aMap": {"k": "1.5", "t": True},
            "aBlock": "line one\nline\ttwo \"quoted\" back\\slash\n"}
    b.page(read)
    raw = f"""---
type: cast
schemaVersion: 1
cast:
- character: {b.name}
  role: background
  actor: 5
  language: no
  voices: {{}}
  manifest: {b.dir}/manifest.json
  aFloat: 1.5
  anOctal: 0755
  aDate: 2026-08-01
  aYes: yes
  aTrue: True
  aFalse: FALSE
  anInt: 5
  aNegative: -5
  aZero: 0
  tooBig: 99999999999999999999
  leadingZero: 007
  plusSign: +5
  aTilde: ~
  anEmpty:
  aNull: NULL
  quotedInt: "5"
  quotedTrue: 'true'
  aList: [1, true, x, null, 1.5]
  aMap: {{k: 1.5, t: true}}
  aBlock: "line one\\nline\\ttwo \\"quoted\\" back\\\\slash\\n"
---
# Cast

Synthetic data only.
"""
    fixture("valid", "member-scalars", [b], [], complete=True, cast_text=raw,
            note="Read by §7's rules, the page's castMember input matches. Reading 1.5 as a number, 0755 as an octal or no as a boolean makes it stale.")

    # What W-STALE and W-ROLE don't report (§7, §14), and what isn't scanned or inventoried (§3, §5.2).
    b = Bundle("THE HARBORMASTER", "background")
    b.put("CHARACTER.md", short_description(b.name, "background"), "description")
    old = png(180, 320, b.name + "old")
    b.image("portrait", old, status="candidate")
    old_path = f"images/portrait-{sha(old)[:8]}.png"
    b.image("portrait", png(180, 320, b.name + "new"))
    del b.assets[-1]["provenance"]["artStyle"]
    b.image("view", png(180, 320, b.name + "view"), "front", status="candidate", derivedFrom=[{"role": "portrait", "path": old_path, "sha256": sha(old)}])
    b.image("portrait", png(180, 180, b.name + "square"), status="candidate")
    b.loose[".gitkeep"] = b""
    elsewhere = base("STORED AWAY", parent="characters/archive")
    fixture("valid", "not-reported", [b, elsewhere], [member(b), {"character": "a passerby (V.O.)", "voices": {}}], complete=True,
            note="A stale candidate; a wrong-shaped candidate; a selected image with no provenance.artStyle; a hidden zero-byte file; a member with no role, no dossier and a non-canonical name; a bundle below characters/, which isn't scanned.")

    # voices.voxalta has several paths, and the bundle's vox isn't the first or written the short way (§8.2).
    b = base("THE TUNER")
    voice = add_voice(b)
    fixture("valid", "voice-second-path", [b], [member(b, prompt=VOICE_PROMPT) | {"voices": {"voxalta": ["voices/other.vox", f"./{voice}"]}}], complete=True)

    # §5.2: a path compares with a name on disk as NFC strings. The manifest is NFC and the disk NFD.
    # Git on a Mac stores this name as NFC unless told otherwise: see examples/README.md.
    b = base("THE GLAZIER")
    nfc = "source/caf\u00e9-sketch.png"
    sketch = png(90, 90, b.name + "source", (20, 20, 50, 50))
    b.put(nfc, sketch, "sourcePhoto", provenance={"provider": "import"})
    b.missing.add(nfc)
    b.loose[unicodedata.normalize("NFD", nfc)] = sketch
    fixture("valid", "name-on-disk-nfd", [b], [member(b)], complete=True, note="The manifest's path is NFC and the file's name on disk is NFD. They compare equal (§5.2).")

    # §9.1, §3: no character key isn't a mismatch.
    b = base("THE CHANDLER", description=short_description("THE CHANDLER", "background").replace(b"character: THE CHANDLER\n", b""))
    fixture("valid", "description-no-character-key", [b], [member(b)], complete=True,
            note="CHARACTER.md has no character key, which isn't E-NAME-MISMATCH (§3). A check reports C-KEY-MISSING (§14), outside these results.")

    # Exactly at §11's limit.
    b = base("THE PORTER"); m = member(b); b.page(m, padding=10_000_000)
    fixture("valid", "page-at-size-limit", [b], [m], complete=True, note="10,000,000 bytes, nearly all of it a comment.")


# --- errors ------------------------------------------------------------------

def errors():
    def err(name, b=None, members=None, codes=None, may_also=(), note=""):
        b = b or base()
        fixture("errors", name, [b], members or [member(b)], codes or [code_for(name)], may_also, note=note)

    b = base(); b.mutate = lambda m: m.update(manifestVersion=3)
    err("E-VERSION", b, may_also=["E-SCHEMA"])

    b = base(); b.no_manifest = True
    err("E-MANIFEST-missing", b)
    b = base(); b.manifest_bytes = b"{ not json\n"
    err("E-MANIFEST-not-json", b)
    b = base(); b.manifest_bytes = b"[]\n"
    err("E-MANIFEST-not-object", b)

    b = base()
    fixture("errors", "E-CAST-unknown-role", [b], [], ["E-CAST"], cast_text=front_matter({"type": "cast", "schemaVersion": 1, "cast": [{**member(b), "role": "Lead"}]}))
    b = base()
    fixture("errors", "E-CAST-not-yaml", [b], [], ["E-CAST"], cast_text="---\ntype: cast\ncast: [unclosed\n---\n")
    b = base()
    fixture("errors", "E-CAST-voices-not-map", [b], [], ["E-CAST"], cast_text=front_matter({"type": "cast", "schemaVersion": 1, "cast": [{**member(b), "voices": "a.vox"}]}))

    b = base("pell arden")
    err("E-NAME-not-canonical", b, codes=["E-NAME"], note="Everything agrees, and the name isn't canonical.")
    b = base("INE\u0301S", dirname="IN\u00c9S.dossier")
    err("E-NAME-not-nfc", b, codes=["E-NAME"], note="The manifest and member are NFD and the directory NFC. They agree as NFC strings (§3), and the name isn't canonical.")

    b = base()
    fixture("errors", "E-CAST-no-character", [b], [], ["E-CAST"], cast_text=front_matter({"type": "cast", "schemaVersion": 1, "cast": [{"role": "background", "voices": {}}]}))
    b = base()
    fixture("errors", "E-CAST-unknown-gender", [b], [], ["E-CAST"], cast_text=front_matter({"type": "cast", "schemaVersion": 1, "cast": [{**member(b), "gender": "X"}]}))

    b = base("AC/DC", dirname="ACDC.dossier")
    err("E-NAME-slash", b, may_also=["E-NAME-MISMATCH", "E-SCHEMA"])
    b = base(".HIDDEN")
    err("E-NAME-leading-dot", b, may_also=["E-SCHEMA"])

    b = base(dirname="PELL.dossier")
    err("E-NAME-MISMATCH-directory", b, codes=["E-NAME-MISMATCH"])
    b = base()
    err("E-NAME-MISMATCH-member", b, members=[{**member(b), "character": "PELL"}], codes=["E-NAME-MISMATCH"])

    b = base()
    err("E-NAME-MISMATCH-case", b, members=[{**member(b), "character": "Pell Arden"}], codes=["E-NAME-MISMATCH"], note="Names compare exactly.")
    b = base(description=short_description("SOMEONE ELSE", "background"))
    err("E-NAME-MISMATCH-description", b, codes=["E-NAME-MISMATCH"])

    b = base(dirname=PELL)
    err("E-NOT-BUNDLE", b, note="A version 2 manifest in a directory with no .dossier extension.")

    def bad_path(path):
        def mutate(m):
            m["files"].append({"path": path, "sha256": "a" * 64, "sizeBytes": 1})
            m["files"].sort(key=lambda e: e["path"].encode())
            m["manifestChecksum"] = checksum(m["files"])
        return mutate
    b = base(); b.mutate = bad_path("../outside.txt")
    err("E-PATH-escape", b, may_also=["E-SCHEMA", "E-FILE-MISSING", "W-UNCLASSIFIED"])
    b = base(); b.mutate = bad_path("/tmp/outside.txt")
    err("E-PATH-absolute", b, may_also=["E-SCHEMA", "E-FILE-MISSING", "W-UNCLASSIFIED"])
    for label, path in (("backslash", "images\\outside.txt"), ("drive-letter", "C:/outside.txt"), ("url", "file:///tmp/outside.txt"), ("empty-segment", "images//outside.txt")):
        b = base(); b.mutate = bad_path(path)
        err(f"E-PATH-{label}", b, may_also=["E-SCHEMA", "E-FILE-MISSING", "W-UNCLASSIFIED"])
    b = base(); b.assets[-1]["provenance"]["references"] = [{"sha256": "a" * 64, "path": "../portrait.png", "role": "portrait"}]
    err("E-PATH-reference", b, may_also=["E-SCHEMA"])
    b = base(); b.mutate = lambda m: m["assets"].append({"path": "../outside.png", "kind": "sourcePhoto", "status": "candidate", "createdAt": MADE, "provenance": {"provider": "manual"}})
    err("E-PATH-asset-only", b, may_also=["E-SCHEMA", "E-ASSET-NO-FILE"])
    b = base(); b.assets[-1]["derivedFrom"][0]["path"] = "../portrait.png"
    err("E-PATH-derived-from", b, may_also=["E-SCHEMA"], note="A path outside files and assets.")

    b = base(); b.missing.add(b.selected("portrait")["path"])
    err("E-FILE-MISSING", b)

    # §5.2: neither a symlink nor manifest.json is in the inventory, so a files entry for one has no file.
    b = base(); b.put("linked-notes.txt", b.files["CHARACTER.md"]); b.missing.add("linked-notes.txt"); b.links["linked-notes.txt"] = "CHARACTER.md"
    err("E-FILE-MISSING-symlink", b, note="The entry's hash and size are the target's. A symlink isn't followed, and it isn't W-UNCLASSIFIED either.")

    def lists_manifest(m):
        m["files"].append({"path": "manifest.json", "sha256": "a" * 64, "sizeBytes": 1})
        m["files"].sort(key=lambda e: e["path"].encode())
        m["manifestChecksum"] = checksum(m["files"])
    b = base(); b.mutate = lists_manifest
    err("E-FILE-MISSING-manifest", b, note="A file can't hold its own hash, so this is never compared: only E-FILE-MISSING, not E-FILE-HASH.")

    b = base(); text = b.files["CHARACTER.md"]; b.disk["CHARACTER.md"] = text.replace(b"grey-eyed", b"gray-eyed")
    err("E-FILE-HASH", b, note="The same size, different bytes.")
    b = base(); b.disk["CHARACTER.md"] = b.files["CHARACTER.md"] + b"\n"
    err("E-FILE-HASH-size", b, note="The file grew by a byte.")

    b = base(); b.put("source/empty.png", b"", "sourcePhoto", provenance={"provider": "import"})
    err("E-ZERO-BYTE", b, may_also=["E-SCHEMA"])

    def wrong_size(m):
        m["files"][0]["sizeBytes"] += 1
    b = base(); b.mutate = wrong_size
    err("E-FILE-HASH-size-only", b, note="The hash is right and sizeBytes isn't.")

    b = base(); b.loose["notes.txt"] = b""
    err("E-ZERO-BYTE-not-listed", b, codes=["E-ZERO-BYTE"], may_also=["W-UNCLASSIFIED"], note="On disk and not in files: §5.2's inventory is of the disk.")

    b = base(); b.mutate = lambda m: m.update(manifestChecksum="0" * 64)
    err("E-CHECKSUM", b)

    def path_order(m):
        order = sha("".join(e["sha256"] for e in m["files"]).encode())
        assert order != m["manifestChecksum"], "this fixture needs path order to differ from hash order"
        m["manifestChecksum"] = order
    b = base(); b.mutate = path_order
    err("E-CHECKSUM-path-order", b, note="Version 1's algorithm in a version 2 manifest.")

    b = base(); b.mutate = lambda m: m["assets"].append({"path": "images/portrait-deadbeef.png", "kind": "portrait", "status": "candidate", "createdAt": MADE, "provenance": {"provider": "manual"}})
    err("E-ASSET-NO-FILE", b)

    b = base()
    def duplicate(m):
        m["assets"].append({**copy.deepcopy(m["assets"][0]), "label": "A second entry for the same file", "status": "candidate"})
    b.mutate = duplicate
    err("E-ASSET-DUPLICATE", b)

    b = base(); b.image("portrait", png(180, 320, "second selected"))
    err("E-MULTI-SELECTED", b, may_also=["W-STALE"])

    b = base(); b.put("images/wardrobe-00000000.png", png(90, 90, "wardrobe", (10, 10, 40, 40)), "wardrobe")
    err("E-KIND-RETIRED", b, may_also=["E-SCHEMA"])

    b = base(); b.mutate = lambda m: m.pop("updatedAt")
    err("E-SCHEMA", b)


# --- warnings ----------------------------------------------------------------

def warnings():
    def warn(name, b=None, members=None, codes=None, may_also=(), complete=True, missing=None, note="", extra=()):
        b = b or base()
        fixture("warnings", name, [b, *extra], members or [member(b)], codes or [code_for(name)], may_also, complete, missing, note)

    b = base(); b.put("notes.txt", b"Not an asset.\n")
    warn("W-UNCLASSIFIED", b)

    b = base(); b.loose["notes.txt"] = b"A tool put this here.\n"
    warn("W-UNCLASSIFIED-not-listed", b, note="On disk and not in files, as §5.6 allows.")

    # Each input role alone (§7). Everything else about each bundle is current.
    b = base(); b.image("expression", png(128, 128, "fixture happy", (30, 25, 68, 85)), "happy",
                        derivedFrom=[{**b.input("face"), "sha256": "0" * 64}, b.input("portrait")])
    warn("W-STALE-input-face", b, codes=["W-STALE"])
    b = base(); add_voice(b); add_sample(b, "neutral", "1.7b", "One line."); b.assets[-1]["derivedFrom"][0]["sha256"] = "0" * 64
    m = member(b, voice=f"{b.dir}/voice/{b.name}.vox", prompt=VOICE_PROMPT)
    warn("W-STALE-input-vox", b, members=[m], codes=["W-STALE"])
    b = base(); m = member(b); b.page(m); b.selected("dossier")["derivedFrom"][0]["sha256"] = "0" * 64
    warn("W-STALE-input-description", b, members=[m], codes=["W-STALE"])
    b = base(); m = member(b); b.page(m)
    warn("W-STALE-input-member", b, members=[{**m, "bio": "Changed after the page was rendered."}], codes=["W-STALE"])
    b = base(); m = member(b); b.page(m); b.selected("dossier")["derivedFrom"][2]["sha256"] = "0" * 64
    warn("W-STALE-input-bundle", b, members=[m], codes=["W-STALE"])

    # A portrait has been rejected and nothing replaces it.
    b = base(); b.selected("portrait")["status"] = "rejected"
    warn("W-STALE-no-selection", b, note="The face's portrait input has no current selection.")

    # The face was cut from a portrait that is no longer the selected one.
    b = Bundle(PELL, "background")
    b.put("CHARACTER.md", short_description(PELL, "background"), "description")
    old = png(180, 320, "old portrait")
    b.image("portrait", old, status="candidate")
    old_path = f"images/portrait-{sha(old)[:8]}.png"
    b.image("portrait", png(180, 320, "new portrait"))
    b.image("face", face_crop(old), derivedFrom=[{"role": "portrait", "path": old_path, "sha256": sha(old)}],
            provenance={"provider": "personaje", "box": {"x": 50, "y": 60, "width": 80, "height": 100}})
    warn("W-STALE", b)

    # §7: the portrait that was sent is no longer in the bundle, so the writer recorded the hash sent with the current selection's path.
    b = base(); gone = sha(png(180, 320, PELL + "a portrait that left the bundle"))
    current = b.selected("portrait")["path"]
    assert all(entry["sha256"] != gone for entry in b.entries())
    b.image("view", png(180, 320, PELL + "front"), "front", derivedFrom=[{"role": "portrait", "path": current, "sha256": gone}],
            provenance={"references": [{"sha256": gone, "path": current, "role": "portrait"}]})
    warn("W-STALE-input-left-bundle", b, codes=["W-STALE"], note="No asset has the input's hash, and path is the current selection's. The file at path doesn't have that hash.")

    b = base(description=short_description(PELL, "background", art="woodcut"))
    warn("W-STALE-art-style", b, note="The images' provenance.artStyle differs from the current front matter.")

    b = base(); m = member(b); b.page(m, template_sha=sha(b"an older template\n"))
    warn("W-STALE-template", b, members=[m], note="The page's template isn't the current one (conformance.json).")

    b = Bundle(PELL, "background")
    b.put("CHARACTER.md", short_description(PELL, "background"), "description")
    b.image("portrait", png(180, 180, "square portrait"))
    warn("W-SHAPE", b)
    b = Bundle(PELL, "background")
    b.put("CHARACTER.md", short_description(PELL, "background"), "description")
    b.image("portrait", png(178, 320, "narrow portrait"))
    warn("W-SHAPE-just-outside", b, note="178×320: 1.1% from 9:16.")

    b = base(); b.image("expression", png(128, 128, "wistful", (30, 25, 68, 85)), "wistful", derivedFrom=[b.input("face"), b.input("portrait")])
    warn("W-VARIANT-expression", b)
    b = base(); b.image("view", png(180, 320, "overhead"), "overhead", derivedFrom=[b.input("portrait"), b.input("face")])
    warn("W-VARIANT-view", b)

    b = base(); b.put(f"images/portrait-{sha(b.files[b.selected('portrait')['path']])[:8]}.json", b'{"seed": 7}\n')
    warn("W-SIDECAR", b, may_also=["W-UNCLASSIFIED"])

    b = base(parent="people"); stray = base("STRAY VISITOR", parent="people")
    warn("W-ORPHAN-beside-a-bundle", b, extra=[stray], codes=["W-ORPHAN"], note="Beside a pointed-at bundle, outside characters/.")
    b = base(); stray = base("STRAY VISITOR")
    warn("W-ORPHAN", b, extra=[stray], note="STRAY VISITOR is reported and not loaded.")

    b = base()
    warn("W-POINTER", b, members=[{**member(b), "manifest": f"characters/archive/{PELL}.dossier/manifest.json"}], codes=["W-POINTER", "W-ORPHAN"], complete=None,
         note="The pointer leads nowhere, so the member's bundle is an orphan and isn't loaded. Completeness isn't defined.")
    b = base()
    warn("W-POINTER-directory", b, members=[{**member(b), "manifest": b.dir}], codes=["W-POINTER", "W-ORPHAN"], complete=None, note="The pointer names the bundle, not its manifest.")
    fixture("warnings", "W-POINTER-nowhere", [], [{"character": PELL, "role": "background", "voices": {}, "manifest": f"characters/{PELL}.dossier/manifest.json"}],
            ["W-POINTER"], bundle_path=f"characters/{PELL}.dossier", note="The member points at a bundle that doesn't exist at all.")

    b = base(role=None)
    warn("W-ROLE", b, complete=None, note="No tier, so completeness isn't defined.")
    b = base(role=None); b.extra_top = {"role": "lead"}
    warn("W-ROLE-manifest-has-one", b, codes=["W-ROLE"], complete=None, note="The manifest's role is a copy and doesn't supply a tier, so no W-INCOMPLETE.")

    b = base(); voice = add_voice(b); add_sample(b, "neutral", "1.7b", "One line.")
    warn("W-VOICE-ELSEWHERE", b, members=[member(b, voice=f"voices/{PELL}.vox", prompt=VOICE_PROMPT)])
    b = base(); voice = add_voice(b)
    warn("W-VOICE-PROMPT", b, members=[member(b, voice=voice, prompt="A different prompt from the one the voice was made with.")])

    b = base(description=short_description(PELL, "background", extra="\nA claim with no definition.[^nowhere]\n"))
    warn("W-FOOTNOTE-undefined", b)
    b = base(description=short_description(PELL, "background") + b"[^unused]: Author. Nothing refers to this, 2026-10-31.\n")
    warn("W-FOOTNOTE-unused", b)
    b = base(description=short_description(PELL, "background", extra="\nA claim.[^cited] A claim with no definition.[^nowhere]\n")
             + b"[^cited]: Author. Cited, 2026-11-01.\n[^z-unused]: Author. Never cited, first in the file, 2026-11-01.\n[^a-unused]: Author. Never cited, second in the file, 2026-11-01.\n")
    m = member(b); b.page(m)
    warn("W-FOOTNOTE-on-page", b, members=[m], codes=["W-FOOTNOTE"],
         note="The page shows the cited footnote first, the two never cited after it in file order, and the undefined mark as plain text.")

    b = base(); m = member(b); b.page(m, padding=10_000_001)
    warn("W-PAGE-SIZE", b, members=[m], note="10,000,001 bytes, nearly all of it a comment, which git compresses.")
    b = base(); m = member(b); b.page(m, body_extra=f'\n<img alt="linked" src="{b.selected("face")["path"]}">')
    warn("W-PAGE-EXTERNAL", b, members=[m])
    for label, html in (("css-url", '<style>body { font-family: x; src: url("fonts/x.woff2"); }</style>'),
                        ("css-import", '<style>@import "site.css";</style>'),
                        ("style-attribute", '<p style="background: url(https://example.org/x.png)">Text.</p>'),
                        ("srcset", '<img alt="set" srcset="data:image/gif;base64,R0lGODlhAQABAAAAACw= 1x, big.png 2x">'),
                        ("link-element", '<link rel="stylesheet" href="https://example.org/site.css">'),
                        ("relative-link", '<a href="other-dossier.html">Another page</a>')):
        b = base(); m = member(b); b.page(m, body_extra="\n" + html)
        warn(f"W-PAGE-EXTERNAL-{label}", b, members=[m])

    name = "WREN HALLOWAY"
    b = Bundle(name, "lead")
    b.put("CHARACTER.md", full_description(name, "lead"), "description")
    warn("W-INCOMPLETE", b, complete=False, missing=["dossier", "expressions", "face", "portrait", "sample.neutral.0.6b", "sample.neutral.1.7b", "sample.range", "views", "voicePrompt", "vox.0.6b", "vox.1.7b"])

    # One check row each, against what §8.3 says satisfies it.
    b = Bundle(name, "lead")
    b.put("CHARACTER.md", short_description(name, "lead"), "description")
    warn("W-INCOMPLETE-short-on-a-lead", b, codes=["W-INCOMPLETE"], complete=False, missing=["description.full", "dossier", "expressions", "face", "portrait", "pronunciation", "sample.neutral.0.6b", "sample.neutral.1.7b", "sample.range", "views", "voicePrompt", "vox.0.6b", "vox.1.7b"])
    b = Bundle(name, "lead")
    b.put("CHARACTER.md", full_description(name, "lead").replace(b"Halloway: HAL-oh-way.[^a-backstory]\n", b""), "description")
    warn("W-INCOMPLETE-empty-pronunciation", b, codes=["W-INCOMPLETE"], complete=False, missing=["dossier", "expressions", "face", "portrait", "pronunciation", "sample.neutral.0.6b", "sample.neutral.1.7b", "sample.range", "views", "voicePrompt", "vox.0.6b", "vox.1.7b"])
    b = Bundle(name, "costar")
    b.put("CHARACTER.md", short_description(name, "costar").replace(b"## Voice & Speech", b"## Notes"), "description")
    warn("W-INCOMPLETE-no-voice-section", b, codes=["W-INCOMPLETE"], complete=False, missing=["description.short", "dossier", "face", "portrait", "sample.neutral.0.6b", "sample.neutral.1.7b", "voicePrompt", "vox.0.6b", "vox.1.7b"])
    b = base(); b.put(f"lora/{PELL}-v1.safetensors", struct.pack("<Q", 2) + b"{}", "lora", provenance={"provider": "manual"},
                      lora={"triggerWord": "pell", "baseModel": "fixture", "version": 1, "rank": 8, "steps": 1, "defaultScale": 0.8, "trainedAt": MADE, "compatibleEngines": ["fixture"]})
    warn("W-INCOMPLETE-lora-no-training", b, codes=["W-INCOMPLETE"], complete=False, missing=["training.withLora"])
    b = Bundle(name, "lead")
    b.put("CHARACTER.md", full_description(name, "lead"), "description")
    voice = add_voice(b)
    for variant, model, suffix in (("neutral", "1.7b", False), ("neutral", "0.6b", True), ("wry", "1.7b", False), ("urgent", "1.7b", False)):
        add_sample(b, variant, model, "One line.", suffix=suffix)
    warn("W-INCOMPLETE-two-range-samples", b, members=[member(b, voice=voice, prompt=VOICE_PROMPT)], codes=["W-INCOMPLETE"], complete=False,
         missing=["dossier", "expressions", "face", "portrait", "sample.range", "views"], note="Neutral reads don't count toward the range.")

    # Version 1, in both shapes Appendix A describes.
    def v1(dirname, second_selected=False):
        b = Bundle(PELL, "background", dirname)
        b.put("CHARACTER.md", short_description(PELL, "background"))
        b.put("images/portrait-v3-photo-s133.png", png(180, 320, "v1 portrait"))
        b.put("images/turnaround-front-s21.png", png(180, 320, "v1 front"))
        b.put("images/face.png", png(128, 128, "v1 face", (30, 25, 68, 85)))
        b.put("images/turnaround-front-s21.json", b'{"seed": 21}\n')
        if second_selected:
            b.put("images/portrait-v2-photo-s99.png", png(180, 320, "v1 second portrait"))
        def downgrade(m):
            m["manifestVersion"] = 1
            m["assets"] = [
                {"path": "CHARACTER.md", "kind": "description", "status": "selected"},
                {"path": "images/face.png", "kind": "faceSheet", "status": "selected"},
                {"path": "images/portrait-v3-photo-s133.png", "kind": "portrait", "status": "selected", "createdAt": MADE, "provenance": {"tool": "fixture", "references": []}},
                {"path": "images/turnaround-front-s21.png", "kind": "turnaround", "status": "selected", "label": "front"},
            ]
            if second_selected:
                m["assets"].append({"path": "images/portrait-v2-photo-s99.png", "kind": "portrait", "status": "selected", "createdAt": MADE, "provenance": {"tool": "fixture", "references": []}})
            order = sha("".join(e["sha256"] for e in m["files"]).encode())
            assert order != checksum(m["files"]), "the v1 fixture needs path order to differ from hash order"
            m["manifestChecksum"] = order
            del m["generator"]
        b.mutate = downgrade
        return b
    warn("W-V1", v1(None), may_also=["W-SIDECAR", "W-UNCLASSIFIED", "W-SHAPE"], complete=None,
         note="Version 1 contents in a .dossier directory; the checksum is in path order. Its turnaround and faceSheet aren't E-KIND-RETIRED.")
    warn("W-V1-plain-directory", v1(PELL), may_also=["W-SIDECAR", "W-UNCLASSIFIED", "W-SHAPE"], complete=None,
         note="Version 1 as first specified: no .dossier extension, and not E-NOT-BUNDLE.")
    warn("W-V1-two-selected", v1(None, second_selected=True), may_also=["W-SIDECAR", "W-UNCLASSIFIED", "W-SHAPE"], complete=None,
         note="Two selected portraits. E-MULTI-SELECTED applies only to version 2 (Appendix A).")


# --- data --------------------------------------------------------------------

NAMES = [
    ("Mitch", "MITCH"), ("@McCowley", "MCCOWLEY"), ("BILLY (V.O.)", "BILLY"), ("BILLY (CONT'D) (O.S.)", "BILLY"),
    ("Aunt   Stanley", "AUNT STANLEY"), ("mccowley's wife", "MCCOWLEY'S WIFE"), ("CB#1", "CB#1"), ("josé", "JOSÉ"),
    ("josé", "JOSÉ"), ("DUKE^", "DUKE"), ("AC/DC", None), (".HIDDEN", None), ("(V.O.)", None), ("A:B", None),
    ("DUKE (V.O.) ^", "DUKE"), ("DUKE^ (V.O.)", "DUKE"), ("@duke ^", "DUKE"), ("^", None),
]


def main():
    for group in ("valid", "errors", "warnings"):
        shutil.rmtree(OUT / group, ignore_errors=True)
    valid()
    errors()
    warnings()
    (OUT / "conformance.json").write_text(json.dumps({"formatVersion": 2, "templateVersion": TEMPLATE_VERSION, "templateSha256": TEMPLATE_SHA, "fixtures": FIXTURES}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    names = [{"input": i, "canonical": c} if c else {"input": i, "error": "E-NAME"} for i, c in NAMES]
    (OUT / "names.json").write_text(json.dumps({"formatVersion": 2, "names": names}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{len(FIXTURES)} fixtures")


if __name__ == "__main__":
    main()
