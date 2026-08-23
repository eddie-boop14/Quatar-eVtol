#!/usr/bin/env python3
"""build_changes.py — the fact-change log as a product (POA W3.2).

feed.xml answers "what was recently re-verified"; this answers the question
journalists and agents actually have at the launch moment: WHAT CHANGED —
which entity moved to which status, when, on whose say-so.

Events are recovered from the git history of entities.json (status
transitions and entity additions between consecutive revisions), so the log
is reproducible from the repository alone and cannot drift from the data.

Outputs:
  changes.html  human changelog, cloned from data.html's shell
  changes.xml   Atom feed of the same events

Run from the repo root after any entities.json change; then ./guard.sh.
"""
import html as H
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def host_of():
    m = re.search(r'<loc>https://([^/<]+)', (ROOT / 'sitemap.xml').read_text(encoding='utf-8'))
    return m.group(1)


def revisions():
    out = subprocess.run(
        ['git', 'log', '--format=%H %ad', '--date=short', '--reverse', '--', 'entities.json'],
        cwd=ROOT, capture_output=True, text=True, check=True).stdout.split('\n')
    return [line.split() for line in out if line.strip()]


def snapshot(rev):
    out = subprocess.run(['git', 'show', f'{rev}:entities.json'],
                         cwd=ROOT, capture_output=True, text=True)
    if out.returncode != 0:
        return None
    data = json.loads(out.stdout)
    return {e['slug']: e for e in data['entities']}


def collect_events():
    events = []  # (date, kind, slug, name, entity_type, old, new)
    revs = revisions()
    prev = None
    for i, (rev, date) in enumerate(revs):
        cur = snapshot(rev)
        if cur is None:
            continue
        if prev is None:
            if i == 0:
                events.append((date, 'published', None,
                               f'Corpus first published — {len(cur)} entities', None, None, None))
        else:
            for slug, e in cur.items():
                if slug not in prev:
                    events.append((date, 'added', slug, e['name'], e['entity_type'],
                                   None, e['status']))
                elif e['status'] != prev[slug]['status']:
                    events.append((date, 'status', slug, e['name'], e['entity_type'],
                                   prev[slug]['status'], e['status']))
            for slug, e in prev.items():
                if slug not in cur:
                    events.append((date, 'removed', slug, e['name'], e['entity_type'],
                                   e['status'], None))
        prev = cur
    events.sort(key=lambda ev: ev[0], reverse=True)
    return events


def label(s):
    return (s or '').replace('_', ' ')


def event_line(ev):
    date, kind, slug, name, etype, old, new = ev
    if kind == 'published':
        return name
    page = f'/{ {"answer": "explainers"}.get(etype, etype + "s") }/{slug}.html'
    link = f'<a href="{page}">{H.escape(name, quote=False)}</a>'
    if kind == 'added':
        return f'{link} added to the corpus ({etype}, status: {label(new)})'
    if kind == 'removed':
        return f'{H.escape(name, quote=False)} removed from the corpus ({etype})'
    return f'{link}: status {label(old)} → <strong>{label(new)}</strong>'


def write_xml(events, host):
    updated = events[0][0] if events else '1970-01-01'
    entries = []
    for date, kind, slug, name, etype, old, new in events:
        eid = f'tag:{host},{date}:{slug or "corpus"}:{kind}:{new or ""}'
        title = re.sub(r'<[^>]+>', '', event_line((date, kind, slug, name, etype, old, new)))
        entries.append(
            f'<entry><id>{H.escape(eid)}</id><title>{H.escape(title, quote=False)}</title>'
            f'<updated>{date}T00:00:00Z</updated>'
            f'<link href="https://{host}/changes.html"/>'
            f'<summary>{H.escape(title, quote=False)}</summary></entry>')
    xml = ('<?xml version="1.0" encoding="utf-8"?>\n'
           f'<feed xmlns="http://www.w3.org/2005/Atom">\n'
           f'<title>{host} — fact changes</title>\n'
           f'<id>tag:{host},2026:changes</id>\n'
           f'<updated>{updated}T00:00:00Z</updated>\n'
           f'<link href="https://{host}/changes.xml" rel="self"/>\n'
           f'<link href="https://{host}/changes.html"/>\n'
           + '\n'.join(entries) + '\n</feed>\n')
    (ROOT / 'changes.xml').write_text(xml, encoding='utf-8')
    return len(entries)


def write_json(events, host):
    rows = [{'date': d, 'kind': k, 'slug': sl, 'name': n, 'entity_type': t,
             'old_status': o, 'new_status': nw}
            for d, k, sl, n, t, o, nw in events]
    (ROOT / 'changes.json').write_text(
        json.dumps({'site': host, 'events': rows}, indent=1, ensure_ascii=False), encoding='utf-8')


def write_html(events, host):
    shell = (ROOT / 'data.html').read_text(encoding='utf-8')
    title = 'Fact changes — every status transition, dated'
    desc = ('The change log of this reference: every entity added and every status '
            'transition, recovered from the dataset’s own revision history. '
            'Machine-readable twin: /changes.xml.')
    head = re.search(r'<head>.*?</head>', shell, re.S).group(0)
    head = re.sub(r'<title>[^<]*</title>', f'<title>{title}</title>', head)
    head = re.sub(r'(<meta name="description" content=")[^"]*', r'\g<1>' + H.escape(desc, quote=True), head)
    head = head.replace('href="https://' + host + '/data.html"', 'href="https://' + host + '/changes.html"')
    head = re.sub(r'(<meta property="og:url" content=")[^"]*', r'\g<1>' + f'https://{host}/changes.html', head)
    for prop in ('og:title', 'twitter:title'):
        head = re.sub(f'(<meta (?:property|name)="{prop}" content=")[^"]*', r'\g<1>' + title, head)
    for prop in ('og:description', 'twitter:description'):
        head = re.sub(f'(<meta (?:property|name)="{prop}" content=")[^"]*',
                      r'\g<1>' + H.escape(desc, quote=True), head)
    # drop the Dataset JSON-LD (it belongs to data.html), keep everything else
    head = re.sub(r'<script type="application/ld\+json">.*?</script>', '', head, flags=re.S)
    # the changes feed announces itself alongside the site feed
    head = head.replace('</head>',
                        f'<link rel="alternate" type="application/atom+xml" title="Fact changes" href="https://{host}/changes.xml">\n</head>')

    header = re.search(r'<body>.*?</header>', shell, re.S).group(0)
    tail = re.search(r'<!-- sister-site -->.*', shell, re.S).group(0)

    rows = ''.join(
        f'<div class="spec-row"><div class="spec-k">{date}</div>'
        f'<div class="spec-v">{event_line(ev)}</div></div>'
        for ev in events for date in [ev[0]])
    body = f'''{header}
<section class="hub-hero"><div class="hub-hero-inner">
  <div class="hub-eyebrow"><span class="pip"></span>Change log</div>
  <h1 class="hub-hero-title">Fact changes</h1>
  <p class="hero-lead">Every entity added and every status transition in this reference, dated and in reverse order — recovered from the dataset&#x27;s own revision history, so this log cannot drift from the data. Subscribe: <a href="/changes.xml">changes.xml</a> (Atom). Re-verification activity is a separate feed: <a href="/feed.xml">feed.xml</a>.</p>
</div></section>
<div class="inner">
<div class="spec-table">{rows}</div>
</div>
{tail}'''
    doc = f'<!DOCTYPE html>\n<html lang="en" dir="ltr">\n{head}\n{body}'
    (ROOT / 'changes.html').write_text(doc, encoding='utf-8')


def ensure_sitemap(host):
    sm = ROOT / 'sitemap.xml'
    t = sm.read_text(encoding='utf-8')
    if f'https://{host}/changes.html' in t:
        return
    from datetime import date
    t = t.replace('</urlset>',
                  f'<url><loc>https://{host}/changes.html</loc></url>\n</urlset>')
    sm.write_text(t, encoding='utf-8')


def main():
    host = host_of()
    events = collect_events()
    n = write_xml(events, host)
    write_json(events, host)
    write_html(events, host)
    ensure_sitemap(host)
    print(f'changes: {n} events -> changes.html + changes.xml')
    return 0


if __name__ == '__main__':
    sys.exit(main())
