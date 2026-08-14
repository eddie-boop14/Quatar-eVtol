#!/usr/bin/env python3
"""
build_data.py — turn entities.json from a build artifact into a citable dataset.

Why this exists. Google Search Console says 94 of 96 Qatar pages are "Discovered
— currently not indexed". That is a web-index verdict on a young domain with no
inbound links, and no amount of further technical work moves it. But Google
Dataset Search is a SEPARATE index, it is far less contested, and it wants
exactly the shape this site already has: a sourced, versioned, licensed corpus
with a per-record freshness field.

So this publishes the corpus as a product rather than a build artifact:

  data.html      documented landing page + schema.org/Dataset JSON-LD
  entities.csv   flat export -- what a journalist or analyst actually opens
  feed.xml       Atom feed of recently re-verified entities

The licence is CC BY 4.0 on purpose. Attribution is the citation mechanism:
anyone who uses the data owes a link, and links are the thing the site does not
have. That is the whole strategy in one line.

Everything is generated from entities.json. Never hand-edit the outputs.
Regenerate, then run ./guard.sh.
"""
import json, csv, sys, os, html, re
from datetime import date, datetime, timezone

CFG = {
    'evtolemirates.com': dict(
        title='UAE eVTOL Reference Dataset',
        region='United Arab Emirates',
        brand='UAE <em>eVTOL</em>',
        sister='https://qatarevtol.com',
    ),
    'qatarevtol.com': dict(
        title='Qatar eVTOL Reference Dataset',
        region='Qatar',
        brand='Qatar <em>eVTOL</em>',
        sister='https://evtolemirates.com',
    ),
}
PRIMARY_TYPES = {'primary', 'operator-ir', 'regulatory', 'government'}
# an editorial note is not a source; a citable source without a URL is not citable
_citable = lambda s: s.get('type') in PRIMARY_TYPES and s.get('url')
CSV_FIELDS = ['slug', 'name', 'entity_type', 'status', 'country', 'city',
              'latitude', 'longitude', 'last_verified',
              'primary_source_count', 'primary_source_urls', 'meta_description']


def host_of():
    m = re.search(r'<loc>https://([^/<]+)', open('sitemap.xml', encoding='utf-8').read())
    return m.group(1)


def load():
    return json.load(open('entities.json', encoding='utf-8'))


def head_block():
    """Reuse the real <head> so the page is native, not a bolt-on.

    guard.sh requires every page to declare @font-face and a preload hint --
    lifting the block wholesale is the only way to satisfy that and stay
    visually identical when the design system changes.
    """
    s = open('vertiports.html', encoding='utf-8').read()
    head = re.search(r'<head>(.*?)</head>', s, re.S).group(1)
    # drop page-specific tags; data.html supplies its own
    for pat in [r'<title>.*?</title>', r'<meta name="description"[^>]*>',
                r'<link[^>]*rel="canonical"[^>]*>', r'<meta property="og:[^>]*>',
                r'<meta name="twitter:[^>]*>', r'<link[^>]*rel="alternate"[^>]*>',
                r'<script type="application/ld\+json">.*?</script>']:
        head = re.sub(pat, '', head, flags=re.S)
    return head.strip()


def csv_rows(data):
    for e in data['entities']:
        srcs = [s for s in e.get('sources', []) if _citable(s)]
        yield {
            'slug': e['slug'], 'name': e['name'], 'entity_type': e['entity_type'],
            'status': e.get('status', ''), 'country': e.get('country', ''),
            'city': e.get('city', ''), 'latitude': e.get('latitude', ''),
            'longitude': e.get('longitude', ''),
            'last_verified': e.get('last_verified', ''),
            'primary_source_count': len(srcs),
            'primary_source_urls': ' | '.join(s['url'] for s in srcs),
            'meta_description': e.get('meta_description', ''),
        }


def write_csv(data, path='entities.csv'):
    with open(path, 'w', encoding='utf-8', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=CSV_FIELDS)
        w.writeheader()
        for row in csv_rows(data):
            w.writerow(row)
    return sum(1 for _ in data['entities'])


def write_feed(data, host, cfg, path='feed.xml'):
    """Recently re-verified entities. Gives a crawler a reason to come back and
    an aggregator something to subscribe to -- neither of which a sitemap does."""
    ents = sorted(data['entities'], key=lambda e: e.get('last_verified', ''), reverse=True)[:25]
    updated = (max(e.get('last_verified', '') for e in data['entities']) or
               date.today().isoformat()) + 'T00:00:00Z'
    esc = lambda t: html.escape(str(t), quote=True)
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<feed xmlns="http://www.w3.org/2005/Atom">',
           f'<title>{esc(cfg["title"])} — recently verified</title>',
           f'<subtitle>Entities whose claims were most recently re-checked against '
           f'their primary sources.</subtitle>',
           f'<link href="https://{host}/feed.xml" rel="self"/>',
           f'<link href="https://{host}/"/>',
           f'<id>https://{host}/</id>',
           f'<updated>{updated}</updated>',
           f'<rights>CC BY 4.0</rights>']
    for e in ents:
        url = f'https://{host}/{e["entity_type"]}s/{e["slug"]}.html'
        lv = e.get('last_verified', date.today().isoformat())
        out += ['<entry>',
                f'<title>{esc(e["name"])}</title>',
                f'<link href="{esc(url)}"/>',
                f'<id>{esc(url)}</id>',
                f'<updated>{lv}T00:00:00Z</updated>',
                f'<category term="{esc(e["entity_type"])}"/>',
                f'<category term="{esc(e.get("status",""))}"/>',
                f'<summary>{esc(e.get("meta_description",""))}</summary>',
                '</entry>']
    out.append('</feed>')
    open(path, 'w', encoding='utf-8').write('\n'.join(out) + '\n')
    return len(ents)


def dataset_jsonld(data, host, cfg):
    ents = data['entities']
    types = sorted({e['entity_type'] for e in ents})
    newest = max((e.get('last_verified', '') for e in ents), default='')
    srcs = {s['url'] for e in ents for s in e.get('sources', []) if _citable(s)}
    return {
        '@context': 'https://schema.org/',
        '@type': 'Dataset',
        'name': cfg['title'],
        'alternateName': f'{cfg["region"]} eVTOL entities — operators, aircraft, '
                         'vertiports, routes, regulators',
        'description': (
            f'A primary-source reference dataset of the {cfg["region"]} electric '
            f'vertical take-off and landing (eVTOL) sector: {len(ents)} entities across '
            f'{", ".join(types)}, each with status, coordinates where applicable, a '
            f'per-entity last-verified date, and citations to named primary sources '
            f'({len(srcs)} distinct source documents). Every claim traces to company '
            f'investor relations, a regulator, or a government body. Aggregators and '
            f'trade press are never cited. Records are re-checked against their sources '
            f'on a monthly schedule and the verification date is published per record.'),
        'url': f'https://{host}/data.html',
        'sameAs': f'https://{host}/entities.json',
        'license': 'https://creativecommons.org/licenses/by/4.0/',
        'isAccessibleForFree': True,
        'dateModified': newest,
        'creator': {'@type': 'Organization', 'name': cfg['title'].replace(' Reference Dataset', ''),
                    'url': f'https://{host}/'},
        'spatialCoverage': {'@type': 'Place', 'name': cfg['region']},
        'keywords': ['eVTOL', 'air taxi', 'vertiport', 'advanced air mobility',
                     'urban air mobility', cfg['region'], 'aviation infrastructure'],
        'variableMeasured': [
            {'@type': 'PropertyValue', 'name': 'status',
             'description': 'Lifecycle state: planned, announced, design_approved, '
                            'under_construction, trial_only, certified, operational, '
                            'orphaned, decommissioned'},
            {'@type': 'PropertyValue', 'name': 'last_verified',
             'description': 'Date the record was last re-checked against its primary sources'},
            {'@type': 'PropertyValue', 'name': 'sources',
             'description': 'Named primary-source citations with URL, type and access date'},
        ],
        'distribution': [
            {'@type': 'DataDownload', 'encodingFormat': 'application/json',
             'contentUrl': f'https://{host}/entities.json',
             'name': 'Full dataset (JSON, includes five-language i18n and full source lists)'},
            {'@type': 'DataDownload', 'encodingFormat': 'text/csv',
             'contentUrl': f'https://{host}/entities.csv',
             'name': 'Flat export (CSV, one row per entity)'},
            {'@type': 'DataDownload', 'encodingFormat': 'application/atom+xml',
             'contentUrl': f'https://{host}/feed.xml',
             'name': 'Atom feed of recently re-verified entities'},
        ],
    }


def write_data_page(data, host, cfg, path='data.html'):
    ents = data['entities']
    from collections import Counter
    by_type = Counter(e['entity_type'] for e in ents)
    by_status = Counter(e.get('status', '') for e in ents)
    srcs = {s['url'] for e in ents for s in e.get('sources', []) if _citable(s)}
    newest = max((e.get('last_verified', '') for e in ents), default='')
    oldest = min((e.get('last_verified', '') for e in ents), default='')

    rows = lambda c: ''.join(
        f'<div class="spec-row"><div class="spec-k">{html.escape(k or "—")}</div>'
        f'<div class="spec-v">{v}</div></div>' for k, v in sorted(c.items(), key=lambda x: -x[1]))

    jsonld = json.dumps(dataset_jsonld(data, host, cfg), ensure_ascii=False, indent=1)

    body = f"""<body>
<header class="hub-nav">
  <div class="hub-nav-inner">
    <a class="hub-brand" href="/">
      <span class="brand-mark" aria-hidden="true"></span>
      <span>{cfg['brand']}</span>
    </a>
  </div>
</header>

<section class="hub-hero">
  <div class="hub-hero-inner">
    <div class="hub-eyebrow"><span class="pip"></span>Dataset · CC BY 4.0</div>
    <h1 class="hero-title">{html.escape(cfg['title'])}</h1>
    <p class="hero-lead">Every entity in this reference, as data. {len(ents)} records across
    {len(by_type)} entity types, {len(srcs)} distinct primary-source documents, a
    per-record verification date, and five languages. Free to use with attribution.</p>
  </div>
</section>

<article class="body">

<h2 id="download">Download</h2>
<div class="spec-table">
<div class="spec-row"><div class="spec-k"><a href="/entities.json">entities.json</a></div>
<div class="spec-v">Full dataset. Five-language <code>i18n</code> block and complete source
lists per entity. This is the source of truth the site is built from.</div></div>
<div class="spec-row"><div class="spec-k"><a href="/entities.csv">entities.csv</a></div>
<div class="spec-v">Flat export, one row per entity, primary-source URLs pipe-separated.</div></div>
<div class="spec-row"><div class="spec-k"><a href="/feed.xml">feed.xml</a></div>
<div class="spec-v">Atom feed of the most recently re-verified entities.</div></div>
</div>

<h2 id="contents">What is in it</h2>
<div class="spec-table">{rows(by_type)}</div>
<p>By lifecycle status:</p>
<div class="spec-table">{rows(by_status)}</div>

<h2 id="standard">The editorial standard</h2>
<p><strong>Primary sources only.</strong> Every claim traces to company investor relations,
a regulator, or a government body. Trade press and aggregators may point us at a story;
they are never cited as the source of a fact. An entity with no primary source on file is
not published.</p>
<p><strong>Verification dates are published, not implied.</strong> Each record carries
<code>last_verified</code> — the date its claims were last re-checked against those sources.
Currently {html.escape(oldest)} to {html.escape(newest)}. Records are re-checked on a monthly
schedule; the riskiest are re-read first, ranked by age weighted by how fast that class of
claim moves.</p>
<p><strong>A new fact does not erase the old one.</strong> When something changes, the
historical event keeps its timeline entry and its citation. Only claims phrased as current
status are rewritten. The history is part of the record.</p>
<p><strong>Targets are labelled as targets.</strong> "Targeted for Q3 2026" is a target.
"Launching Q3 2026" would be a claim we cannot source, so we do not make it.</p>

<h2 id="cite">How to cite</h2>
<p>The licence is <a href="https://creativecommons.org/licenses/by/4.0/"
rel="license noopener" target="_blank">CC BY 4.0</a>. Use it commercially, redistribute it,
build on it — attribution is the only condition.</p>
<pre><code>{html.escape(cfg['title'])}. {html.escape(host)}, {html.escape(newest)}.
https://{html.escape(host)}/data.html — CC BY 4.0</code></pre>
<p>If you are an operator, regulator or vertiport developer and a record about you is wrong,
that is a bug and we want it: the correction path is a primary source we can read.</p>

<h2 id="sister">Companion dataset</h2>
<p>The same standard, applied to the neighbouring market:
<a href="{cfg['sister']}/data.html" rel="noopener">{cfg['sister'].replace('https://','')}</a>.</p>

</article>
<footer class="site-foot"><p>CC BY 4.0 · generated from entities.json · {html.escape(newest)}</p></footer>
</body>"""

    doc = f"""<!DOCTYPE html>
<html dir="ltr" lang="en">
<head>
<title>{html.escape(cfg['title'])} — free, primary-sourced, CC BY 4.0</title>
<meta name="description" content="{len(ents)} eVTOL entities in {html.escape(cfg['region'])} as open data: operators, aircraft, vertiports, routes and regulators, each with status, coordinates, a verification date and named primary sources. JSON and CSV, CC BY 4.0.">
<link rel="canonical" href="https://{host}/data.html">
<meta property="og:title" content="{html.escape(cfg['title'])}">
<meta property="og:description" content="{len(ents)} entities, {len(srcs)} primary sources, per-record verification dates. Free with attribution.">
<meta property="og:url" content="https://{host}/data.html">
<meta property="og:type" content="website">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{html.escape(cfg['title'])}">
<meta name="twitter:description" content="{len(ents)} entities, {len(srcs)} primary sources, CC BY 4.0.">
{head_block()}
<script type="application/ld+json">
{jsonld}
</script>
</head>
{body}
</html>
"""
    open(path, 'w', encoding='utf-8').write(doc)
    return len(ents), len(srcs)


def main():
    host = host_of()
    cfg = CFG[host]
    data = load()
    n = write_csv(data)
    f = write_feed(data, host, cfg)
    e, s = write_data_page(data, host, cfg)
    print(f"  {host}")
    print(f"    entities.csv : {n} rows")
    print(f"    feed.xml     : {f} entries")
    print(f"    data.html    : {e} entities, {s} distinct primary sources")


main()
