#!/usr/bin/env python3
"""build_atoms.py — the enum/atoms layer (POA E-layer; loisirs74 W1 analog).

Entity-level atoms (status enum, type, coordinates, dates, sources) have
always lived in entities.json. This module extends the atom layer to the
per-page "At a glance" fact grids, which used to be hand-authored prose in
five locales with no tie to the dataset — the failure mode the 2026-08-22
sweep caught live (a Status row stale in five locales).

Commands:

  harvest   E1 backfill. Parses every entity page's fact grid in all five
            locales and stores it on the entity as `facts`:
                [{id, k, v, i18n: {lang: {k?, v?}}}]
            k/v are the EN label and value (the canonical, language-free
            form); i18n carries ONLY what a locale renders differently
            (its translated label, and its value only when translated).
            Also derives data/facts_vocab.json — the EN-key -> per-locale
            label vocabulary, learned from the human translations already
            on the pages. Harvest is idempotent: it re-reads pages, so run
            it after editing a fact row anywhere (page + all locales).

  stamp     Writes data-status="<enum>" onto each entity page's Status
            fact row, sourced from entities.json (machine truth beside the
            human prose).

  check     The gate (wired into guard.sh). Fails when:
              - a stamped Status row's enum disagrees with entities.json
              - an entity's locales render different fact-row counts
              - any page fact row (label or value, any locale) disagrees
                with the entity's stored `facts` atoms.
            After `check`, editing a fact grid without updating the atoms
            (or vice versa) is build-breaking instead of silent. The
            legitimate workflow for a fact change: edit the page row in
            every locale it needs, run `harvest`, run `check`, run guard.
"""
import html as H
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SECTION = {'aircraft': 'aircraft', 'operator': 'operators', 'vertiport': 'vertiports',
           'route': 'routes', 'regulator': 'regulators', 'answer': 'explainers'}
LANGS = ('', 'ar', 'fr', 'de', 'zh')
STATUS_KEYS = {'Status', 'Statut', 'الحالة', '状态'}
FACT_ROW = re.compile(
    r'<div class="fact"><span class="fact-key">(.*?)</span>'
    r'<span class="fact-val"[^>]*>(.*?)</span></div>', re.S)
STAMP_ROW = re.compile(r'(<span class="fact-key">([^<]+)</span><span class="fact-val")( data-status="[^"]*")?(>)')


def clean(s):
    return H.unescape(re.sub(r'<[^>]+>', '', s)).strip()


def pages_of(slug, etype):
    for L in LANGS:
        p = ROOT / L / SECTION[etype] / f'{slug}.html' if L else ROOT / SECTION[etype] / f'{slug}.html'
        if p.exists():
            yield L or 'en', p


def grid_of(path):
    h = path.read_text(encoding='utf-8')
    return [(clean(k), clean(v)) for k, v in FACT_ROW.findall(h)]


def snake(s):
    return re.sub(r'[^a-z0-9]+', '_', s.lower()).strip('_') or 'fact'


def load():
    return json.loads((ROOT / 'entities.json').read_text(encoding='utf-8'))


def save(d):
    (ROOT / 'entities.json').write_text(json.dumps(d, indent=1, ensure_ascii=False), encoding='utf-8')


def harvest():
    d = load()
    vocab = {}
    n_rows = n_i18n = 0
    for e in d['entities']:
        grids = {lang: grid_of(p) for lang, p in pages_of(e['slug'], e['entity_type'])}
        en = grids.get('en', [])
        counts = {lang: len(g) for lang, g in grids.items()}
        if len(set(counts.values())) > 1:
            print(f'HARVEST FLAG {e["slug"]}: locale row counts differ {counts} — atoms take the EN grid; fix pages, re-harvest')
        facts, seen = [], Counter()
        for i, (k, v) in enumerate(en):
            fid = snake(k)
            seen[fid] += 1
            if seen[fid] > 1:
                fid = f'{fid}_{seen[fid]}'
            row = {'id': fid, 'k': k, 'v': v}
            i18n = {}
            for lang in ('ar', 'fr', 'de', 'zh'):
                g = grids.get(lang)
                if not g or i >= len(g):
                    continue
                lk, lv = g[i]
                diff = {}
                if lk != k:
                    diff['k'] = lk
                    vocab.setdefault(k, {}).setdefault(lang, Counter())[lk] += 1
                if lv != v:
                    diff['v'] = lv
                if diff:
                    i18n[lang] = diff
                    n_i18n += 1
            if i18n:
                row['i18n'] = i18n
            facts.append(row)
            n_rows += 1
        e['facts'] = facts
    save(d)
    vocab_out = {
        k: {lang: {'label': c.most_common(1)[0][0],
                   **({'variants': sorted(x for x in c if x != c.most_common(1)[0][0])}
                      if len(c) > 1 else {})}
            for lang, c in per.items()}
        for k, per in sorted(vocab.items())}
    (ROOT / 'data').mkdir(exist_ok=True)
    (ROOT / 'data/facts_vocab.json').write_text(
        json.dumps(vocab_out, indent=1, ensure_ascii=False), encoding='utf-8')
    conflicts = sum(1 for k in vocab_out for lang in vocab_out[k] if 'variants' in vocab_out[k][lang])
    print(f'harvest: {n_rows} fact rows -> atoms on {len(d["entities"])} entities '
          f'({n_i18n} locale diffs recorded) · vocab: {len(vocab_out)} keys, {conflicts} label variants flagged')


def stamp():
    d = load()
    stamped = skipped = 0
    for e in d['entities']:
        for lang, p in pages_of(e['slug'], e['entity_type']):
            h = p.read_text(encoding='utf-8')
            out, last, n = [], 0, 0
            for m in STAMP_ROW.finditer(h):
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
    d = load()
    fail = 0
    for e in d['entities']:
        grids, counts = {}, {}
        for lang, p in pages_of(e['slug'], e['entity_type']):
            h = p.read_text(encoding='utf-8')
            grids[lang] = grid_of(p)
            counts[lang] = len(grids[lang])
            m = re.search(r'<span class="fact-key">(?:' + '|'.join(STATUS_KEYS) + r')</span>'
                          r'<span class="fact-val" data-status="([^"]+)"', h)
            if m and m.group(1) != e['status']:
                print(f'ATOMS FAIL: {p.relative_to(ROOT)}: fact grid says {m.group(1)}, entities.json says {e["status"]}')
                fail += 1
        if len(set(counts.values())) > 1:
            print(f'ATOMS FAIL: {e["slug"]}: fact-row count differs across locales: {counts}')
            fail += 1
        facts = e.get('facts')
        if facts is None:
            continue
        if len(facts) != counts.get('en', 0):
            print(f'ATOMS FAIL: {e["slug"]}: {len(facts)} fact atoms but EN page renders {counts.get("en", 0)} rows — run harvest')
            fail += 1
            continue
        for i, row in enumerate(facts):
            for lang, g in grids.items():
                if i >= len(g):
                    continue
                exp_k = row['k'] if lang == 'en' else row.get('i18n', {}).get(lang, {}).get('k', row['k'])
                exp_v = row['v'] if lang == 'en' else row.get('i18n', {}).get(lang, {}).get('v', row['v'])
                got_k, got_v = g[i]
                if got_k != exp_k or got_v != exp_v:
                    print(f'ATOMS FAIL: {e["slug"]} [{lang}] row {i} ({row["id"]}): page says '
                          f'{got_k!r}={got_v[:40]!r}, atoms say {exp_k!r}={exp_v[:40]!r} — edit pages then run harvest')
                    fail += 1
    if fail:
        print(f'atoms check: {fail} failure(s)')
        return 1
    print('atoms check: fact grids agree with atoms in all locales; status rows agree with entities.json')
    return 0


if __name__ == '__main__':
    cmd = (sys.argv[1:] or ['stamp'])[0]
    sys.exit({'harvest': harvest, 'stamp': stamp, 'check': check}.get(cmd, stamp)() or 0)
