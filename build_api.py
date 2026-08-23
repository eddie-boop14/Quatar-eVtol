#!/usr/bin/env python3
"""build_api.py — per-entity JSON endpoints (POA W4.1/W4.2).

entities.json is one monolith; an agent answering one question should not
have to download and parse the whole corpus. This emits:

  api/index.json           slug -> endpoint map with status + last_verified
  api/{type}/{slug}.json   the entity's record verbatim, plus provenance
  .well-known/openapi.json minimal OpenAPI 3.1 description of the above

and adds <link rel="alternate" type="application/json"> to every entity
page (all locales) between HTML markers, idempotently.

Static files only — no server. Run from the repo root; then ./guard.sh.
"""
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SECTION_OF = {'aircraft': 'aircraft', 'operator': 'operators', 'vertiport': 'vertiports',
              'route': 'routes', 'regulator': 'regulators', 'answer': 'explainers'}
MARK_OPEN, MARK_CLOSE = '<!-- api-link -->', '<!-- /api-link -->'
LANG_DIRS = {'ar', 'fr', 'de', 'zh'}


def host_of():
    m = re.search(r'<loc>https://([^/<]+)', (ROOT / 'sitemap.xml').read_text(encoding='utf-8'))
    return m.group(1)


def main():
    host = host_of()
    data = json.loads((ROOT / 'entities.json').read_text(encoding='utf-8'))
    ents = data['entities']
    api = ROOT / 'api'

    index = []
    for e in ents:
        section = SECTION_OF[e['entity_type']]
        d = api / e['entity_type']
        d.mkdir(parents=True, exist_ok=True)
        record = {
            'about': {
                'source': f'https://{host}/entities.json',
                'page': f'https://{host}/{section}/{e["slug"]}.html',
                'license': 'CC BY 4.0 — https://creativecommons.org/licenses/by/4.0/',
                'attribution': host,
            },
            'entity': e,
        }
        (d / f'{e["slug"]}.json').write_text(
            json.dumps(record, indent=1, ensure_ascii=False), encoding='utf-8')
        index.append({
            'slug': e['slug'], 'name': e['name'], 'entity_type': e['entity_type'],
            'status': e['status'], 'last_verified': e['last_verified'],
            'endpoint': f'https://{host}/api/{e["entity_type"]}/{e["slug"]}.json',
            'page': f'https://{host}/{section}/{e["slug"]}.html',
        })
    (api / 'index.json').write_text(json.dumps({
        'title': f'{host} entity API',
        'license': 'CC BY 4.0',
        'generated': date.today().isoformat(),
        'count': len(index),
        'entities': index,
    }, indent=1, ensure_ascii=False), encoding='utf-8')

    wk = ROOT / '.well-known'
    wk.mkdir(exist_ok=True)
    (wk / 'openapi.json').write_text(json.dumps({
        'openapi': '3.1.0',
        'info': {'title': f'{host} entity API', 'version': date.today().isoformat(),
                 'description': 'Static, read-only JSON for every entity in the reference. '
                                'CC BY 4.0; per-record primary sources and verification dates included.',
                 'license': {'name': 'CC BY 4.0', 'url': 'https://creativecommons.org/licenses/by/4.0/'}},
        'servers': [{'url': f'https://{host}'}],
        'paths': {
            '/api/index.json': {'get': {'summary': 'List every entity with status, last_verified and endpoint URL',
                                        'responses': {'200': {'description': 'Entity index'}}}},
            '/api/{entityType}/{slug}.json': {'get': {
                'summary': 'One entity record: status, claim, coordinates, i18n, primary sources',
                'parameters': [
                    {'name': 'entityType', 'in': 'path', 'required': True,
                     'schema': {'enum': sorted(SECTION_OF)}},
                    {'name': 'slug', 'in': 'path', 'required': True, 'schema': {'type': 'string'}}],
                'responses': {'200': {'description': 'Entity record'}, '404': {'description': 'Unknown entity'}}}},
        },
    }, indent=1), encoding='utf-8')

    # wire <link rel="alternate" type="application/json"> into entity pages
    slugs = {e['slug']: e['entity_type'] for e in ents}
    wired = 0
    for path in ROOT.rglob('*.html'):
        rel = path.relative_to(ROOT)
        if rel.parts[0] in ('.git', 'og', 'api'):
            continue
        parts = list(rel.parts)
        if parts and parts[0] in LANG_DIRS:
            parts = parts[1:]
        if len(parts) != 2:
            continue
        stem = Path(parts[-1]).stem
        if stem not in slugs:
            continue
        href = f'https://{host}/api/{slugs[stem]}/{stem}.json'
        block = f'{MARK_OPEN}<link rel="alternate" type="application/json" href="{href}">{MARK_CLOSE}\n'
        h = path.read_text(encoding='utf-8')
        if MARK_OPEN in h:
            new = re.sub(re.escape(MARK_OPEN) + r'.*?' + re.escape(MARK_CLOSE) + r'\n?',
                         block, h, count=1, flags=re.S)
        else:
            new = h.replace('</head>', block + '</head>', 1)
        if new != h:
            path.write_text(new, encoding='utf-8')
        wired += 1

    print(f'api: {len(index)} entity endpoints + index.json + .well-known/openapi.json · {wired} pages wired')
    return 0


if __name__ == '__main__':
    sys.exit(main())
