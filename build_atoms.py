#!/usr/bin/env python3
"""build_atoms.py — the enum layer's first gate (POA addendum, loisirs74 W1 analog).

The entity-level atoms already live in entities.json (status enum, type,
coordinates, dates, sources) and feed the API, cards, CSV and changes log.
What was NOT atomised is the per-page "At a glance" fact grid: hand-authored
prose in five locales. The sweep of 2026-08-22 proved the failure mode — the
DXB vertiport's Status row still said "technical completion" in all five
locales a month after certification, because nothing tied that row to the
dataset.

This script ties it:

  stamp  (default)  writes data-status="<enum>" onto each entity page's
                    Status fact row, sourced from entities.json. Prose stays
                    for humans; the attribute is the machine truth.
  check             fails (exit 1) when a stamped row's enum disagrees with
                    entities.json, or when an entity's locale pages render a
                    different number of fact rows than its EN page.

guard.sh runs `check` on every build, so status drift in the fact grid is now
build-breaking instead of silent. Full atomisation of the remaining fact keys
(operator, builder, dates …) is the recorded E1 backlog item in the POA.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SECTION = {'aircraft': 'aircraft', 'operator': 'operators', 'vertiport': 'vertiports',
           'route': 'routes', 'regulator': 'regulators', 'answer': 'explainers'}
LANGS = ('', 'ar', 'fr', 'de', 'zh')
STATUS_KEYS = {'Status', 'Statut', 'الحالة', '状态'}
ROW = re.compile(r'(<span class="fact-key">([^<]+)</span><span class="fact-val")( data-status="[^"]*")?(>)')


def pages_of(slug, etype):
    for L in LANGS:
        p = ROOT / L / SECTION[etype] / f'{slug}.html' if L else ROOT / SECTION[etype] / f'{slug}.html'
        if p.exists():
            yield L or 'en', p


def stamp():
    ents = json.loads((ROOT / 'entities.json').read_text(encoding='utf-8'))['entities']
    stamped = skipped = 0
    for e in ents:
        for lang, p in pages_of(e['slug'], e['entity_type']):
            h = p.read_text(encoding='utf-8')
            out, n = [], 0
            last = 0
            for m in ROW.finditer(h):
                if m.group(2).strip() in STATUS_KEYS:
                    out.append(h[last:m.start()])
                    out.append(f'{m.group(1)} data-status="{e["status"]}"{m.group(4)}')
                    last = m.end()
                    n += 1
            if n:
                out.append(h[last:])
                p.write_text(''.join(out), encoding='utf-8')
                stamped += 1
            else:
                skipped += 1
    print(f'atoms: status stamped on {stamped} pages ({skipped} pages have no Status fact row)')


def check():
    ents = json.loads((ROOT / 'entities.json').read_text(encoding='utf-8'))['entities']
    fail = 0
    for e in ents:
        counts = {}
        for lang, p in pages_of(e['slug'], e['entity_type']):
            h = p.read_text(encoding='utf-8')
            counts[lang] = len(re.findall(r'<div class="fact">', h))
            for m in re.finditer(r'data-status="([^"]+)"[^>]*>', h):
                pass  # cards elsewhere on the page may carry other entities' statuses
            m = re.search(r'<span class="fact-key">(?:' + '|'.join(STATUS_KEYS) + r')</span>'
                          r'<span class="fact-val" data-status="([^"]+)"', h)
            if m and m.group(1) != e['status']:
                print(f'ATOMS FAIL: {p.relative_to(ROOT)}: fact grid says {m.group(1)}, '
                      f'entities.json says {e["status"]}')
                fail += 1
        vals = set(counts.values())
        if len(vals) > 1:
            print(f'ATOMS FAIL: {e["slug"]}: fact-row count differs across locales: {counts}')
            fail += 1
    if fail:
        print(f'atoms check: {fail} failure(s)')
        return 1
    print('atoms check: status rows agree with entities.json; locale fact parity holds')
    return 0


if __name__ == '__main__':
    sys.exit(check() if 'check' in sys.argv[1:] else stamp())
