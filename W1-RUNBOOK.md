# W1 runbook — putting the dataset in the citation graph

Everything below needs the repo owner's accounts, so it cannot be automated
from inside the repo. The repo side is already prepared: `CITATION.cff`,
`.zenodo.json`, `data.html` (Dataset + DataDownload schema, CC BY 4.0),
`/api/` endpoints, `/.well-known/openapi.json`, `changes.xml`. Total owner
effort: roughly one hour, once.

## 1. DOI via Zenodo (~15 min)

1. Make this repository **public** on GitHub (Settings → General → Danger
   Zone → Change visibility). The dataset is already CC BY 4.0 on the live
   site; the repo is the same content.
2. Log in at https://zenodo.org with the GitHub account → Account →
   GitHub → flip the toggle for this repository.
3. Create a GitHub release, tag `v2026.08` (title: "August 2026 corpus —
   post-sweep"). Zenodo archives it automatically and mints a DOI.
4. Copy the **concept DOI** (the one that always resolves to the latest
   version) into:
   - `CITATION.cff` — uncomment the `doi:` line
   - `data.html` — add `"identifier": "https://doi.org/10.5281/zenodo.XXXX"`
     to the Dataset JSON-LD (in `build_data.py`, so it survives regeneration)
   - `llms.txt` — Dataset section
5. Repeat for the Qatar repo (same steps, `Quatar-eVtol`).

## 2. Google Dataset Search (~5 min)

The Dataset markup on `data.html` is already what Dataset Search ingests.
After the DOI lands: request indexing of `data.html` in Search Console
(URL inspection → Request indexing) on both properties. Check appearance at
https://datasetsearch.research.google.com after a few days.

## 3. sameAs wiring (~10 min, after the repo is public)

Add to the Organization/WebSite JSON-LD (via `build_data.py` and the page
templates): the GitHub repo URL, the Zenodo record URL, the sister site,
and the LinkedIn page (once W5.3 exists). Do not add links that 404 —
that is why this step waits for the repo to be public.

## 4. Wikidata (~30 min, editorial judgement required)

Goal: the entities this site documents exist as structured items with
primary-source references — the layer AI answers are assembled from. Use
the primary sources already in `entities.json` as references; do NOT cite
qatarevtol.com itself as a source (the DOI'd dataset may be used where
a dataset reference fits).

Highest-value items, in order:
1. **VDX vertiport** (new item): instance of → vertiport/heliport; country,
   coordinates; significant event → GCAA certification (7 Jul 2026);
   operator → Skyports Infrastructure. Refs: Skyports 7 Jul 2026 release,
   The National 7 Jul 2026.
2. **Joby–RTA Dubai agreement**: add to the existing Joby Aviation item —
   significant event, 11 Feb 2024, ref Joby IR detail/87.
3. **EH216-S Doha flights** (Qatar side): add to EHang/EH216-S items —
   first urban pilotless passenger flights in the Middle East, Nov 2025,
   refs EHang IR + Qatar MoT.
4. Check "Transport in Dubai" / "Joby Aviation" Wikipedia articles carry the
   July 2026 certification; if you edit, cite the primary sources, follow
   the talk-page norms, and declare nothing you can't source.

## 5. What this unlocks

Every step above creates an off-domain, machine-trusted assertion that this
dataset is the record for Gulf AAM. That — not more schema — is what moves
the rankings and gets the site cited by AI answers. Track the effect in GSC
(branded queries > 0 is the first signal; see POA acceptance).
