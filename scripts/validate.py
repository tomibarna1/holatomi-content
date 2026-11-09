#!/usr/bin/env python3
"""A holatomi-content JSON-fájljainak ellenőrzése. Hiba esetén 1-gyel lép ki.

Futtatás a repó gyökeréből:  python3 scripts/validate.py
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
errors: list[str] = []
warnings: list[str] = []

PERSONS = {"yo", "tu", "el", "nosotros", "vosotros", "ellos"}
TENSES = {"presente", "preteritoPerfecto", "indefinido", "imperfecto", "futuro", "imperativo"}
STEM = {None, "e>ie", "o>ue", "e>i", "u>ue"}
POS = {None, "noun", "verb", "adj", "phrase", "number", "other"}
GENDER = {None, "m", "f", "mf"}
ITEM_TYPES = {"multipleChoice", "fillBlank", "translateToEs", "translateToHu", "reorder", "match", "serEstar", "article"}
SECTION_TYPES = {"text", "table", "examples", "tip", "warning"}
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ID = re.compile(r"^[a-z0-9][a-z0-9._\-]*$")
DASHES = (chr(0x2014), chr(0x2013))


def err(where: str, msg: str) -> None:
    errors.append(f"{where}: {msg}")


def load(path: str):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:  # noqa: BLE001
        err(os.path.relpath(path, ROOT), f"nem olvasható JSON ({e})")
        return None


def check_dashes(path: str) -> None:
    with open(path, encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            if any(d in line for d in DASHES):
                err(f"{os.path.relpath(path, ROOT)}:{n}", "gondolatjel (em/en dash) tilos")


def need(obj: dict, key: str, typ, where: str) -> bool:
    if key not in obj or obj[key] is None:
        err(where, f"hiányzik: {key}")
        return False
    if not isinstance(obj[key], typ):
        err(where, f"rossz típus: {key}")
        return False
    return True


def check_vocab() -> None:
    path = os.path.join(ROOT, "vocab.json")
    d = load(path)
    if d is None:
        return
    check_dashes(path)
    for k, t in (("schemaVersion", int), ("deckVersion", int), ("updatedAt", str), ("categories", list), ("cards", list)):
        need(d, k, t, "vocab.json")
    cats = set()
    for c in d.get("categories", []):
        if need(c, "id", str, "vocab.json kategória") and need(c, "nameHu", str, f"kategória {c.get('id')}"):
            if c["id"] in cats:
                err("vocab.json", f"duplikált kategória: {c['id']}")
            cats.add(c["id"])
    ids = set()
    for i, card in enumerate(d.get("cards", [])):
        where = f"vocab.json kártya #{i} ({card.get('id')})"
        ok = all(need(card, k, str, where) for k in ("id", "category", "es", "hu"))
        if not ok:
            continue
        if not ID.match(card["id"]):
            err(where, "az id kisbetű, szám, pont, aláhúzás, kötőjel lehet")
        if card["id"] in ids:
            err(where, "duplikált id")
        ids.add(card["id"])
        if card["category"] not in cats:
            err(where, f"ismeretlen kategória: {card['category']}")
        for dk in ("lesson", "addedAt"):
            v = card.get(dk)
            if v is not None and not (isinstance(v, str) and DATE.match(v)):
                err(where, f"{dk} formátuma ÉÉÉÉ-HH-NN")
        if card.get("gender") not in GENDER:
            err(where, "gender: m, f, mf vagy null")
        if card.get("partOfSpeech") not in POS:
            err(where, "partOfSpeech érvénytelen")
        if card.get("tags") is not None and not (isinstance(card["tags"], list) and all(isinstance(t, str) for t in card["tags"])):
            err(where, "tags: szöveglista")
    print(f"vocab.json: {len(ids)} kártya, {len(cats)} kategória")


def check_verbs() -> None:
    path = os.path.join(ROOT, "verbs.json")
    if not os.path.exists(path):
        err("verbs.json", "hiányzik")
        return
    d = load(path)
    if d is None:
        return
    check_dashes(path)
    need(d, "schemaVersion", int, "verbs.json")
    ids = set()
    for i, v in enumerate(d.get("verbs", [])):
        where = f"verbs.json #{i} ({v.get('id')})"
        if not all(need(v, k, str, where) for k in ("id", "infinitive", "hu", "type")):
            continue
        if v["id"] in ids:
            err(where, "duplikált id")
        ids.add(v["id"])
        if v["type"] not in ("ar", "er", "ir"):
            err(where, "type: ar, er, ir")
        for b in ("reflexive", "irregular"):
            need(v, b, bool, where)
        if v.get("stemChange") not in STEM:
            err(where, "stemChange érvénytelen")
        if v.get("reflexive") and not v["infinitive"].endswith("se"):
            err(where, "visszaható ige infinitive-je -se végű")
        ov = v.get("overrides")
        if ov is not None:
            if not isinstance(ov, dict):
                err(where, "overrides: objektum")
            else:
                for tense, forms in ov.items():
                    if tense not in TENSES:
                        err(where, f"ismeretlen idő: {tense}")
                    for p, f in (forms or {}).items():
                        if p not in PERSONS:
                            err(where, f"ismeretlen személy: {p}")
                        if not isinstance(f, str) or not f.strip():
                            err(where, f"üres alak: {tense}.{p}")
                if not v.get("irregular"):
                    warnings.append(f"{where}: van overrides, de irregular=false")
    print(f"verbs.json: {len(ids)} ige")


def check_item(it: dict, where: str) -> None:
    if not need(it, "id", str, where) or not need(it, "type", str, where):
        return
    t = it["type"]
    w = f"{where} [{it['id']}]"
    if t not in ITEM_TYPES:
        err(w, f"ismeretlen type: {t}")
        return
    if t != "match":
        need(it, "prompt", str, w)
    if t in ("multipleChoice", "serEstar", "article"):
        if need(it, "options", list, w) and need(it, "answer", int, w):
            if not 0 <= it["answer"] < len(it["options"]):
                err(w, "answer index a tartományon kívül")
    if t in ("fillBlank", "translateToEs", "translateToHu", "reorder"):
        if need(it, "answers", list, w) and not it["answers"]:
            err(w, "answers üres")
    if t in ("fillBlank", "serEstar", "article") and "___" not in it.get("prompt", ""):
        err(w, "a promptban kell ___")
    if t == "reorder":
        need(it, "tiles", list, w)
    if t == "match":
        if need(it, "pairs", list, w):
            for p in it["pairs"]:
                if not (isinstance(p, dict) and isinstance(p.get("es"), str) and isinstance(p.get("hu"), str)):
                    err(w, "pairs elem: {es, hu}")


def check_grammar() -> None:
    files = sorted(glob.glob(os.path.join(ROOT, "grammar", "*.json")))
    orders = set()
    for path in files:
        rel = os.path.relpath(path, ROOT)
        d = load(path)
        if d is None:
            continue
        check_dashes(path)
        for k, t in (("id", str), ("titleHu", str), ("order", int), ("level", str), ("sections", list), ("quiz", list)):
            need(d, k, t, rel)
        if d.get("id") and os.path.basename(path) != f"{d['id']}.json":
            err(rel, "a fájlnév legyen <id>.json")
        if d.get("order") in orders:
            err(rel, "duplikált order")
        orders.add(d.get("order"))
        if d.get("status", "taken") not in ("taken", "next"):
            err(rel, "status: taken vagy next")
        for s in d.get("sections", []):
            if s.get("type") not in SECTION_TYPES:
                err(rel, f"ismeretlen szekció: {s.get('type')}")
            if s.get("type") == "table":
                cols = s.get("columns", [])
                for r in s.get("rows", []):
                    if len(r) != len(cols):
                        err(rel, f"táblázat sora nem {len(cols)} oszlopos: {r}")
            if s.get("type") == "examples":
                for e in s.get("items", []):
                    if not (isinstance(e.get("es"), str) and isinstance(e.get("hu"), str)):
                        err(rel, "példa: {es, hu}")
        ids = set()
        for it in d.get("quiz", []):
            if it.get("id") in ids:
                err(rel, f"duplikált kvíz-id: {it.get('id')}")
            ids.add(it.get("id"))
            check_item(it, rel)
    print(f"grammar: {len(files)} lecke")


def check_exercises() -> None:
    files = sorted(glob.glob(os.path.join(ROOT, "exercises", "*.json")))
    for path in files:
        rel = os.path.relpath(path, ROOT)
        d = load(path)
        if d is None:
            continue
        check_dashes(path)
        for k, t in (("id", str), ("titleHu", str), ("items", list)):
            need(d, k, t, rel)
        lesson = d.get("lesson")
        if lesson is not None and not DATE.match(str(lesson)):
            err(rel, "lesson formátuma ÉÉÉÉ-HH-NN")
        for it in d.get("items", []):
            check_item(it, rel)
    print(f"exercises: {len(files)} feladatsor")


def main() -> int:
    check_vocab()
    check_verbs()
    check_grammar()
    check_exercises()
    for w in warnings:
        print("FIGYELEM:", w)
    if errors:
        print(f"\n{len(errors)} HIBA:")
        for e in errors:
            print(" -", e)
        return 1
    print("OK: minden fájl érvényes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
