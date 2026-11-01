#!/usr/bin/env python3
"""Write or check the sha256 in template/VERSION.json.

    python3 tools/template_version.py          # writes the sha256
    python3 tools/template_version.py --check  # exits 1 when it doesn't match

The hash is stated in template/README.md, as proposed. Standard library only.
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "template"
VERSION = TEMPLATE / "VERSION.json"
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


def main():
    current = json.loads(VERSION.read_text(encoding="utf-8"))
    computed = template_hash()
    if "--check" in sys.argv[1:]:
        if current.get("sha256") != computed:
            print(f"template/VERSION.json sha256 is {current.get('sha256')!r}, the files hash to {computed}")
            return 1
        print(f"ok: template {current['version']} {computed}")
        return 0
    current["sha256"] = computed
    VERSION.write_text(json.dumps(current, indent=2) + "\n", encoding="utf-8")
    print(f"wrote: template {current['version']} {computed}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
