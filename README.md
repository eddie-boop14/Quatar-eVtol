# Qatar eVTOL — the primary-source reference for eVTOL in Qatar

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22068077.svg)](https://doi.org/10.5281/zenodo.22068077)
[![License: CC BY 4.0](https://img.shields.io/badge/License-CC_BY_4.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![Site](https://img.shields.io/badge/site-qatarevtol.com-c2410c.svg)](https://qatarevtol.com)

The documented record of Qatar's eVTOL programme — **12 entities** (aircraft,
routes, vertiports, regulators, explainers) around the EHang EH216-S Doha
trials, the Ministry of Transport strategy and the QCAA's regulatory
framework. Each record carries a status enum, a per-record *last-verified*
date and a full list of named primary sources (EHang IR, MoT and QCAA
statements, official announcements). No aggregation, no invented launch
dates: the editorial bar is **contracted, built, flight-tested, or
regulated**, and candidates that fail it are documented transparently on the
[did-not-make-the-cut](https://qatarevtol.com/explainers/did-not-make-the-cut.html) page.

Published as a static site in five languages (EN · AR · FR · DE · ZH) and as
open data. Sister project: [UAE eVTOL](https://github.com/eddie-boop14/emirates-eVtol) · [evtolemirates.com](https://evtolemirates.com).

## The data

| Surface | URL |
|---|---|
| Dataset documentation | https://qatarevtol.com/data.html |
| Full corpus (JSON, with i18n + sources) | https://qatarevtol.com/entities.json |
| Flat export (CSV) | https://qatarevtol.com/entities.csv |
| Per-entity JSON API | https://qatarevtol.com/api/index.json → `/api/{type}/{slug}.json` |
| **MCP server** (for AI agents) | `POST https://qatarevtol.com/mcp` — tools: `get_entity`, `search_entities`, `list_changes` |
| Fact-change log | [changes.html](https://qatarevtol.com/changes.html) · [changes.xml](https://qatarevtol.com/changes.xml) (Atom) · [changes.json](https://qatarevtol.com/changes.json) |
| Re-verification feed | https://qatarevtol.com/feed.xml (Atom) |
| For LLMs | [llms.txt](https://qatarevtol.com/llms.txt) · [llms-full.txt](https://qatarevtol.com/llms-full.txt) |
| OpenAPI description | https://qatarevtol.com/.well-known/openapi.json |

Quick taste — one entity, one request:

```bash
curl -s https://qatarevtol.com/api/aircraft/ehang-eh216-s-qatar.json
```

Or ask the MCP server:

```bash
curl -s -X POST https://qatarevtol.com/mcp -H 'content-type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"get_entity","arguments":{"slug":"ehang-eh216-s-qatar"}}}'
```

## How correctness is enforced

The repository is the dataset; the HTML sits on top of it, and a build gate
keeps the two from drifting:

- **`entities.json`** — source of truth: status enums, coordinates, dates,
  per-source citations, per-page fact atoms (`facts`) with a five-locale
  label vocabulary (`data/facts_vocab.json`).
- **`guard.sh`** — 24 invariants, run on every deploy. Among them: every
  page canonicalised and in the sitemap, every sitemap URL existing, fonts
  self-hosted, and *atoms check* — every fact row on every page in every
  locale must equal the stored atoms, and every rendered status must equal
  the dataset's enum. Drift is build-breaking, not silent.
- **`FRESHNESS.md`** — the re-verification protocol: primary sources are
  re-read on a risk-ranked schedule and `last_verified` moves only when the
  sources were actually re-read. Full-corpus sweep last completed
  **2026-08-22**.
- **Build tooling** — `build_data.py`, `build_og.py`, `build_api.py`,
  `build_changes.py`, `build_atoms.py`, `build_redirects.py`,
  `build_sister.py`, `freshness.py`.

## Citing

Attribution is the only condition of the CC BY 4.0 licence — it is also the
point. Cite the dataset as [`CITATION.cff`](CITATION.cff) describes, or simply:

> Qatar eVTOL Reference Dataset, qatarevtol.com.
> https://doi.org/10.5281/zenodo.22068077

The DOI always resolves to the latest versioned release.

## Independence

This is an independent reference. It is not affiliated with any operator,
regulator, or government body documented on the site. Source links go to
original documents — verify anything that matters before relying on it.
