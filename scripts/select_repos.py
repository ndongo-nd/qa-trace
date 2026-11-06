#!/usr/bin/env python3
"""Propose les repos a analyser pour une spec.

Deux signaux :
  1. la section "Product Scope" de la spec (cases cochees) mappee via config/repos.json ;
  2. une recherche de mots-cles dans le code local (--keywords a,b,c) pour reperer
     les repos touches mais non coches.
Les repos e2e du produit concerne sont ajoutes pour connaitre les tests existants.
"""
import argparse
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHECK = re.compile(r"^\s*[-*]\s*\[([xX ])\]\s*(.+?)\s*$")
TEXT_EXT = {".go", ".ts", ".tsx", ".js", ".scala", ".java", ".kt", ".py", ".md", ".json", ".yml", ".yaml", ".conf", ".html", ".sql", ".feature"}


def checked_scope(spec_path):
    labels, in_scope = [], False
    with open(spec_path, encoding="utf-8") as f:
        for line in f:
            if re.match(r"^#{1,6}\s", line):
                in_scope = "product scope" in line.lower()
                continue
            if in_scope:
                m = CHECK.match(line)
                if m and m.group(1).lower() == "x":
                    labels.append(m.group(2))
    return labels


def scan(repo_path, skip, patterns, limit=5):
    hits, count = [], 0
    for dirpath, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in skip]
        for name in files:
            if os.path.splitext(name)[1].lower() not in TEXT_EXT:
                continue
            p = os.path.join(dirpath, name)
            try:
                if os.path.getsize(p) > 1_000_000:
                    continue
                with open(p, encoding="utf-8", errors="ignore") as f:
                    text = f.read()
            except OSError:
                continue
            if any(pat.search(text) for pat in patterns):
                count += 1
                if len(hits) < limit:
                    hits.append(os.path.relpath(p, repo_path))
    return count, hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--keywords", default="")
    args = ap.parse_args()

    with open(os.path.join(ROOT, "config", "repos.json"), encoding="utf-8") as f:
        cfg = json.load(f)
    repos = cfg["repos"]
    labels = checked_scope(args.spec)
    selected, reasons, unmapped = {}, {}, []

    for label in labels:
        matched = [r for r in repos if any(k.lower() in label.lower() for k in r["scope_labels"])]
        if not matched:
            unmapped.append(label)
        for r in matched:
            selected[r["id"]] = r
            reasons.setdefault(r["id"], []).append(f"Product Scope coche : {label}")

    # Repos e2e du meme produit que les repos selectionnes
    for r in repos:
        if r["kind"] == "e2e" and any(s["product"] == r["product"] for s in list(selected.values())):
            selected.setdefault(r["id"], r)
            reasons.setdefault(r["id"], []).append("tests e2e du produit concerne")

    keywords = [k.strip() for k in args.keywords.split(",") if k.strip()]
    patterns = [re.compile(re.escape(k), re.I) for k in keywords]
    scans = {}
    for r in repos:
        path = os.path.normpath(os.path.join(ROOT, r["path"]))
        if r["status"] != "local" or not os.path.isdir(path) or not patterns:
            continue
        count, hits = scan(path, set(cfg["skip_dirs"]), patterns)
        scans[r["id"]] = {"files_matching": count, "examples": hits}
        if count and r["id"] not in selected:
            selected[r["id"]] = r
            reasons.setdefault(r["id"], []).append(f"{count} fichier(s) contiennent les mots-cles (hors scope coche)")

    out = {
        "scope_checked": labels,
        "scope_without_repo": unmapped,
        "selected": [
            {
                "id": rid, "product": r["product"], "kind": r["kind"], "status": r["status"],
                "path": os.path.normpath(os.path.join(ROOT, r["path"])),
                "reasons": reasons[rid],
            }
            for rid, r in selected.items()
        ],
        "keyword_scan": scans,
        "to_clone": [r["id"] for r in selected.values() if r["status"] != "local"],
    }
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
