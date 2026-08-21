#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# guard.sh — build-time invariants for qatarevtol.com
#
# Every check below exists because it already broke once. The comment on each
# says what it cost. This runs as the Netlify build command and in CI on every
# push and pull request; a non-zero exit blocks the deploy.
#
# Rule for adding to this file: only assertions that are deterministic and that
# encode a regression we actually suffered. Lighthouse scores are NOT in here —
# they fluctuate run to run and a flaky gate is worse than no gate. Scores are
# tracked separately, out of the deploy path.
# ---------------------------------------------------------------------------
set -uo pipefail

LIVE_HOST="qatarevtol.com"
DEAD_HOSTS="evtolquatar.com evtolqatar.com"
MIN_PAGES=95

fail=0
say(){ echo "GUARD FAIL: $1"; fail=1; }
pages(){ find . -name '*.html' -not -path './.git/*' -not -name 'google*'; }

# 1 ── Fonts stay self-hosted. Remote Google Fonts = three cross-origin hops
#      on the critical path; cost ~1s of FCP and 9 performance points.
if grep -rqE 'fonts\.(googleapis|gstatic)\.com' --include='*.html' . ; then
  say "remote Google Fonts reference reintroduced"
  grep -rlE 'fonts\.(googleapis|gstatic)\.com' --include='*.html' . | head -5
fi

# 2 ── font-display must be optional. swap reflows the hero: CLS 0.198.
if grep -rqE 'font-display: *swap' --include='*.html' . ; then
  say "font-display:swap found — must be optional (swap caused CLS 0.198)"
  grep -rlE 'font-display: *swap' --include='*.html' . | head -5
fi

# 3 ── The self-hosted font files must exist and be non-trivial.
for f in fonts/newsreader-wght-normal.woff2 \
         fonts/newsreader-wght-italic.woff2 \
         fonts/jetbrains-mono-wght-normal.woff2; do
  [ -s "$f" ] || say "missing or empty font: $f"
done

# 4 ── Every page declares the faces. A normalising HTML pass once stripped the
#      declaration from 77 of 97 pages while index.html still looked fine.
missing=0
for f in $(pages); do grep -q '@font-face' "$f" || { missing=$((missing+1)); }; done
[ "$missing" -eq 0 ] || say "$missing page(s) missing @font-face"

# 5 ── Same failure mode, other half: the preload hint.
missing=0
for f in $(pages); do grep -q 'rel="preload"' "$f" || { missing=$((missing+1)); }; done
[ "$missing" -eq 0 ] || say "$missing page(s) missing the font preload hint"

# 6 ── Resource hints belong in <head>. In <body> they are parsed too late to
#      do anything, which is a silent performance loss, not an error.
#      (tags are split onto their own lines first — these pages are minified,
#      so a line-oriented scan would see </head> and the stray hint as one line
#      and miss it entirely. That bug shipped in the first version of this file.)
late=0
for f in $(pages); do
  tr '>' '\n' < "$f" \
    | awk '/\/head/{h=1;next} h&&/rel="preload"|rel="preconnect"|rel="dns-prefetch"/{x=1;exit} END{exit !x}' \
    && { late=$((late+1)); }
done
[ "$late" -eq 0 ] || say "$late page(s) have a resource hint after </head>"

# 7 ── Dead domains. The original launch shipped 1,916 references to a domain
#      that was never registered. Zero tolerance.
for d in $DEAD_HOSTS; do
  if grep -rqF "$d" --include='*.html' --include='*.xml' --include='*.txt' . ; then
    say "dead domain '$d' reintroduced"
    grep -rlF "$d" --include='*.html' --include='*.xml' --include='*.txt' . | head -5
  fi
done

# 8 ── Every canonical and every sitemap URL points at the live host.
bad=$(grep -rhoE '<link rel="canonical" href="https://[^/"]+' --include='*.html' . \
      | sed 's|.*https://||' | sort -u | grep -v "^${LIVE_HOST}$" || true)
[ -z "$bad" ] || say "canonical points at wrong host(s): $bad"
bad=$(grep -ohE 'https://[^/<]+' sitemap.xml 2>/dev/null \
      | sed 's|https://||' | sort -u | grep -v "^${LIVE_HOST}$" || true)
[ -z "$bad" ] || say "sitemap references wrong host(s): $bad"

# 9 ── Page-count floor. Catches a partial build or an accidental mass delete
#      before it reaches production, which no per-file check can see.
n=$(find . -name '*.html' -not -path './.git/*' | wc -l)
[ "$n" -ge "$MIN_PAGES" ] || say "only $n HTML pages, expected at least $MIN_PAGES"

# 10 ── Measured contrast tokens. Reverting any of these fails WCAG AA and
#       drops Accessibility off 100. Checked on every page that has the ticker,
#       not just index.html — the regression that started this was on a subpage.
for f in $(grep -rl 'ticker-item' --include='*.html' . ); do
  grep -q 'ticker-item{flex-shrink:0;background' "$f" || say "$f: ticker-item lost its opaque background"
  grep -q '#e44c0e'        "$f" || say "$f: --signal-on-dark #e44c0e missing (was 3.50:1 on --ink)"
  grep -q '254,251,243,.48' "$f" || say "$f: .ticker-type alpha below .48 (was 4.37:1)"
done

# 11 ── Translated trees keep their language declaration. Agent passes have
#       twice overwritten a localised page with its English source.
for L in fr de ar; do
  [ -d "$L" ] || continue
  n=$(find "$L" -name '*.html' | wc -l)
  m=$(grep -rlE "<html[^>]*lang=\"$L\"" "$L" --include='*.html' | wc -l)
  [ "$n" -eq "$m" ] || say "$L/: $((n-m)) page(s) not declaring lang=\"$L\""
done
if [ -d zh ]; then
  n=$(find zh -name '*.html' | wc -l)
  m=$(grep -rlE '<html[^>]*lang="zh' zh --include='*.html' | wc -l)
  [ "$n" -eq "$m" ] || say "zh/: $((n-m)) page(s) not declaring a zh lang"
fi
if [ -d ar ]; then
  n=$(find ar -name '*.html' | wc -l)
  m=$(grep -rl 'dir="rtl"' ar --include='*.html' | wc -l)
  [ "$n" -eq "$m" ] || say "ar/: $((n-m)) page(s) missing dir=\"rtl\""
fi

# 13 ── The status filter must be able to reach every card. The homepage JS
#       compares dataset.status to the selected <option value>; when the data
#       drifted into two spellings of one status, 18 of 51 UAE cards and 9 of
#       20 Qatar cards became unreachable by any selection, and two dropdown
#       options matched nothing at all. Pure set comparison, no dependencies.
for f in $(grep -rl 'id="f-status"' --include='*.html' . ); do
  # only the status <select>, not the type/country ones sharing the filter bar
  opts=$(tr '<' '\n' < "$f" \
         | awk '/select .*id="f-status"/{i=1;next} i&&/^\/select/{exit} i' \
         | grep -oE 'value="[^"]+"' | sed 's/value="//;s/"//' | sort -u)
  cards=$(grep -oE 'data-status="[^"]+"' "$f" | sed 's/.*="//;s/"//' | sort -u)
  orphan=$(comm -13 <(echo "$opts") <(echo "$cards"))
  dead=$(comm -23 <(echo "$opts") <(echo "$cards"))
  [ -z "$orphan" ] || say "$f: card status with no filter option: $(echo $orphan)"
  [ -z "$dead" ]   || say "$f: filter option matching no card: $(echo $dead)"
done

# 14 ── A status badge must render a human label, never the raw token. Eight
#       cards on each homepage showed 'trial-only' in five languages instead of
#       Trial-only / Essais seulement / Nur Tests / تجريبي فقط / 仅试运行.
raw=$(grep -rhoE 'class="(hub-)?card-status">[a-z][a-z_-]*<' --include='*.html' . | sort -u)
[ -z "$raw" ] || say "raw status slug rendered as a label: $(echo $raw | tr -d '<')"

# 15 ── Every indexable page declares a canonical that points at ITSELF, and no
#       two pages claim the same one. A canonical pointing somewhere else is a
#       request to de-index the page, so a copy-paste here deletes a page from
#       search silently -- nothing breaks, traffic just never arrives.
#       404.html is excluded: it must NOT have a canonical, and must say noindex.
LIVE="https://${LIVE_HOST}"
canon_tmp=$(mktemp)
for f in $(pages); do
  rel="${f#./}"
  [ "$rel" = "404.html" ] && continue
  case "$rel" in
    index.html)   want="$LIVE/" ;;
    */index.html) want="$LIVE/${rel%index.html}" ;;
    *)            want="$LIVE/$rel" ;;
  esac
  got=$(grep -o '<link[^>]*rel="canonical"[^>]*>' "$f" | head -1 | grep -o 'href="[^"]*"' | sed 's/href="//;s/"//')
  if [ -z "$got" ]; then
    say "$rel: no canonical"
  elif [ "$got" != "$want" ]; then
    say "$rel: canonical is $got, should be $want"
  else
    echo "$got" >> "$canon_tmp"
  fi
  grep -qF "<loc>$want</loc>" sitemap.xml || say "$rel: not in sitemap.xml"
done
dupes=$(sort "$canon_tmp" | uniq -d)
[ -z "$dupes" ] || say "canonical URL claimed by more than one page: $(echo $dupes)"
rm -f "$canon_tmp"

# 16 ── The 404 page must be uncrawlable and unlisted, or it competes with real
#       pages in the index.
if [ -f 404.html ]; then
  grep -q 'noindex' 404.html || say "404.html is missing noindex"
  grep -q '<link[^>]*rel="canonical"' 404.html && say "404.html must not declare a canonical"
  grep -qF "<loc>${LIVE}/404.html</loc>" sitemap.xml && say "404.html must not be in sitemap.xml"
fi

# 17 ── The dataset is a product now, not a build artifact. Google Dataset
#       Search is a separate index from web search and it is the surface this
#       site can actually win on today, so the exports and the markup that
#       declares them are load-bearing.
for f in data.html entities.json entities.csv feed.xml; do
  [ -s "$f" ] || say "missing or empty dataset artifact: $f"
done
if [ -s data.html ]; then
  grep -q '"@type": "Dataset"'                      data.html || say "data.html: schema.org/Dataset markup gone"
  grep -q 'creativecommons.org/licenses/by/4.0'     data.html || say "data.html: CC BY licence declaration gone (attribution IS the citation mechanism)"
  grep -q '"@type": "DataDownload"'                 data.html || say "data.html: no DataDownload distribution declared"
fi

# 18 ── The exports must be regenerated, not stale. A CSV that disagrees with
#       entities.json is worse than no CSV: it is a wrong answer served with
#       confidence.
if [ -s entities.csv ] && [ -s entities.json ]; then
  j=$(grep -c '"slug":' entities.json)
  c=$(( $(wc -l < entities.csv) - 1 ))
  [ "$j" -eq "$c" ] || say "entities.csv has $c rows but entities.json has $j entities — re-run build_data.py"
fi

# 19 ── A citable source needs something to cite. One source once shipped typed
#       'primary' with url: null -- an editorial note counted toward the
#       primary-source tally the whole site's credibility rests on.
badurl=$(grep -n '"url":' entities.json | grep -v '"url": "https\?://' || true)
if [ -n "$badurl" ]; then
  say "entities.json source(s) with a non-citable url (null, empty or not http):"
  echo "$badurl" | head -5
fi

# 20 ── Feed autodiscovery on every page, or the feed is unfindable.
missing=0
for f in $(pages); do grep -q 'application/atom+xml' "$f" || missing=$((missing+1)); done
[ "$missing" -eq 0 ] || say "$missing page(s) missing the Atom feed autodiscovery link"

# 21 ── The reverse of 15. Invariant 15 proves every page is listed; nothing
#       proved every listed URL exists. data.html shipped with a copy-pasted
#       hreflang block advertising /ar/, /de/, /fr/ and /zh/ translations that
#       were never written — four sitemap-declared 404s handed straight to
#       Googlebot, on a domain whose entire problem is index trust.
missing=0
for u in $(grep -ohE 'https://'"$LIVE_HOST"'/[^"<]*' sitemap.xml | sort -u); do
  rel="${u#https://$LIVE_HOST/}"
  case "$rel" in ''|*/) rel="${rel}index.html" ;; esac
  [ -f "$rel" ] || { say "sitemap.xml lists $u but $rel does not exist"; missing=$((missing+1)); }
done
[ "$missing" -eq 0 ] || say "$missing sitemap URL(s) point at nothing"

# 22 ── Every in-page link must actually go somewhere. A source list once
#       rendered <a href="internal"> and <a href=""> for notes that had no URL
#       to cite: five live 404s per language plus a self-link, and Search
#       Console reported the 404 while all 21 invariants passed.
badhref=$(for f in $(pages); do grep -oE 'href="[^"]*"' "$f"; done \
  | sed 's/^href="//; s/"$//' | sed 's/^$/<empty>/' | sort -u \
  | grep -vE '^(https?://|/|#|mailto:|tel:|data:)' \
  | grep -vE '^[A-Za-z0-9._~-]+\.(html|xml|json|csv|txt|png|svg|ico|woff2)$' || true)
if [ -n "$badhref" ]; then
  say "link(s) with no valid target: $(echo $badhref | tr '\n' ' ')"
fi

# 12 ── The machine-readable surface. This is the whole point of the site.
for f in llms.txt llms-full.txt robots.txt sitemap.xml; do
  [ -s "$f" ] || say "missing $f"
done

if [ "$fail" -ne 0 ]; then
  echo ""
  echo "Build blocked. Each check above names the regression it prevents."
  exit 1
fi
echo "guard.sh: all invariants hold ($(find . -name '*.html' -not -path './.git/*' | wc -l) pages checked)"
