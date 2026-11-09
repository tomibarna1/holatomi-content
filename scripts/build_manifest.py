#!/usr/bin/env python3
"""manifest.json újraépítése: contentVersion +1, updatedAt most, minden tartalomfájl SHA256-ja.

Futtatás a repó gyökeréből, a validate.py UTÁN:  python3 scripts/build_manifest.py
Ha a fájlok nem változtak a legutóbbi manifest óta, a verzió nem nő.
"""
import datetime
import glob
import hashlib
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(ROOT, "manifest.json")


def content_files() -> list[str]:
    files = ["vocab.json", "verbs.json"]
    files += sorted(os.path.relpath(p, ROOT) for p in glob.glob(os.path.join(ROOT, "grammar", "*.json")))
    files += sorted(os.path.relpath(p, ROOT) for p in glob.glob(os.path.join(ROOT, "exercises", "*.json")))
    return [f for f in files if os.path.exists(os.path.join(ROOT, f))]


def main() -> None:
    entries = []
    for rel in content_files():
        with open(os.path.join(ROOT, rel), "rb") as f:
            data = f.read()
        entries.append({"path": rel, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)})

    old = {}
    if os.path.exists(MANIFEST):
        with open(MANIFEST, encoding="utf-8") as f:
            old = json.load(f)
    version = int(old.get("contentVersion", 0))
    if old.get("files") != entries:
        version += 1
        updated = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    else:
        updated = old.get("updatedAt")
        print("Nincs változás, a verzió marad.")

    manifest = {"schemaVersion": 1, "contentVersion": version, "updatedAt": updated, "files": entries}
    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"manifest.json: contentVersion {version}, {len(entries)} fájl")


if __name__ == "__main__":
    main()
