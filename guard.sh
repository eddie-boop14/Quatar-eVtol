#!/usr/bin/env bash
# Build-time invariants. Any of these regressing puts us back where we were
# on 2026-08-03: CLS 0.200, Performance 90, Agentic 2/3.
# This runs on every Netlify deploy. Non-zero exit fails the build.
set -uo pipefail
fail=0
say(){ echo "GUARD FAIL: $1"; fail=1; }

# 1. Fonts must stay self-hosted. Remote Google Fonts = 3 cross-origin hops
#    and the font-swap CLS that cost 9 performance points.
if grep -rqE 'fonts\.(googleapis|gstatic)\.com' --include='*.html' . ; then
  say "remote Google Fonts reference reintroduced"
  grep -rlE 'fonts\.(googleapis|gstatic)\.com' --include='*.html' . | head -5
fi

# 2. font-display MUST be optional, not swap. swap reintroduces the hero reflow.
if grep -rq 'font-display:swap' --include='*.html' . ; then
  say "font-display:swap found — must be optional (swap caused CLS 0.198)"
fi

# 3. The three self-hosted font files must exist and be non-trivial.
for f in fonts/newsreader-wght-normal.woff2 fonts/newsreader-wght-italic.woff2 fonts/jetbrains-mono-wght-normal.woff2; do
  [ -s "$f" ] || say "missing or empty font: $f"
done

# 4. Every page must declare the self-hosted faces (a stripped <head> shipped
#    77 pages with no font declaration at all during this work).
missing=0
for f in $(find . -name '*.html' -not -path './.git/*' -not -name 'google*'); do
  grep -q '@font-face' "$f" || missing=$((missing+1))
done
[ "$missing" -eq 0 ] || say "$missing page(s) missing @font-face"

# 5. Contrast tokens that were measured and fixed. Reverting them fails WCAG AA.
grep -q '#e44c0e' index.html || say "--signal-on-dark #e44c0e missing (was 3.50:1 on --ink)"
grep -q '254,251,243,.48' index.html || say ".ticker-type alpha reverted below .48 (was 4.37:1)"

# 6. The animated ticker layer needs an opaque background or the contrast
#    audit cannot resolve it.
grep -q 'ticker-item{flex-shrink:0;background' index.html || say "ticker-item lost its opaque background"

# 7. AI-discoverability surface must stay present.
for f in llms.txt llms-full.txt robots.txt sitemap.xml; do
  [ -s "$f" ] || say "missing $f"
done

if [ "$fail" -ne 0 ]; then
  echo ""
  echo "Build blocked. See guard.sh for why each invariant exists."
  exit 1
fi
echo "guard.sh: all invariants hold"
