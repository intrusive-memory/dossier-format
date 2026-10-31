#!/usr/bin/env python3
"""Regenerate examples/ (the conformance fixtures) from nothing.

This builds test data. It is not a reader, writer, validator or renderer of
the format, and no implementation may treat it as one: it deliberately writes
broken bundles, and it hard-codes what each one should report.

    python3 -m venv /tmp/df && /tmp/df/bin/pip install -r tools/requirements.txt
    /tmp/df/bin/python tools/build_examples.py

Everything is invented. No character, image, voice or line here comes from a
real production (AGENTS.md rule 1).
"""
import base64
import copy
import hashlib
import io
import json
import re
import shutil
import struct
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
TEMPLATE_VERSION = "0.0.0-fixture"
TEMPLATE_SHA = hashlib.sha256(b"dossier-format fixture template\n").hexdigest()
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
    image = Image.open(io.BytesIO(data)).convert("RGB").resize(size)
    buffer = io.BytesIO()
    image.save(buffer, "JPEG", quality=80)
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

    def page(self, member, body_extra="", padding=0):
        """A hand-made page meeting §11, without the template, which doesn't exist yet."""
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
        text = self.files[description["path"]].decode()
        _, fm, body = text.split("---\n", 2)
        record = {"formatVersion": 2, "character": self.name, "castMember": member,
                  "frontMatter": yaml.safe_load(fm), "body": body, "manifest": embedded}
        record_json = json.dumps(record, sort_keys=True, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
        parts = []
        sizes = {"portrait": (720, 1280), "view": (720, 1280), "face": (512, 512), "expression": (512, 512)}
        for asset in embedded["assets"]:
            if asset["status"] != "selected":
                continue
            if asset["kind"] in sizes:
                data = base64.b64encode(jpeg_copy(self.files[asset["path"]], sizes[asset["kind"]])).decode()
                parts.append(f'<img alt="{asset["kind"]} {asset.get("variant", "")}" src="data:image/jpeg;base64,{data}">')
            elif asset["kind"] == "voiceSample":
                data = base64.b64encode(self.files[asset["path"]]).decode()
                parts.append(f'<audio controls src="data:audio/mp4;base64,{data}"></audio>')
        html = (f'<!DOCTYPE html>\n<html lang="en"><head><meta charset="utf-8">'
                f'<meta name="dossier-template" content="{TEMPLATE_VERSION} {TEMPLATE_SHA}">'
                f"<title>{self.name}</title></head><body><h1>{self.name}</h1>\n"
                + "\n".join(parts) + body_extra
                + f'\n<script type="application/json" id="character-record">{record_json}</script>\n</body></html>\n').encode()
        if padding:
            html += b"<!--" + b" " * (padding - len(html) - 7) + b"-->\n"
        derived = [self.input("description"),
                   {"role": "castMember", "sha256": sha(json.dumps(member, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode())},
                   {"role": "bundle", "sha256": embedded["manifestChecksum"]},
                   {"role": "template", "version": TEMPLATE_VERSION, "sha256": TEMPLATE_SHA}]
        self.put(path, html, "dossier", provenance={"provider": "manual", "notes": "Hand-made for the fixtures."}, created=NOW, derivedFrom=derived)

    def write(self, project):
        root = project / self.dir
        root.mkdir(parents=True)
        for path, data in {**self.files, **self.disk, **self.loose}.items():
            if path in self.missing:
                continue
            target = root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
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


def code_for(name):
    return next(code for code in CODES if name == code or name.startswith(code + "-"))


def fixture(group, name, bundles, members, codes=(), may_also=(), complete=None, missing=None, note=""):
    project = OUT / group / name
    project.mkdir(parents=True)
    cast = front_matter({"type": "cast", "schemaVersion": 1, "cast": members}) + "# Cast\n\nSynthetic data only.\n"
    (project / "CAST.md").write_text(cast, encoding="utf-8")
    for bundle in bundles:
        bundle.write(project)
    entry = {"path": f"{group}/{name}", "bundle": bundles[0].dir, "verdict": {"valid": "valid", "warnings": "warnings", "errors": "invalid"}[group],
             "codes": sorted(codes), "mayAlso": sorted(may_also)}
    if complete is not None:
        entry["complete"] = complete
        entry["missingRequired"] = missing or []
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
    fixture("valid", "empty-background", [b], [member(b)], complete=True, note="No files and no assets; manifestChecksum is the SHA-256 of the empty string.")


# --- errors ------------------------------------------------------------------

def errors():
    def err(name, b=None, members=None, codes=None, may_also=(), note=""):
        b = b or base()
        fixture("errors", name, [b], members or [member(b)], codes or [code_for(name)], may_also, note=note)

    b = base(); b.mutate = lambda m: m.update(manifestVersion=3)
    err("E-VERSION", b)

    b = base("AC/DC", dirname="ACDC.dossier")
    err("E-NAME-slash", b, may_also=["E-NAME-MISMATCH", "E-SCHEMA"])
    b = base(".HIDDEN")
    err("E-NAME-leading-dot", b, may_also=["E-SCHEMA"])

    b = base(dirname="PELL.dossier")
    err("E-NAME-MISMATCH-directory", b, codes=["E-NAME-MISMATCH"])
    b = base()
    err("E-NAME-MISMATCH-member", b, members=[{**member(b), "character": "PELL"}], codes=["E-NAME-MISMATCH"])

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

    b = base(); b.missing.add(b.selected("portrait")["path"])
    err("E-FILE-MISSING", b)

    b = base(); text = b.files["CHARACTER.md"]; b.disk["CHARACTER.md"] = text.replace(b"grey-eyed", b"gray-eyed")
    err("E-FILE-HASH", b, note="The same size, different bytes.")
    b = base(); b.disk["CHARACTER.md"] = b.files["CHARACTER.md"] + b"\n"
    err("E-FILE-HASH-size", b, note="The file grew by a byte.")

    b = base(); b.put("source/empty.png", b"", "sourcePhoto", provenance={"provider": "import"})
    err("E-ZERO-BYTE", b, may_also=["E-SCHEMA"])

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

    b = base(description=short_description(PELL, "background", art="woodcut"))
    warn("W-STALE-art-style", b, note="The images' provenance.artStyle differs from the current front matter.")

    b = Bundle(PELL, "background")
    b.put("CHARACTER.md", short_description(PELL, "background"), "description")
    b.image("portrait", png(180, 180, "square portrait"))
    warn("W-SHAPE", b)

    b = base(); b.image("expression", png(128, 128, "wistful", (30, 25, 68, 85)), "wistful", derivedFrom=[b.input("face"), b.input("portrait")])
    warn("W-VARIANT-expression", b)
    b = base(); b.image("view", png(180, 320, "overhead"), "overhead", derivedFrom=[b.input("portrait"), b.input("face")])
    warn("W-VARIANT-view", b)

    b = base(); b.put(f"images/portrait-{sha(b.files[b.selected('portrait')['path']])[:8]}.json", b'{"seed": 7}\n')
    warn("W-SIDECAR", b, may_also=["W-UNCLASSIFIED"])

    b = base(); stray = base("STRAY VISITOR")
    warn("W-ORPHAN", b, extra=[stray], note="STRAY VISITOR is reported and not loaded.")

    b = base()
    warn("W-POINTER", b, members=[{**member(b), "manifest": f"characters/archive/{PELL}.dossier/manifest.json"}], may_also=["W-ORPHAN"], complete=None,
         note="The pointer leads nowhere, so the bundle isn't loaded and completeness isn't defined.")

    b = base(role=None)
    warn("W-ROLE", b, complete=None, note="No tier, so completeness isn't defined.")

    b = base(); voice = add_voice(b); add_sample(b, "neutral", "1.7b", "One line.")
    warn("W-VOICE-ELSEWHERE", b, members=[member(b, voice=f"voices/{PELL}.vox", prompt=VOICE_PROMPT)])
    b = base(); voice = add_voice(b)
    warn("W-VOICE-PROMPT", b, members=[member(b, voice=voice, prompt="A different prompt from the one the voice was made with.")])

    b = base(description=short_description(PELL, "background", extra="\nA claim with no definition.[^nowhere]\n"))
    warn("W-FOOTNOTE-undefined", b)
    b = base(description=short_description(PELL, "background") + b"[^unused]: Author. Nothing refers to this, 2026-10-31.\n")
    warn("W-FOOTNOTE-unused", b)

    b = base(); m = member(b); b.page(m, padding=11_000_000)
    warn("W-PAGE-SIZE", b, members=[m], note="11,000,000 bytes, nearly all of it a comment, which git compresses.")
    b = base(); m = member(b); b.page(m, body_extra=f'\n<img alt="linked" src="{b.selected("face")["path"]}">')
    warn("W-PAGE-EXTERNAL", b, members=[m])

    name = "WREN HALLOWAY"
    b = Bundle(name, "lead")
    b.put("CHARACTER.md", full_description(name, "lead"), "description")
    warn("W-INCOMPLETE", b, complete=False, missing=["dossier", "expressions", "face", "portrait", "sample.neutral.0.6b", "sample.neutral.1.7b", "sample.range", "views", "voicePrompt", "vox.0.6b", "vox.1.7b"])

    # Version 1, in both shapes Appendix A describes.
    def v1(dirname):
        b = Bundle(PELL, "background", dirname)
        b.put("CHARACTER.md", short_description(PELL, "background"))
        b.put("images/portrait-v3-photo-s133.png", png(180, 320, "v1 portrait"))
        b.put("images/turnaround-front-s21.png", png(180, 320, "v1 front"))
        b.put("images/face.png", png(128, 128, "v1 face", (30, 25, 68, 85)))
        b.put("images/turnaround-front-s21.json", b'{"seed": 21}\n')
        def downgrade(m):
            m["manifestVersion"] = 1
            m["assets"] = [
                {"path": "CHARACTER.md", "kind": "description", "status": "selected"},
                {"path": "images/face.png", "kind": "faceSheet", "status": "selected"},
                {"path": "images/portrait-v3-photo-s133.png", "kind": "portrait", "status": "selected", "createdAt": MADE, "provenance": {"tool": "fixture", "references": []}},
                {"path": "images/turnaround-front-s21.png", "kind": "turnaround", "status": "selected", "label": "front"},
            ]
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


# --- data --------------------------------------------------------------------

NAMES = [
    ("Mitch", "MITCH"), ("@McCowley", "MCCOWLEY"), ("BILLY (V.O.)", "BILLY"), ("BILLY (CONT'D) (O.S.)", "BILLY"),
    ("Aunt   Stanley", "AUNT STANLEY"), ("mccowley's wife", "MCCOWLEY'S WIFE"), ("CB#1", "CB#1"), ("josé", "JOSÉ"),
    ("josé", "JOSÉ"), ("DUKE^", "DUKE"), ("AC/DC", None), (".HIDDEN", None), ("(V.O.)", None), ("A:B", None),
]


def main():
    for group in ("valid", "errors", "warnings"):
        shutil.rmtree(OUT / group, ignore_errors=True)
    valid()
    errors()
    warnings()
    (OUT / "conformance.json").write_text(json.dumps({"formatVersion": 2, "templateVersion": TEMPLATE_VERSION, "fixtures": FIXTURES}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    names = [{"input": i, "canonical": c} if c else {"input": i, "error": "E-NAME"} for i, c in NAMES]
    (OUT / "names.json").write_text(json.dumps({"formatVersion": 2, "names": names}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{len(FIXTURES)} fixtures")


if __name__ == "__main__":
    main()
