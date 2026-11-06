#!/usr/bin/env python3
"""Valide un feature.json : schema minimal, IDs, references, couverture."""
import json
import sys

PRIORITIES = {"P1", "P2", "P3"}
TEST_TYPES = {"Functional", "Regression", "Security", "Performance", "Usability"}
AUTOMATION = {"Manual", "Automatable", "Automated"}
REQ_TYPES = {"US", "FR", "AC", "NFR", "ACT"}
MUST_BE_COVERED = {"FR", "AC", "NFR", "ACT"}


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def validate(data):
    errors, warnings = [], []

    for key in ("slug", "title", "explanation", "requirements", "tests"):
        if key not in data:
            errors.append(f"champ racine manquant : {key}")
    if errors:
        return errors, warnings

    for key in ("summary", "ecosystem_role", "example"):
        if not data["explanation"].get(key):
            errors.append(f"explanation.{key} vide ou manquant")

    reqs = {}
    for r in data["requirements"]:
        rid = r.get("id")
        if not rid:
            errors.append("exigence sans id")
            continue
        if rid in reqs:
            errors.append(f"exigence en double : {rid}")
        reqs[rid] = r
        if r.get("type") not in REQ_TYPES:
            errors.append(f"{rid} : type invalide {r.get('type')!r}")
        if not r.get("text"):
            errors.append(f"{rid} : texte vide")
        for parent in r.get("derived_from", []):
            if parent not in {x.get("id") for x in data["requirements"]}:
                errors.append(f"{rid} : derived_from inconnu {parent}")
        if r.get("type") in MUST_BE_COVERED and not r.get("code"):
            warnings.append(f"{rid} : aucune reference de code")

    seen, covered = set(), {}
    for t in data["tests"]:
        tid = t.get("id")
        if not tid:
            errors.append("test sans id")
            continue
        if tid in seen:
            errors.append(f"test en double : {tid}")
        seen.add(tid)
        if not t.get("title"):
            errors.append(f"{tid} : titre vide")
        if t.get("priority") not in PRIORITIES:
            errors.append(f"{tid} : priorite invalide {t.get('priority')!r}")
        if t.get("type") not in TEST_TYPES:
            errors.append(f"{tid} : type invalide {t.get('type')!r}")
        if t.get("automation") not in AUTOMATION:
            errors.append(f"{tid} : automation invalide {t.get('automation')!r}")
        if not t.get("req"):
            errors.append(f"{tid} : test orphelin (aucune exigence)")
        for rid in t.get("req", []):
            if rid not in reqs:
                errors.append(f"{tid} : exigence inconnue {rid}")
            covered.setdefault(rid, []).append(tid)
        steps = t.get("steps", [])
        if not steps:
            errors.append(f"{tid} : aucune etape")
        for i, s in enumerate(steps, 1):
            if not (isinstance(s, list) and len(s) == 2 and s[0] and s[1]):
                errors.append(f"{tid} : etape {i} doit etre [action, attendu] non vides")
        if "needs-clarification" in t.get("tags", []):
            warnings.append(f"{tid} : needs-clarification")

    for rid, r in reqs.items():
        if r.get("type") in MUST_BE_COVERED and rid not in covered:
            errors.append(f"{rid} : exigence sans test")

    return errors, warnings


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: validate.py feature.json")
    errors, warnings = validate(load(sys.argv[1]))
    for w in warnings:
        print(f"AVERTISSEMENT {w}")
    for e in errors:
        print(f"ERREUR {e}")
    print(f"{len(errors)} erreur(s), {len(warnings)} avertissement(s)")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
