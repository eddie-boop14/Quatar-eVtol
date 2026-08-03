# Freshness protocol

This site's only real asset is being right. A directory that says a certified
vertiport is "under construction" is worse than no directory: it looks
authoritative and it is wrong, and a reader who catches it once stops trusting
everything else.

No script can detect a fact going stale. `freshness.py` ranks entities by risk
and hands you the primary-source URLs; the judgement is yours. This file is how
to exercise it. Read it fully before editing anything — most of it was learned
by getting it wrong.

---

## The sweep

```bash
python3 freshness.py --top 8          # the work-list
python3 freshness.py --json           # same, for an agent
./guard.sh                            # must pass before and after
```

1. **Take the top N by risk.** Do not skip down the list to something easier.
2. **Re-read every primary source listed.** Actually fetch them. Do not decide
   from memory that nothing has changed — that is how the DXB vertiport sat at
   "under construction" for four weeks after it was certified.
3. **Search for what the sources do not mention.** A press release tells you
   what happened, not what stopped happening. A programme that has gone quiet
   is news too.
4. **For anything that moved, apply the edit protocol below.**
5. **Update `last_verified` to the date you re-read the sources** — even if
   nothing changed. An entity confirmed unchanged is fresher than one nobody
   looked at, and the score should reflect that.
6. **Run `./guard.sh`.** It blocks the deploy on twelve invariants. If it fails,
   read the message; each one names the regression it prevents.

## The edit protocol — the part that is actually hard

**A new event does not delete the old one.** When the GCAA certified DXB
Vertiport on 7 July 2026, the site carried 169 mentions of its 16 April 2026
technical completion. Both events are real. Sorting them was the whole job:

| Keep exactly as written | Rewrite |
|---|---|
| Timeline entries (`tl-item`) dated to the old event | Sentences phrased as **current status** — "As of 20 May 2026, X is technically complete" |
| Source citations of the old release | Status badges, `data-status`, `card-status`, `fact-val` |
| "According to <source>'s <date> announcement, …" | Meta / og / twitter descriptions |
| Sentences reporting what a document *said* | FAQ answers to "when will X open / what is X's status" |

If you cannot tell which bucket a sentence is in, ask: *would this sentence have
been false the day before the new event?* If no, it is history — keep it. If
yes, it was a status claim — rewrite it.

**Add, do not just amend.** A superseded event earns a new timeline entry and a
new primary source citation, not only an edited sentence. The history is part of
the value.

## The five-language pass

The `fr/`, `de/`, `ar/`, `zh/` trees are **DOM-aligned copies** of the English
pages. Verify before relying on it:

```python
# identical text-node counts, excluding .auto-trans-banner
```

Because they are aligned, address each edit **by text-node index** computed from
the English diff, not by trying to match translated prose. Working code for this
lives in the commit that added this file (`apply_tr.py` pattern).

Four traps, all of which have bitten this project:

1. **JSON-LD is invisible to a text-node walk.** The `<script type="ld+json">`
   FAQ blocks duplicate the visible `<details>` answers. A node-index pass
   updates the visible copy and leaves the machine-readable one stale — on a
   site whose entire point is being machine-readable. Patch JSON-LD separately,
   with raw string replacement.
2. **Do not re-serialise the parse tree.** A BeautifulSoup round-trip on these
   pages is *not* byte-identical. An incidental re-encode once stripped
   `@font-face` from 77 of 97 pages while `index.html` still looked perfect. Use
   string surgery.
3. **Attribute order differs between the English and translated trees.** The
   translated pages went through a parser and came out alphabetised, so
   `<a href=… aria-label=…>` in English is `<a aria-label=… href=…>` in French.
   Any regex touching a tag must be order-agnostic.
4. **Meta descriptions on translated pages are often still English.** They are
   outside the translated body. Check them explicitly.

## Reviewing machine translation

Every segment gets read by a human or by an agent instructed to check meaning,
not fluency. Real failures caught here:

- DeepL rendered *"Qatar is earlier in its programme than the UAE"* as
  **"ahead of the UAE"** — the exact opposite — in French, German and Arabic.
- *"The UAE programme is closer [than Qatar's]"* came back as "is taking shape"
  in both French and German, dropping the comparison the sentence exists to make.
- *"as of 7 July"* became *"since 7 July"* in both.
- Arabic transliterated **DXB Vertiport**, **Skyports** and **Joby** into Arabic
  script. Every other Arabic page on this site keeps proper nouns in Latin.
- An agent fleet silently left 146 of 270 German segments in English, twice.
  Always scan the output for untranslated source-language prose.

Fluent output is not evidence of correct output. Check the claim, the direction
of every comparison, the tense, and the proper nouns.

## Editorial bar

- **Cite primary sources only**: company investor relations, regulators,
  government. Aggregators and trade press may point you at a story; they never
  appear in a source list.
- Every source needs `id`, `name`, `url`, `type`, `accessed`.
- If an entity has no primary source, it should not be published as-is.
  `freshness.py` flags this.
- Where a claim is contested or a date is a target rather than a fact, say so in
  the sentence. "Targeted for Q3 2026" is honest; "launching Q3 2026" is not.

## Status vocabulary

Canonical tokens, snake_case, and the `<select id="f-status">` on every homepage
must list every one that occurs:

`planned` · `announced` · `design_approved` · `under_construction` ·
`trial_only` · `certified` · `operational` · `orphaned` · `decommissioned`

A badge renders the **localised label**, never the raw token. `guard.sh` checks
both — this went unnoticed long enough that 18 of 51 UAE cards and 9 of 20 Qatar
cards were unreachable by any filter selection, and two dropdown options matched
nothing at all.

## What "done" looks like

- `./guard.sh` exits 0
- every entity you touched has `last_verified` set to today
- every new claim has a primary source in the source list **and** a timeline entry
- the change is stated in all five languages, including JSON-LD
- the commit message says what changed, what stayed, and why
