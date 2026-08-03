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
