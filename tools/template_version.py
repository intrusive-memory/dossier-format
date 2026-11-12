#!/usr/bin/env python3
"""Write or check the sha256 in template/VERSION.json and template-locations/VERSION.json.

    python3 tools/template_version.py          # writes both
    python3 tools/template_version.py --check  # exits 1 when either doesn't match

The dossier template's hash is stated in template/README.md, rule 1, and the LOCATIONS
page template's in template-locations/README.md, rule 1. Standard library only.
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "template"
VERSION = TEMPLATE / "VERSION.json"
LOCATIONS_TEMPLATE = ROOT / "template-locations"
LOCATIONS_VERSION = LOCATIONS_TEMPLATE / "VERSION.json"
SHARED = ("template/dossier.css", "template/fonts.css")  # What the LOCATIONS page carries from template/.
EXCLUDED_FILES = {"VERSION.json", "README.md"}
EXCLUDED_DIRECTORIES = {"example"}


def hashed_paths(root=TEMPLATE):
    """Every file the hash covers, relative to root, in byte order of the UTF-8 path."""
    paths = []
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if not path.is_file() or any(part.startswith(".") for part in relative.parts):
            continue
        if relative.parts[0] in EXCLUDED_DIRECTORIES or relative.as_posix() in EXCLUDED_FILES:
            continue
        paths.append(relative.as_posix())
    return sorted(paths, key=lambda text: text.encode("utf-8"))


def template_hash(root=TEMPLATE):
    digest = hashlib.sha256()
    for relative in hashed_paths(root):
        digest.update(relative.encode("utf-8") + b"\0" + (root / relative).read_bytes())
    return digest.hexdigest()


def locations_hashed_paths():
    """template-locations/README.md rule 1: its own files and the two it carries from template/, by repository path."""
    own = [f"{LOCATIONS_TEMPLATE.name}/{relative}" for relative in hashed_paths(LOCATIONS_TEMPLATE)]
    return sorted(own + list(SHARED), key=lambda text: text.encode("utf-8"))


def locations_template_hash():
    digest = hashlib.sha256()
    for relative in locations_hashed_paths():
        digest.update(relative.encode("utf-8") + b"\0" + (ROOT / relative).read_bytes())
    return digest.hexdigest()


def main():
    status = 0
    for name, path, computed in (("template", VERSION, template_hash()),
                                 ("template-locations", LOCATIONS_VERSION, locations_template_hash())):
        current = json.loads(path.read_text(encoding="utf-8"))
        if "--check" in sys.argv[1:]:
            if current.get("sha256") != computed:
                print(f"{name}/VERSION.json sha256 is {current.get('sha256')!r}, the files hash to {computed}")
                status = 1
                continue
            print(f"ok: {name} {current['version']} {computed}")
            continue
        current["sha256"] = computed
        path.write_text(json.dumps(current, indent=2) + "\n", encoding="utf-8")
        print(f"wrote: {name} {current['version']} {computed}")
    return status


if __name__ == "__main__":
    sys.exit(main())
