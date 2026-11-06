#!/usr/bin/env python3
"""Keep in-page navigation on this site.

1. The homepage "Recently verified" ticker (all five locales) is rebuilt from
   this site's own entities.json: the most recently verified entries, one per
   entity type first, linking to this site's pages in the page's language. It
   had been copied from the sister site and pointed at it (Nov 2026).
2. "More aircraft / regulators / ..." cards that point at the sister site are
   removed; a block left empty goes with them. The sister-site band above the
   footer is the one deliberate cross-link.

Idempotent. Run from the repo root before build_og.py, then ./guard.sh
(invariant 28 keeps both fixed).
"""
import html as H
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent
LANGS = ("en", "ar", "fr", "de", "zh")
DIRS = {"operator": "operators", "aircraft": "aircraft", "vertiport": "vertiports",
        "route": "routes", "regulator": "regulators", "answer": "explainers"}
TYPE_LABEL = {
    "en": {"operator": "Operator", "aircraft": "Aircraft", "vertiport": "Vertiport", "route": "Route", "regulator": "Regulator", "answer": "Explainer"},
    "ar": {"operator": "مشغل", "aircraft": "طائرة", "vertiport": "محطة طائرات عمودية", "route": "مسار", "regulator": "جهة تنظيمية", "answer": "شرح"},
    "fr": {"operator": "Opérateur", "aircraft": "Aéronef", "vertiport": "Vertiport", "route": "Liaison", "regulator": "Régulateur", "answer": "Décryptage"},
    "de": {"operator": "Betreiber", "aircraft": "Luftfahrzeug", "vertiport": "Vertiport", "route": "Verbindung", "regulator": "Aufsichtsbehörde", "answer": "Erklärung"},
    "zh": {"operator": "运营方", "aircraft": "飞行器", "vertiport": "垂直起降港", "route": "航线", "regulator": "监管机构", "answer": "解读"},
}
SISTERS = ("evtolemirates.com", "qatarevtol.com")
N_TICKER = 6


def host():
    return re.search(r"<loc>https://([^/<]+)", (ROOT / "sitemap.xml").read_text(encoding="utf-8")).group(1)


def ticker_items(entities):
    live = [e for e in entities if (ROOT / DIRS[e["entity_type"]] / f"{e['slug']}.html").exists()]
    live.sort(key=lambda e: (e["last_verified"], e["name"]), reverse=True)
    picked, seen = [], set()
    for e in live:  # newest of each type first, so the strip shows the range
        if e["entity_type"] not in seen:
            picked.append(e)
            seen.add(e["entity_type"])
    for e in live:
        if len(picked) >= N_TICKER:
            break
        if e not in picked:
            picked.append(e)
    picked = picked[:N_TICKER]
    picked.sort(key=lambda e: (e["last_verified"], e["name"]), reverse=True)
    return picked


def ticker_html(items, lang):
    pre = "" if lang == "en" else f"/{lang}"
    out = []
    for e in items:
        name = e.get("i18n", {}).get(lang, {}).get("name") or e["name"]
        out.append(
            f'<a class="ticker-item" href="{pre}/{DIRS[e["entity_type"]]}/{e["slug"]}.html">'
            f'<span class="ticker-date">{e["last_verified"]}</span>'
            f'<span class="ticker-name">{H.escape(name, quote=False)}</span>'
            f'<span class="ticker-type">{TYPE_LABEL[lang][e["entity_type"]]}</span></a>')
    return "".join(out) * 2  # the strip scrolls a doubled track


def main():
    me = host()
    other = next(s for s in SISTERS if s != me)
    entities = json.loads((ROOT / "entities.json").read_text(encoding="utf-8"))["entities"]
    items = ticker_items(entities)

    tickers = 0
    for lang in LANGS:
        p = ROOT / ("index.html" if lang == "en" else f"{lang}/index.html")
        h = p.read_text(encoding="utf-8")
        new, n = re.subn(r'(<div class="ticker-track">).*?(</div>)',
                         lambda m: m.group(1) + ticker_html(items, lang) + m.group(2), h, count=1, flags=re.S)
        if n and new != h:
            p.write_text(new, encoding="utf-8")
        tickers += n

    card = re.compile(r'<a class="sibling-card reveal" href="https?://(?:www\.)?' + re.escape(other) + r'[^"]*">.*?</a>', re.S)
    empty_block = re.compile(r'<div class="sibling-eyebrow">[^<]*</div><div class="sibling-grid">\s*</div>')
    empty_section = re.compile(r'<section class="sibling-nav reveal">\s*</section>\n?')
    cards = pages = 0
    for p in sorted(ROOT.rglob("*.html")):
        if p.relative_to(ROOT).parts[0] in (".git", "og", "netlify"):
            continue
        h = p.read_text(encoding="utf-8")
        new, n = card.subn("", h)
        if not n:
            continue
        new = empty_section.sub("", empty_block.sub("", new))
        p.write_text(new, encoding="utf-8")
        cards += n
        pages += 1
    print(f"nav: ticker rebuilt on {tickers} homepages ({', '.join(e['slug'] for e in items)}) · "
          f"{cards} cross-site 'more' cards removed from {pages} pages")
    return 0


if __name__ == "__main__":
    sys.exit(main())
