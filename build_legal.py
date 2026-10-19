#!/usr/bin/env python3
"""Publisher imprint in every footer, plus the legal notice page.

1. Every page with a footer gets the imprint block (between HTML markers, so
   re-runs refresh it): the publisher's signature — the same one
   officiallink.org carries — a link to /legal.html, and one line naming
   officiallink.org as the sister site, linking its "why" page. The old
   "© 2026 <site>" line is removed so the page carries one signature.
2. legal.html is generated from data.html's shell (like changes.html) and
   follows officiallink.org/legal/ section for section, so the two notices
   corroborate each other.

Run from the repo root after build_data.py / build_changes.py (they rewrite
data.html and changes.html) and before build_og.py, then ./guard.sh.
"""
import html as H
import pathlib
import re
import sys

# ---- per-site config -------------------------------------------------------
SITE = "Qatar eVTOL"
SCOPE = "eVTOL in Qatar"
# ---------------------------------------------------------------------------
ROOT = pathlib.Path(__file__).resolve().parent
LANG_DIRS = ("ar", "fr", "de", "zh")
MARK_OPEN, MARK_CLOSE = "<!-- imprint -->", "<!-- /imprint -->"
SIGNATURE = "© 2026 Edmaster &amp; Claudius · bleu canard éditions"
UPDATED = "19 October 2026"

# Footer strings (ar/de/zh from DeepL; the French "why" label is officiallink.org's own).
T = {
    "en": ("Legal notice", "Sister site of {ol} — nothing sold, every fact sourced.", "Why it exists"),
    "fr": ("Mentions légales", "Site partenaire d'{ol} — aucune vente, toutes les informations sont sourcées.", "Pourquoi ce site existe"),
    "de": ("Rechtliche Hinweise", "Schwester-Website von {ol} – hier wird nichts verkauft, jede Angabe ist mit Quellenangaben versehen.", "Warum es existiert"),
    "ar": ("إشعار قانوني", "موقع شقيق لموقع {ol} — لا يتم بيع أي شيء، وكل معلومة مرفقة بمصدرها.", "لماذا يوجد؟"),
    "zh": ("法律声明", "{ol} 的姊妹网站——不销售任何商品，所有事实均有来源。", "它为何存在"),
}
OL_HOME = {"fr": "https://officiallink.org/fr/"}
OL_WHY = {"fr": "https://officiallink.org/fr/why/"}


def host():
    return re.search(r"<loc>https://([^/<]+)", (ROOT / "sitemap.xml").read_text(encoding="utf-8")).group(1)


def imprint(lang):
    legal, sister, why = T[lang]
    arrow = "←" if lang == "ar" else "→"
    a = 'style="color:inherit;text-decoration:underline;text-underline-offset:2px"'
    ol = f'<a {a} href="{OL_HOME.get(lang, "https://officiallink.org/")}">officiallink.org</a>'

    style = 'style="max-width:1280px;margin:1.25rem auto 0;padding:0 var(--space,1.25rem);font-size:.8rem;line-height:1.7;opacity:.8;text-align:center"'
    return (
        f'{MARK_OPEN}\n<div class="imprint" {style}>\n'
        f'<div>{SIGNATURE} · <a {a} href="/legal.html">{legal}</a></div>\n'
        f'<div>{sister.format(ol=ol)} <a {a} href="{OL_WHY.get(lang, "https://officiallink.org/why/")}">{why} {arrow}</a></div>\n'
        f'</div>\n{MARK_CLOSE}\n'
    )


OLD_COPYRIGHT = re.compile(r'[ \t]*<(span|div)>© 2026 [^<]*eVTOL[^<]*</\1>\n?')


def stamp_footers():
    done = 0
    for path in sorted(ROOT.rglob("*.html")):
        rel = path.relative_to(ROOT)
        if rel.parts[0] in (".git", "og", "netlify"):
            continue
        h = path.read_text(encoding="utf-8")
        if "</footer>" not in h or 'rel="canonical"' not in h:
            continue  # 404 and verification stubs
        lang = rel.parts[0] if rel.parts[0] in LANG_DIRS else "en"
        new = OLD_COPYRIGHT.sub("", h)
        block = imprint(lang)
        if MARK_OPEN in new:
            new = re.sub(re.escape(MARK_OPEN) + r".*?" + re.escape(MARK_CLOSE) + r"\n?", lambda _: block, new, count=1, flags=re.S)
        else:
            i = new.rfind("</footer>")
            new = new[:i] + block + new[i:]
        if new != h:
            path.write_text(new, encoding="utf-8")
        done += 1
    return done


def sec(title, *paras):
    return f"<h2>{title}</h2>\n" + "\n".join(f"<p>{p}</p>" for p in paras)


def write_legal(host):
    mail = f"hello@{host}"
    m = f'<a href="mailto:{mail}">{mail}</a>'
    title = f"Legal notice — {SITE}"
    desc = (f"Who publishes {host}, who hosts it, how its facts are sourced, the CC BY 4.0 "
            f"data licence, and what it does with your data: nothing. No cookies, no tracking.")
    body = "\n".join([
        sec("Publisher",
            f"{host} is published by a private individual, under the imprint Edmaster &amp; Claudius · "
            f"bleu canard éditions — the same publisher as <a href=\"https://officiallink.org/\">officiallink.org</a>. "
            f"It is a non-professional publication: nothing is sold here, no commission is taken, no advertising is carried.",
            "Under article 6-III-2 of French law no. 2004-575 of 21 June 2004 (LCEN), an individual who publishes "
            "non-professionally may keep their identity private. The publisher's identity is held by the host named "
            "below. The publisher is the director of publication.",
            f"Contact, corrections and takedown requests: {m}"),
        sec("Host",
            "Netlify, Inc., 101 2nd Street, San Francisco, CA 94105, United States — "
            "<a href=\"https://www.netlify.com/\">netlify.com</a> (address as published in Netlify's terms of use)."),
        sec("Independence and trademarks",
            f"{host} is independent. It is not affiliated with, endorsed by, or acting on behalf of any operator, "
            f"manufacturer, regulator, government body or developer it documents. Company and product names, logos "
            f"and domain names belong to their owners and appear here only to identify them."),
        sec("Content",
            f"This is a reference on {SCOPE}. Every claim cites the primary document it was read in — operator "
            f"investor relations, regulator and government announcements — with the date it was read. A status "
            f"changes only on dated evidence; a missed deadline is reported as missed, not as progress.",
            "Programmes, dates and approvals change. The cited source is the reference before relying on anything "
            f"here; nothing on this site is investment, legal or aviation-safety advice. If you find an error, "
            f"write to {m}: a correction ships with the next build, usually within the day."),
        sec("Data and licence",
            "The dataset — <a href=\"/entities.json\">entities.json</a>, <a href=\"/entities.csv\">entities.csv</a>, "
            "the per-entity JSON under <a href=\"/api/\">/api/</a>, the sourced facts and their translations, and the "
            "change feeds — is released under the Creative Commons Attribution 4.0 International licence (CC BY 4.0). "
            f"You may copy, redistribute and build on it, including commercially, if you credit {host} and link to "
            "the licence. Keep each fact's source and date with it. Citation details: <a href=\"/data.html\">/data.html</a>.",
            "<a href=\"https://creativecommons.org/licenses/by/4.0/\">creativecommons.org/licenses/by/4.0</a>",
            "The pages, design and code are © 2026 Edmaster &amp; Claudius · bleu canard éditions. All rights reserved."),
        sec("Personal data",
            "The site sets no cookies, has no accounts and no forms, and runs no advertising, analytics or tracking "
            "scripts. The open API and the MCP endpoint answer anonymously; we keep nothing you send them.",
            "The host keeps standard server logs (including IP addresses) for a limited time, for security and "
            "operation, under its own privacy policy. An email you send us is kept for as long as it takes to answer it.",
            f"Under the General Data Protection Regulation (EU 2016/679) you may ask what we hold about you, and ask "
            f"for it to be corrected or erased, by writing to {m}. We hold nothing beyond the emails you send."),
        f"<p><em>Last updated {UPDATED}. Mirrors the notice at "
        f"<a href=\"https://officiallink.org/legal/\">officiallink.org/legal</a>.</em></p>",
    ])

    shell = (ROOT / "data.html").read_text(encoding="utf-8")
    head = re.search(r"<head>.*?</head>", shell, re.S).group(0)
    head = re.sub(r"<title>[^<]*</title>", f"<title>{H.escape(title, quote=False)}</title>", head)
    head = re.sub(r'(<meta name="description" content=")[^"]*', lambda mm: mm.group(1) + H.escape(desc, quote=True), head)
    head = head.replace(f'href="https://{host}/data.html"', f'href="https://{host}/legal.html"')
    head = re.sub(r'(<meta property="og:url" content=")[^"]*', lambda mm: mm.group(1) + f"https://{host}/legal.html", head)
    for prop in ("og:title", "twitter:title"):
        head = re.sub(f'(<meta (?:property|name)="{prop}" content=")[^"]*', lambda mm: mm.group(1) + H.escape(title, quote=True), head)
    for prop in ("og:description", "twitter:description"):
        head = re.sub(f'(<meta (?:property|name)="{prop}" content=")[^"]*', lambda mm: mm.group(1) + H.escape(desc, quote=True), head)
    head = re.sub(r'<script type="application/ld\+json">.*?</script>', "", head, flags=re.S)
    head = re.sub(r"<!-- og-image -->.*?<!-- /og-image -->\n?", "", head, flags=re.S)
    head = head.replace("</head>", "<style>article.body{max-width:46rem;margin:0 auto;padding:clamp(2rem,5vw,3.5rem) var(--space,1.25rem)}"
                        "article.body h2{font-size:1.35rem;margin:2.2rem 0 .7rem;line-height:1.25}article.body h2:first-child{margin-top:0}"
                        "article.body p{margin:0 0 .9rem}article.body a{border-bottom-color:var(--rule,#d8d0bc)}</style>\n</head>")
    head = head.replace("</head>", f'<link rel="alternate" type="application/atom+xml" title="{SITE} — re-verified entities" href="https://{host}/feed.xml">\n</head>')

    header = re.search(r"<body>.*?</header>", shell, re.S).group(0)
    tail = re.search(r"<!-- sister-site -->.*", shell, re.S).group(0)
    page = f"""<!DOCTYPE html>
<html lang="en" dir="ltr">
{head}
{header}

<section class="hub-hero">
  <div class="hub-hero-inner">
    <div class="hub-eyebrow"><span class="pip"></span>Legal notice</div>
    <h1 class="hero-title">Legal notice</h1>
    <p class="hero-lead">{host} is an independent, primary-source reference. It sells nothing, takes no commission and belongs to no operator or regulator. This page says who publishes it, who hosts it, and what it does with your data — nothing.</p>
  </div>
</section>

<article class="body">
{body}
</article>

{tail}"""
    (ROOT / "legal.html").write_text(page, encoding="utf-8")

    sm = ROOT / "sitemap.xml"
    t = sm.read_text(encoding="utf-8")
    if f"https://{host}/legal.html" not in t:
        sm.write_text(t.replace("</urlset>", f"<url><loc>https://{host}/legal.html</loc></url>\n</urlset>"), encoding="utf-8")


def main():
    h = host()
    write_legal(h)
    n = stamp_footers()
    print(f"legal: legal.html written · imprint on {n} pages")
    return 0


if __name__ == "__main__":
    sys.exit(main())
