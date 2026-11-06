#!/usr/bin/env python3
"""Genere testiny.csv, matrice_tracabilite.csv et explication.md depuis feature.json."""
import csv
import json
import os
import re
import sys

from validate import load, validate

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def bracketed(lines):
    # Format observe dans l'export Testiny : "[1] texte", une ligne vide entre chaque etape
    return "\n\n".join(f"[{i}] {x}" for i, x in enumerate(lines, 1)) + "\n"


def bullets(text):
    if isinstance(text, list):
        items = text
    else:
        items = re.split(r"(?<=\.)\s+(?=[A-Z])", text.strip()) if text else []
    return "".join(f"- {x}\n" for x in items)


def full_title(t):
    refs = [r for r in t["req"] if r.startswith("AC-")] or t["req"]
    return f"{t['id']} {t['title']} ({', '.join(refs)})"


def testiny_row(t, cfg):
    values = {
        "folder": t.get("folder", "").replace(" / ", cfg["folder_separator"]),
        "title_full": full_title(t),
        "template": cfg["template"],
        "preconditions": bullets(t.get("preconditions", "")),
        "steps_text": bracketed([s[0] for s in t["steps"]]),
        "expected_text": bracketed([s[1] for s in t["steps"]]),
        "priority": cfg["priority_map"].get(t["priority"], t["priority"]),
        "type": cfg["type_map"].get(t["type"], t["type"].upper()),
        "automation": cfg["automation_map"].get(t["automation"], "NOT_AUTOMATED"),
    }
    return [values[c["field"]] for c in cfg["columns"]]


def write_testiny(data, out_dir):
    with open(os.path.join(ROOT, "config", "testiny_mapping.json"), encoding="utf-8") as f:
        cfg = json.load(f)
    path = os.path.join(out_dir, "testiny.csv")
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=cfg["delimiter"])
        w.writerow([c["header"] for c in cfg["columns"]])
        for t in data["tests"]:
            w.writerow(testiny_row(t, cfg))
    return path


def write_matrix(data, out_dir):
    by_req = {}
    for t in data["tests"]:
        for rid in t["req"]:
            by_req.setdefault(rid, []).append(t)
    path = os.path.join(out_dir, "matrice_tracabilite.csv")
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Exigence", "Type", "Enonce", "Source spec", "Derive de",
                    "Tests", "Nb tests", "Priorite max", "Code", "Couverture"])
        for r in data["requirements"]:
            tests = by_req.get(r["id"], [])
            prios = sorted(t["priority"] for t in tests)
            if r["type"] == "US":
                derived = [x["id"] for x in data["requirements"] if r["id"] in x.get("derived_from", [])]
                linked = sorted({t["id"] for x in derived for t in by_req.get(x, [])})
                tests_cell = ", ".join(linked)
                nb = len(linked)
                cover = "Couverte via " + ", ".join(derived) if linked else "Non couverte"
                prio = ""
            else:
                tests_cell = ", ".join(t["id"] for t in tests)
                nb = len(tests)
                cover = "Couverte" if tests else "NON COUVERTE"
                prio = prios[0] if prios else ""
            w.writerow([r["id"], r["type"], r["text"], r.get("source", ""),
                        ", ".join(r.get("derived_from", [])), tests_cell, nb, prio,
                        "\n".join(r.get("code", [])), cover])
    return path


def write_explanation(data, out_dir):
    e = data["explanation"]
    lines = [f"# {data['title']}", ""]
    meta = [data.get("release"), data.get("spec_file")]
    meta = [m for m in meta if m]
    if meta:
        lines += [" | ".join(meta), ""]
    lines += ["## Ce que fait la fonctionnalite", "", e["summary"], "",
              "## Son role dans l'ecosysteme", "", e["ecosystem_role"], "",
              "## Exemple d'utilisation", "", "Le deroule", ""]
    lines += [f"{i}. {s}" for i, s in enumerate(e["example"], 1)]
    if e.get("limits"):
        lines += ["", "## Limites et hors perimetre", ""] + [f"- {x}" for x in e["limits"]]
    if data.get("findings"):
        lines += ["", "## Ecarts constates entre spec et code", ""] + [f"- {x}" for x in data["findings"]]
    if data.get("open_questions"):
        lines += ["", "## Questions ouvertes", ""] + [f"- {x}" for x in data["open_questions"]]
    lines += ["", "---", "", "Brouillon genere par IA, a relire par un humain avant diffusion ou import.", ""]
    path = os.path.join(out_dir, "explication.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return path


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: export.py feature.json")
    src = sys.argv[1]
    data = load(src)
    errors, warnings = validate(data)
    for w in warnings:
        print(f"AVERTISSEMENT {w}")
    if errors:
        for e in errors:
            print(f"ERREUR {e}")
        sys.exit(f"{len(errors)} erreur(s) : export annule")
    out_dir = os.path.dirname(os.path.abspath(src))
    for p in (write_testiny(data, out_dir), write_matrix(data, out_dir), write_explanation(data, out_dir)):
        print("ecrit", p)
    print(f"{len(data['requirements'])} exigences, {len(data['tests'])} tests, {len(warnings)} avertissement(s)")


if __name__ == "__main__":
    main()
