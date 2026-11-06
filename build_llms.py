#!/usr/bin/env python3
"""Regenerate llms-full.txt from entities.json.

The file had been edited by hand and drifted from the data (stale statuses,
summaries and access dates; found Oct 2026). Each entity block carries type,
status, location, last-verified date, summary, fact atoms and every source.
The header (title and site summary) is kept from the existing file; entity
order follows the existing file, new entities slot in by name within their
type.

Run from the repo root after any entities.json change, then ./guard.sh.
"""
import datetime
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent
DIRS = {"operator": "operators", "aircraft": "aircraft", "vertiport": "vertiports",
        "route": "routes", "regulator": "regulators", "answer": "explainers"}
ORDER = list(DIRS)


def host():
    return re.search(r"<loc>https://([^/<]+)", (ROOT / "sitemap.xml").read_text(encoding="utf-8")).group(1)


def block(e, site):
    lines = [
        f"## {e['name']}",
        f"Type: {e['entity_type']} | Status: {e['status']} | City: {e.get('city') or '—'} | "
        f"Country: {e.get('country') or '—'} | Last verified: {e['last_verified']}",
    ]
    if e.get("latitude") is not None and e.get("longitude") is not None:
        lines.append(f"Coordinates: {e['latitude']}, {e['longitude']}")
    lines.append(f"Summary: {e['meta_description']}")
    if e.get("facts"):
        lines.append("Facts: " + " · ".join(f"{f['k']}: {f['v']}" for f in e["facts"]))
    lines.append("Primary sources:")
    for s in e["sources"]:
        lines.append(f"- {s['name']} ({s['type']}), accessed {s['accessed']}" + (f": {s['url']}" if s.get("url") else ""))
    lines.append(f"Page: https://{site}/{DIRS[e['entity_type']]}/{e['slug']}.html")
    return "\n".join(lines)


def main():
    site = host()
    path = ROOT / "llms-full.txt"
    old = path.read_text(encoding="utf-8")
    head = old[: old.index("\n## ") + 1]
    known = re.findall(r"^## (.*)$", old, re.M)
    entities = json.loads((ROOT / "entities.json").read_text(encoding="utf-8"))["entities"]

    ordered = sorted((e for e in entities if e["name"] in known),
                     key=lambda e: (ORDER.index(e["entity_type"]), known.index(e["name"])))
    for e in sorted((e for e in entities if e["name"] not in known), key=lambda e: e["name"].lower()):
        i = next((k for k, x in enumerate(ordered)
                  if ORDER.index(x["entity_type"]) > ORDER.index(e["entity_type"])
                  or (x["entity_type"] == e["entity_type"] and x["name"].lower() > e["name"].lower())), len(ordered))
        ordered.insert(i, e)

    stamp = max(e["last_verified"] for e in entities)
    head = re.sub(r"Generated: [^ ]+\.", f"Generated: {stamp}T00:00:00.000Z.", head, count=1)
    path.write_text(head + "\n" + "\n\n".join(block(e, site) for e in ordered) + "\n", encoding="utf-8")
    print(f"llms-full: {len(ordered)} entities written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
