# POA — evtolemirates.com + qatarevtol.com · citation layer
**Edmaster & Claudius 🦆 — bleu-canard éditions 2026**
Recorded: 2026-08-22 · Sources: `eddie-boop14/emirates-eVtol` + `eddie-boop14/Quatar-eVtol` @ `claude/website-competitiveness-demand-bfwkvf`, read directly · Google Search Console exports for both properties (3-month window, exported 2026-08-22) · competitor sweep of 2026-08-22.

Every number below was computed from the repos and the two Search Console exports. Nothing is estimated. Where a number could not be measured, the line says so.

The goal on the table: **become the reference for eVTOL in the Middle East** — the dataset AI answers are built from, the tracker journalists quote, the record the 2028 market looks things up in. This POA is the distance between the build and that goal, measured.

---

## THE PANEL

Six lenses, not six real people: each is the role one proven player in this niche has already made a living from, aimed at this build. What each one would say after reading the repos and the GSC exports:

| Lens | Modelled on | One-line verdict on this build |
|---|---|---|
| The directory editor | evtol.news (1,200+ aircraft directory, newsletter since 2016) | "The atoms are right — enums, sources, dates. But 38 of 45 UAE entities and 12 of 12 Qatar entities are ≥94 days unverified. A directory that stops verifying stops being one." |
| The publisher | eVTOL Insights (23.6k LinkedIn, 11k newsletter) | "`og:image` count across 360 pages: **0**. I could not share these pages attractively if I wanted to. There is no newsletter, no LinkedIn, no channel. Nothing here can travel." |
| The index author | SMG / AAM Reality Index | "Nothing is *releasable*. No versioned index, no DOI, no dateline. My index gets covered as news every release because it ships as a quotable artefact. Yours is a site." |
| The consumer builder | evtol.travel (vertiport DB + city pages + booking hook) | "`AED` appears on 0 pages. `Uber` — the announced booking channel — on 0 pages. The launch is Q4 2026 and the money queries have no page to land on." |
| The tail-number tracker | SkyZero (solo Substack, flight-log data, paid tier) | "Your changelog IS your proprietary dataset — status transitions with dates and receipts, which nobody else compiles for the Gulf. You're not publishing the diffs." |
| The trade database | FutureFlight / AIN | "One 161 KB monolithic JSON. No per-entity endpoint, no API description, no agent access. Machine-*readable* is done; machine-*queryable* is not started." |

The panel agrees on one thing: **the reference layer is built and correct. The citation, distribution, and freshness layers around it do not exist.** That is why 360 pages earn 11 clicks.

---

## MEASURED STATE

| | evtolemirates.com | qatarevtol.com |
|---|---|---|
| HTML pages | 262 (EN 54 + ar/fr/de/zh × 52) | 98 |
| Sitemap URLs | 256 | 96 |
| Entities | 45 (11 operator, 11 vertiport, 9 aircraft, 6 route, 5 regulator, 3 answer) | 12 (5 answer, 2 route, 2 aircraft, 2 regulator, 1 vertiport) |
| Entities ≥90 days since `last_verified` (at 2026-08-22) | **38 / 45** (21 @ 05-01, 15 @ 05-20, 2 @ 04-30) | **12 / 12** (8 @ 05-01, 4 @ 05-20) |
| Highest freshness risk (`freshness.py --json`) | `joby-s4-uae`: risk 885.9, referenced by 115 pages, 113 days stale | not run — all 12 are the backlog |
| `guard.sh` | all invariants hold (262 pages) | passing (per repo history) |
| GSC, 3-mo window | **10 clicks / 1,316 impressions / 0.76 % CTR** | **1 click / 127 impressions / 0.79 % CTR** |
| Avg position trend (Aug 1 → 20) | 34.2 → 15.1; impressions 51 → 106/day | too little data to trend |
| Branded queries in GSC | 0 of 130 queries | 0 of 5 queries |
| Consumer-intent queries in GSC | `evtol dubai` 2 impr, `vertiport dubai` 2 impr — nothing about price, booking, launch | none |
| Top impression queries | navigational for *other* entities: `gcaa certificate` 25, `gcaa private jet operator verification` 21, `department of municipal affairs and transport` 17 | junk (`cnevpost`, `bignewsnetwork.com`) |
| Device split | 85 % desktop (1,124 / 1,316) — consumer air-taxi intent is mobile | 92 impr desktop / 33 mobile |
| `og:image` | **0 / 262 pages** (`og:title` on 231 — 31 pages have no OG block at all) | **0 / 98 pages** |
| Pages mentioning `AED` or `Uber` | **0** | 0 (`QAR` on 17 pages via taxi/metro comparison) |
| `sameAs` in JSON-LD | index.html 0 · data.html 1 | not measured |
| Response headers (`netlify.toml`) | `X-Content-Type-Options`, `Referrer-Policy` only — no CSP, no HSTS, no X-Frame-Options, no Permissions-Policy | same shape |
| Machine layer shipped | `llms.txt` 12,930 B · `llms-full.txt` 74,093 B · `entities.json` 161,270 B (20,097 B gz) · `entities.csv` 34,582 B · Atom feed 25 entries (newest 2026-08-03) · `.well-known/security.txt` (canonical correct, expires 2027-07-28) · robots.txt allowlists 16 AI crawlers by name | same layer, feed 12 entries, security.txt canonical correct |
| JSON-LD vocabulary in use | Dataset, DataDownload, FAQPage, Vehicle, Place, GeoCoordinates, BreadcrumbList, WebSite, Organization | same generator |
| URL canonicalisation | one URL per page since `c31c080` (301 extensionless → `.html`); GSC still shows pre-collapse duplicates receiving impressions (e.g. `/operators/skyports-infrastructure` 14 impr extensionless vs 18 on `.html`) — expected to decay, no work | same fix landed |

**Already done — do not redo:** llms.txt/llms-full.txt, AI-crawler robots policy, CC BY 4.0 dataset with Dataset+DataDownload schema, security.txt, hreflang (7 alternates/page), FAQ/Vehicle/Geo JSON-LD, URL collapse, no-JS reveal fix, and the flagship fact is *current* — `dxb-vertiport.html` carries the 7 July 2026 certification 11 times. The spine is sound.

---

## THE DEFECTS

**D1 — The citation graph is empty.** 0 branded queries out of 135 across both properties. The site's impressions come from other entities' navigational searches (positions 18–56, 0 % CTR — unwinnable and worthless). Google holds correct 2,000-word sourced pages at position 15–25 because nothing external corroborates the domain. The dataset exists only on its own domain: not on GitHub as data, not in Google Dataset Search results that matter, no DOI, no Wikidata presence, `sameAs` essentially unset. **Format-citability is done; graph-citability was never started.**

**D2 — The launch-moment layer does not exist.** Joby's Dubai commercial launch is expected before end 2026. Booking will run through the Uber app; the reported launch fare is ~AED 350/seat. The queries that will spike — *price, how to book, routes, launch date* — have **zero pages** on this site (`AED`: 0 pages, `Uber`: 0 pages, no launch-tracker page). The sites currently ranking for them are thin (digitaldubai.ai, thenation.ae) or generalist (Khaleej Times, Time Out). This window closes at launch.

**D3 — No pulse.** The Atom feed records re-verifications only (25 entries, newest 2026-08-03). There is no page or feed of *fact changes* — status transitions with before/after and the receipt. Meanwhile the verification debt: 38/45 + 12/12 entities ≥94 days stale, top risk `joby-s4-uae` (115 referencing pages). FRESHNESS.md's own warning — "the DXB vertiport sat at 'under construction' for four weeks after it was certified" — is the standing failure mode of this backlog.

**D4 — Machine-readable, not machine-queryable.** One monolithic `entities.json`. No per-entity JSON endpoint, no index of endpoints, no OpenAPI description, no MCP server. An AI agent wanting "current status of DXB vertiport" must download 161 KB and parse, or scrape HTML. The `.well-known/` directory holds security.txt and nothing else.

**D5 — Zero distribution surface.** 0/360 pages have `og:image`; 31 Emirates pages lack any OG block. No newsletter, no LinkedIn presence, no citable release artefact. Every mechanism by which the proven players in this niche acquired their audience is absent.

**D6 — Header hygiene below reference grade.** A site asking to be treated as infrastructure ships without CSP, HSTS, X-Frame-Options, or Permissions-Policy. One `netlify.toml` block each.

---

## W1 — PUT THE DATASET IN THE CITATION GRAPH

**Goal:** the dataset resolvable and citable *off-domain*; `sameAs` closes the loop.

- **W1.1** Public data repo `gulf-aam-data` (GitHub): `entities.json` + `entities.csv` for both sites, `CITATION.cff`, `CHANGELOG.md`, CC BY 4.0, release-tagged. Repo README states the editorial bar verbatim from llms.txt.
- **W1.2** Zenodo deposit wired to the GitHub releases → **DOI**. The DOI goes on `data.html`, in the Dataset JSON-LD (`identifier`), and in llms.txt.
- **W1.3** `sameAs` on the Organization/WebSite JSON-LD of both sites: GitHub repo, Zenodo record, LinkedIn page (W5.3), sister site. Verify Dataset markup is picked up by Google Dataset Search once the DOI lands.
- **W1.4** Wikidata: create/enrich items for the entities that clear notability — VDX/DXB vertiport (world-first certified commercial vertiport, 7 Jul 2026), the Joby/RTA exclusive, EH216-S Doha flights — sourced to the *primary* sources already in `entities.json` (operator IR, GCAA, MoT). The dataset DOI is the citable object where a secondary source is needed. Do not cite the sites themselves into Wikipedia; that is not how that graph works.

## W2 — BUILD THE LAUNCH LAYER (deadline: before Joby Day 1, target 2026-10-01)

**Goal:** when "dubai air taxi price" spikes, the best page on the internet for it is here, in EN and AR.

- **W2.1** Four new EN pages + AR translations, same template and editorial bar as existing explainers: `explainers/dubai-air-taxi-price` (AED 350 launch fare, AED 150 2028 target, every figure sourced and dated) · `explainers/how-to-book-dubai-air-taxi` (Uber app + Joby app, sourced) · `explainers/dubai-air-taxi-routes-and-times` (the 4-vertiport network, DXB–Marina first) · `explainers/dubai-air-taxi-launch-tracker` (dated milestone log, updated on every event — this page IS the news hook).
- **W2.2** A `stat-line` component: one dated, standalone, quotable sentence near the top of every key page — "As of 22 August 2026, the UAE has one certified commercial vertiport (VDX at DXB, certified 7 July 2026)." Generated from `entities.json` at build so it cannot silently rot. LLMs quote sentences, not tables.
- **W2.3** Retitle where the current `<title>` serves nobody (list pages, homepage) toward query language, without touching entity-page titles that already rank top-10.

## W3 — PULSE: THE CHANGELOG IS THE PRODUCT

**Goal:** the fact-diffs become a public, subscribable artefact; the verification debt is paid and never re-accrues.

- **W3.1** Pay the debt: run the FRESHNESS.md sweep to zero — all 45 + 12 entities re-verified, `last_verified` updated even where nothing changed. Start with the risk-ranked top: `joby-s4-uae` first.
- **W3.2** `/changes.html` + `changes.xml`: every status transition as *event* — entity, old→new, date, source URL. Backfill from git history where recoverable; forward, `build_data.py` emits it from entity diffs.
- **W3.3** Cadence: fortnightly, the changelog becomes the "Gulf AAM Briefing" — a LinkedIn newsletter and email issue that is 80 % generated from W3.2. This is the only Middle-East-dedicated AAM briefing in existence; the market gap was verified 2026-08-22.
- **W3.4** Quarterly, the changelog + tracker rolls up into a versioned **Gulf AAM Launch Index** release (v2026.Q3, …) — the SMG pattern: a dated, quotable artefact pitched to the trade press each release. Nov 2026 (Dubai Airshow + VFS AAM conference *in Dubai*, Nov 24–26) is the launch release.

## W4 — AGENT LAYER: FROM READABLE TO QUERYABLE

**Goal:** an AI agent answers "status of X" from this dataset without parsing HTML.

- **W4.1** Build step emits per-entity JSON: `/api/{type}/{slug}.json` (the entity's `entities.json` record verbatim) + `/api/index.json` (slug → endpoint map, with `last_verified`). Static files, no server. Each HTML entity page gets `<link rel="alternate" type="application/json">`.
- **W4.2** `/.well-known/` grows: `openapi.json` describing W4.1 (it is an API, static or not), and an `mcp.json` pointer once W4.3 exists.
- **W4.3** MCP server (one small worker): tools `get_entity`, `search_entities`, `list_changes` over the same JSON. First AAM dataset an agent can mount. The announcement of W4.3 is itself a W3.4-grade press hook.
- **W4.4** llms.txt gains the API section; `llms-full.txt` regeneration joins the build so it can never lag `entities.json` (today both carry the same stale dates — 21 × "2026-05-01" — proving they move together; keep it that way by construction).

## W5 — DISTRIBUTION SURFACE

- **W5.1** OG image generator in the build: one branded card per page (entity name, type badge, status, "as of" date) — 360 images, zero hand-drawn. Fix the 31 pages missing OG blocks entirely.
- **W5.2** `og:image`/`twitter:card` wired into both generators; validate on LinkedIn Post Inspector for one page per template.
- **W5.3** LinkedIn organisation page; the W3.3 briefing publishes there natively.
- **W5.4** Sister-site band — each site names its sibling right before the footer: logo, label, one-line description, localized link (the loisirs74 ↔ loisirs73 pattern). Each site becomes the other's first honest backlink. **Shipped with this POA**: `build_sister.py` in both repos, idempotent between HTML markers; 230 + 65 footer-bearing pages injected, `guard.sh` green on both (262 + 98 pages).

## W6 — REFERENCE-GRADE HEADERS

One `netlify.toml` block per site: `Content-Security-Policy` (self + fonts, no inline-script exceptions the pages don't need), `Strict-Transport-Security`, `X-Frame-Options: DENY`, `Permissions-Policy` (camera/mic/geolocation off). Verify nothing breaks on the three template types, ship.

## W-Q — QATAR POSTURE

Maintenance mode, deliberately: **W3.1 sweep of all 12 entities, W4 + W5 + W6 inherited through the shared build tooling, interlink with the UAE tracker — and no W2.** The Qatar GSC export shows the market is not searching yet (127 impressions, junk queries) while positions are already good (2.7–6 where it appears). The site's job until the EHang program produces fares and routes is to stay correct and be ready. Revisit posture at the first Qatar commercial announcement.

---

## ORDER

1. **W6 + W5.1/W5.2** — independent, no editorial risk, hours not days. Nothing else should ship shareable pages before the pages are shareable.
2. **W3.1** — the sweep. Everything after this step *publishes claims*; the claims must be current first. This is also the gate FRESHNESS.md already defines — it is overdue, not new.
3. **W2** — deadline-driven by Joby Day 1. Target all four pages live (EN+AR) by 2026-10-01.
4. **W1** — needs W3.1 (you DOI a dataset once it's fresh, not before).
5. **W3.2 → W3.4** — pulse machinery, first Index release timed to Nov 24–26 Dubai week.
6. **W4** — after W1's repo exists (the API serves the same artefact the DOI names).
7. **W-Q** rides along at each step via shared tooling; its sweep happens inside step 2.

## ACCEPTANCE

- Both sitemaps: 100 % of pages carry a rendered `og:image`; LinkedIn Post Inspector shows a card on one page per template.
- `freshness.py --json` on 2026-10-01: zero entities >45 days on either site.
- The four W2 pages live in EN+AR before Joby's first commercial flight; each carries a dated stat-line and ≥3 primary sources.
- Dataset resolvable at a DOI; `data.html` Dataset JSON-LD carries the DOI as `identifier`; the GitHub data repo has ≥1 tagged release.
- `/changes.xml` validates and contains every status transition after its ship date; the fortnightly briefing has published ≥2 issues before Nov 24.
- An agent with only the MCP endpoint answers "what is the status of the DXB vertiport and when did it change?" correctly, with the source URL — no HTML involved.
- GSC, first re-check 2026-12-01: ≥1 branded query on evtolemirates.com; ≥1 W2 page with impressions in the top 10 for a price/booking/launch query. (These are outcome metrics — the panel judges the work above by the artefacts, and the market by these.)

## PROGRESS LOG

- **2026-08-22 · Step 1 shipped** — W6 headers (CSP/HSTS/XFO/Permissions-Policy) and W5.1/W5.2 OG card layer (53+20 branded cards, site faces, full-page wiring, hub OG blocks) live on both repos; sister band extended to all three footer templates.
- **2026-08-22 · Step 2 shipped (W3.1)** — full-corpus sweep: 57 entities re-verified against primary sources, 5 changed (AUD vertiport → under_construction with RTA-confirmed Marina identity; Skyports claim synced; Archer RTC programme added; Joby-vs-Archer operator corrected; QCAA Law No. 10 of 2026), 9 dead source URLs re-pointed, `last_verified` = 2026-08-22 corpus-wide. See SWEEP-2026-08-22.md in each repo.
- **2026-08-22 · Step 3 shipped (W2.1–W2.3)** — four launch-layer explainers live in EN + AR as `answer` entities (price / how-to-book / routes-and-times / launch-tracker), fully integrated (entities.json, sitemap, redirects, hub + homepage cards, llms files, OG cards). Editorial note: the circulating ‘AED 350’ fare was checked and is unsourced — the price page says so explicitly, with the RTA’s ‘price not decided’ quote. Dated stat-lines on all four pages (W2.2); homepage + hub titles moved to query language (W2.3). fr/de/zh twins of the four pages are recorded translation debt.
- **2026-08-23 · Enum-layer gate shipped** — audit found the loisirs74 failure mode live: the DXB vertiport's Status fact row still said "technical completion" in all five locales a month after certification (the sweep's hero/FAQ edits never reached the hand-synced fact grid). Fixed in 5 locales; `build_atoms.py` now stamps `data-status="<enum>"` from entities.json onto every Status fact row (170 + 40 pages) and guard check 24 fails the build on drift or locale fact-count divergence. Measured baseline: entity-level atoms 49/49 complete; locale fact parity 0/49 mismatches; remaining backlog **E1**: the 133 free-form fact keys (Operator, Builder, dates, capacities …) are still prose ×5 locales — promoting them to typed atoms in entities.json with a per-locale label vocabulary is the next enum-layer increment.
- **2026-08-23 · E1 shipped — the full enum/atoms layer** — `build_atoms.py harvest` backfilled every fact grid into entities.json `facts` atoms (322 rows / 49 entities on evtolemirates.com, 78 / 12 on qatarevtol.com; EN label+value canonical, per-locale diffs stored only where a locale genuinely differs — 1,020 + 237 recorded), and derived `data/facts_vocab.json`, the 45- and 14-key five-locale label vocabulary learned from the pages' own human translations (3 label variants flagged, all legitimate synonyms of 'Aircraft'). The gate now enforces **page ⇄ atom equality for every fact row in every locale on every build** (negative-tested); facts flow into `/api/{type}/{slug}.json` and `llms-full.txt`. Editorial workflow for a fact change: edit the row in every locale → `python3 build_atoms.py harvest` → `check` → `guard.sh`. W1 also closed this date: both Zenodo DOIs minted and wired (UAE 10.5281/zenodo.22068156 · Qatar 10.5281/zenodo.22068077).
- **Next in order:** W1 (data repo + Zenodo DOI + Dataset Search + Wikidata — needs owner accounts), then W3.2–W3.4 (changelog feed, briefing, quarterly index), then W4 (per-entity JSON, MCP).

## THE BAR

"Reference" in this domain, 2028 definition: the dataset AI systems answer from, the tracker journalists lift numbers out of, the changelog analysts subscribe to — with a receipt trail no competitor bothered to keep. The build already has the receipts. This POA is the part where anyone else finds out.
