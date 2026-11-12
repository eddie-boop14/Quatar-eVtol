#!/usr/bin/env python3
"""build_stamps.py — the dates a reader sees are the dates in the dataset.

Every entity page ends with a footer line, in five locales:

    Published 1 May 2026 · Last verified 2026-05-01
    Publié le 1er mai 2026 · Dernière vérification 2026-05-01

That line was written once, by hand, when the page was created. Sweeps moved
`last_verified` in entities.json (and with it the API, the CSV, the feeds, the
OG cards and llms-full.txt) but nothing moved the line on the page itself. By
Nov 2026 all 12 Qatar and 46 UAE entity pages said "Last verified" May–July
while the dataset said October: the one date a human visitor actually reads
was the only one not generated from the data, and it made a current site look
six months stale. An automated reader fell for it too.

The Published half had the same disease in a milder form: it was hand-written
with an English month in every locale ("Publié le 1 May 2026") and, on six UAE
pages, the whole line was left in English in all four translations. The date
lived nowhere in the dataset. Since 12 Nov 2026 each entity carries
`published` (ISO) and this script renders the whole line — label, date in the
locale's own format, separator, label, ISO date — from the data.

Same class of drift build_atoms.py closed for the Status row; same cure.

Commands:

  stamp   (default) Rewrites the footer line of every entity page, all
          locales, from entities.json's `published` and `last_verified`.
          String surgery on the line only; the surrounding markup is kept.
          Then refreshes entities.json's top-level `generated` if (and only
          if) it is older than the newest date inside the file.

  check   The gate (wired into guard.sh). Fails when
            - an entity has no `published` or `last_verified` ISO date
            - an entity page's footer line is not exactly what the data
              renders to (wrong date, English month, English label)
            - an entity page (any locale) has no footer line to stamp
            - `generated` is older than a `last_verified` or source
              `accessed` date in the file it claims to describe.

`generated` is deliberately NOT date.today(): a value that changes on every
run makes every build a diff. It moves only when the data has moved past it.

Run from the repo root after any last_verified or published change; then
./guard.sh.
"""
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SECTION = {'aircraft': 'aircraft', 'operator': 'operators', 'vertiport': 'vertiports',
           'route': 'routes', 'regulator': 'regulators', 'answer': 'explainers'}
LANGS = ('', 'ar', 'fr', 'de', 'zh')
LABELS = {  # (published, last verified) — the wording already on the pages
    'en': ('Published', 'Last verified'),
    'fr': ('Publié le', 'Dernière vérification'),
    'de': ('Veröffentlicht', 'Zuletzt geprüft'),
    'ar': ('تاريخ النشر', 'آخر تحقق'),
    'zh': ('发布日期', '最近核实'),
}
MONTHS = {
    'en': ['January', 'February', 'March', 'April', 'May', 'June', 'July',
           'August', 'September', 'October', 'November', 'December'],
    'fr': ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet',
           'août', 'septembre', 'octobre', 'novembre', 'décembre'],
    'de': ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli',
           'August', 'September', 'Oktober', 'November', 'Dezember'],
    'ar': ['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو', 'يوليو',
           'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر'],
}
# <div class="meta-foot">\n  <inner>\n</div> — inner is one line of prose with one <span class="sep">
FOOT = re.compile(r'(<div class="meta-foot">\s*)(.*?)(\s*</div>)', re.S)
ISO = re.compile(r'^\d{4}-\d{2}-\d{2}$')


def load_text():
    return (ROOT / 'entities.json').read_text(encoding='utf-8')


def pages_of(e):
    sec = SECTION.get(e['entity_type'])
    if not sec:
        return
    for L in LANGS:
        p = (ROOT / L / sec if L else ROOT / sec) / f'{e["slug"]}.html'
        if p.exists():
            yield L or 'en', p


def human_date(lang, iso):
    """The locale's own way of writing a day: 1 May 2026 · 1er mai 2026 ·
    1. Mai 2026 · 1 مايو 2026 · 2026年5月1日."""
    y, m, d = (int(x) for x in iso.split('-'))
    if lang == 'zh':
        return f'{y}年{m}月{d}日'
    month = MONTHS[lang][m - 1]
    if lang == 'fr':
        return f'{d}er {month} {y}' if d == 1 else f'{d} {month} {y}'
    if lang == 'de':
        return f'{d}. {month} {y}'
    return f'{d} {month} {y}'


def render(lang, e):
    pub, ver = LABELS[lang]
    return f'{pub} {human_date(lang, e["published"])}<span class="sep">·</span>\n  {ver} {e["last_verified"]}'


def dates_ok(e):
    return bool(ISO.match(e.get('published') or '') and ISO.match(e.get('last_verified') or ''))


def newest_date(d):
    """The latest date the file itself asserts something happened on."""
    dates = []
    for e in d['entities']:
        if ISO.match(e.get('last_verified') or ''):
            dates.append(e['last_verified'][:10])
        for s in e.get('sources', []):
            if ISO.match(s.get('accessed') or ''):
                dates.append(s['accessed'][:10])
    return max(dates) if dates else ''


def stamp():
    raw = load_text()
    d = json.loads(raw)
    changed = same = 0
    for e in d['entities']:
        if e['entity_type'] not in SECTION:
            continue
        if not dates_ok(e):
            print(f'STAMPS: {e["slug"]}: published/last_verified missing or not ISO — nothing stamped')
            continue
        for lang, p in pages_of(e):
            h = p.read_text(encoding='utf-8')
            out, n = FOOT.subn(lambda m: m.group(1) + render(lang, e) + m.group(3), h, count=1)
            if not n:
                print(f'STAMPS: {p.relative_to(ROOT)}: no meta-foot line to stamp')
                continue
            if out != h:
                p.write_text(out, encoding='utf-8')
                changed += 1
            else:
                same += 1
    print(f'stamps: footer line written to {changed} page(s), {same} already current')

    newest = newest_date(d)
    gen = d.get('generated', '')
    if newest and gen[:10] < newest:
        now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.000Z')
        # one-line string surgery: do not re-serialise 2,000 lines for one field
        new_raw, n = re.subn(r'("generated":\s*")[^"]*(")', lambda m: m.group(1) + now + m.group(2), raw)
        if n == 1:
            (ROOT / 'entities.json').write_text(new_raw, encoding='utf-8')
            print(f'stamps: generated {gen or "(unset)"} -> {now} (data ran to {newest})')
        else:
            print('STAMPS: entities.json has no single top-level "generated" field to refresh')
    return 0


def check():
    d = json.loads(load_text())
    fail = 0
    for e in d['entities']:
        if e['entity_type'] not in SECTION:
            continue
        if not dates_ok(e):
            print(f'STAMPS FAIL: {e["slug"]}: published={e.get("published")!r} last_verified={e.get("last_verified")!r} (need ISO dates)')
            fail += 1
            continue
        seen = 0
        for lang, p in pages_of(e):
            seen += 1
            m = FOOT.search(p.read_text(encoding='utf-8'))
            if not m:
                print(f'STAMPS FAIL: {p.relative_to(ROOT)}: no footer line')
                fail += 1
            elif m.group(2) != render(lang, e):
                print(f'STAMPS FAIL: {p.relative_to(ROOT)}: footer says {" ".join(m.group(2).split())!r}, '
                      f'data renders {" ".join(render(lang, e).split())!r}')
                fail += 1
        if not seen:
            print(f'STAMPS FAIL: {e["slug"]}: no page found for this entity')
            fail += 1
    newest = newest_date(d)
    gen = d.get('generated', '')
    if not ISO.match(gen[:10]):
        print(f'STAMPS FAIL: entities.json "generated" is missing or not a date: {gen!r}')
        fail += 1
    elif gen[:10] < newest:
        print(f'STAMPS FAIL: entities.json says it was generated {gen[:10]} but contains dates up to {newest}')
        fail += 1
    if fail:
        print(f'stamps check: {fail} failure(s) — run build_stamps.py')
        return 1
    print('stamps check: every page footer line (published, last verified, in its own locale) equals entities.json; generated is not older than the data')
    return 0


if __name__ == '__main__':
    cmd = (sys.argv[1:] or ['stamp'])[0]
    sys.exit({'stamp': stamp, 'check': check}.get(cmd, stamp)() or 0)
