#!/usr/bin/env python3
"""
freshness.py — produce the work-list for a freshness sweep.

Reads entities.json and answers one question: which entities are most likely to
be wrong right now, and what should be re-read to find out?

It cannot detect a stale fact. Nothing can. What it can do is rank by risk and
hand a reviewer the exact primary-source URLs and the exact claims currently on
the site, so the expensive part (judgement) is the only part left.

Usage:
    python3 freshness.py                # human-readable work-list, stalest first
    python3 freshness.py --json         # machine-readable, for an agent
    python3 freshness.py --top 8        # limit the batch
    python3 freshness.py --today 2026-09-01   # override "now" (tests, backdating)

Risk score, highest first:
  age            days since last_verified
  volatility     how fast this kind of entity moves. A regulator's mandate
                 changes on a scale of years; a vertiport under construction
                 changes monthly; a route that has not launched can launch any
                 week. Status matters more than entity_type here.
  blast radius   how many pages repeat this entity's claims. Getting a widely
                 cited entity wrong is worse than getting an orphan wrong.

See FRESHNESS.md for how to actually do the sweep. Read it before editing
anything — the April/July lesson in there is the whole discipline.
"""
import json, sys, glob, os, re
from datetime import date, datetime

# How fast a claim of this shape goes stale. Multiplier on age.
VOLATILITY = {
    'under_construction': 2.0,   # milestones land monthly
    'certified':          2.0,   # the step after this one is service launch
    'planned':            1.5,   # can break ground any week
    'announced':          1.5,   # can be confirmed, delayed, or quietly dropped
    'trial_only':         1.4,   # a trial either becomes a service or lapses
    'design_approved':    1.3,
    'operational':        1.0,   # already arrived; changes are slower
    'orphaned':           0.7,   # by definition nothing is moving
    'decommissioned':     0.3,   # done is done
}
TYPE_FLOOR = {'regulator': 0.6, 'answer': 0.8}   # dampen slow-moving kinds

# Sources worth re-reading. Aggregators are for finding leads, never for citing.
PRIMARY_TYPES = {'primary', 'operator-ir', 'regulatory', 'government'}


def load(path='entities.json'):
    with open(path, encoding='utf-8') as fh:
        return json.load(fh)


def page_refs(slug, root='.'):
    """How many HTML pages mention this entity. Cheap proxy for blast radius."""
    n = 0
    for f in glob.glob(os.path.join(root, '**', '*.html'), recursive=True):
        if os.sep + '.git' + os.sep in f:
            continue
        try:
            if slug in open(f, encoding='utf-8').read():
                n += 1
        except (OSError, UnicodeDecodeError):
            continue
    return n


def score(entity, today, refs):
    lv = entity.get('last_verified')
    try:
        age = (today - date.fromisoformat(lv)).days
    except (TypeError, ValueError):
        age = 9999                                   # never verified = maximum risk
    vol = VOLATILITY.get(entity.get('status'), 1.0)
    vol *= TYPE_FLOOR.get(entity.get('entity_type'), 1.0)
    reach = 1 + (refs / 25)                          # 25 pages ~= +100%
    return age * vol * reach, age, vol, refs


def build(data, today, root='.'):
    rows = []
    for e in data['entities']:
        refs = page_refs(e['slug'], root)
        s, age, vol, refs = score(e, today, refs)
        srcs = [x for x in e.get('sources', []) if x.get('type') in PRIMARY_TYPES]
        rows.append({
            'slug': e['slug'],
            'name': e['name'],
            'entity_type': e['entity_type'],
            'status': e.get('status'),
            'last_verified': e.get('last_verified'),
            'age_days': age,
            'volatility': round(vol, 2),
            'pages_referencing': refs,
            'risk': round(s, 1),
            'current_claim': e.get('meta_description', ''),
            'primary_sources': [{'name': x['name'], 'url': x['url'],
                                 'type': x['type'], 'accessed': x.get('accessed')}
                                for x in srcs],
            'non_primary_source_count': len(e.get('sources', [])) - len(srcs),
        })
    rows.sort(key=lambda r: -r['risk'])
    return rows


def main():
    args = sys.argv[1:]
    today = date.today()
    if '--today' in args:
        today = date.fromisoformat(args[args.index('--today') + 1])
    top = int(args[args.index('--top') + 1]) if '--top' in args else None

    data = load()
    rows = build(data, today)
    if top:
        rows = rows[:top]

    if '--json' in args:
        json.dump({'generated_for': today.isoformat(), 'entities': rows},
                  sys.stdout, ensure_ascii=False, indent=1)
        print()
        return

    print(f"FRESHNESS WORK-LIST · {today.isoformat()} · {len(rows)} entities, stalest first")
    print("Read FRESHNESS.md before changing anything.\n")
    for i, r in enumerate(rows, 1):
        print(f"{i:>2}. {r['name']}")
        print(f"    risk {r['risk']}  ·  {r['age_days']}d since {r['last_verified']}"
              f"  ·  status {r['status']}  ·  cited on {r['pages_referencing']} pages")
        print(f"    site currently says: {r['current_claim'][:150]}"
              f"{'…' if len(r['current_claim']) > 150 else ''}")
        if r['primary_sources']:
            print("    re-read:")
            for s in r['primary_sources'][:4]:
                print(f"      - [{s['type']}] {s['url']}")
        else:
            print("    !! NO PRIMARY SOURCE ON FILE — this entity should not be published as-is")
        if r['non_primary_source_count']:
            print(f"    ({r['non_primary_source_count']} non-primary source(s) on file — "
                  "leads only, never cite)")
        print()


if __name__ == '__main__':
    main()
