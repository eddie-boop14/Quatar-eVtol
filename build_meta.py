#!/usr/bin/env python3
"""Search-snippet hygiene for every canonical page (Bing SEO report, Oct 2026).

Three idempotent passes over the HTML at the repo root:

1. Locale entity pages (ar/fr/de/zh) that still carry the English meta
   description get one built from their own localized hero-lead, so the five
   language versions stop sharing a description.
2. Section hubs (all locales) get the hub subtitle plus one sentence on
   sourcing, so the description is long enough to be used as a snippet.
3. Titles over 70 characters drop trailing " · " segments until they fit.

og:/twitter: title and description follow the page's own values when they
mirrored them. Run from the repo root before build_og.py, then ./guard.sh.
"""
import html as htmlmod
import pathlib
import re
import sys

LANG_DIRS = ("ar", "fr", "de", "zh")
HUBS = ("aircraft", "vertiports", "routes", "operators", "regulators", "explainers")
TITLE_MAX, DESC_MIN, DESC_MAX = 70, 110, 160
HUB_TAIL = {
    "en": "Every entry cites primary sources and carries a last-verified date. Open data, CC BY 4.0.",
    "ar": "يستشهد كل مدخل بمصادر أولية ويتضمن تاريخ آخر تحديث. بيانات مفتوحة، CC BY 4.0.",
    "fr": "Chaque entrée cite des sources primaires et indique la date de la dernière vérification. Données ouvertes, licence CC BY 4.0.",
    "de": "Jeder Eintrag enthält Verweise auf Primärquellen und ein Datum der letzten Überprüfung. Offene Daten, CC BY 4.0.",
    "zh": "每条条目均引用了原始资料，并标注了最后核查日期。开放数据，CC BY 4.0。",
}

DESC_TAG = re.compile(r'<meta\b[^>]*\bname="description"[^>]*>')
CONTENT = re.compile(r'\bcontent="([^"]*)"')


def get_desc(h):
    m = DESC_TAG.search(h)
    c = CONTENT.search(m.group(0)) if m else None
    return htmlmod.unescape(c.group(1)) if c else None


def set_meta(h, attr, value, old=None):
    """Set content= on <meta {attr}>; with old, only when it currently equals old."""
    pat = re.compile(r'<meta\b[^>]*\b' + re.escape(attr) + r'[^>]*>')
    esc = htmlmod.escape(value, quote=True)

    def rep(m):
        tag = m.group(0)
        c = CONTENT.search(tag)
        if not c or (old is not None and htmlmod.unescape(c.group(1)) != old):
            return tag
        return tag[: c.start(1)] + esc + tag[c.end(1):]

    return pat.sub(rep, h)


def set_desc(h, new):
    old = get_desc(h)
    h = set_meta(h, 'name="description"', new)
    for a in ('property="og:description"', 'name="twitter:description"'):
        h = set_meta(h, a, new, old)
    return h


def trim(text, limit=DESC_MAX):
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    cut = text[:limit]
    ends = [m.end() for m in re.finditer(r"[.。!?！？](\s|$)|[。！？]", cut)]
    if ends and ends[-1] >= 70:
        return cut[: ends[-1]].strip()
    sp = cut.rfind(" ")
    return (cut[:sp] if sp > 70 else cut[: limit - 1]).rstrip(" ,;:—-") + "…"


def strip_tags(s):
    return htmlmod.unescape(re.sub(r"<[^>]+>", "", s))


def fix_title(h):
    m = re.search(r"<title>([^<]+)</title>", h)
    if not m:
        return h
    old = htmlmod.unescape(m.group(1)).strip()
    new = old
    while len(new) > TITLE_MAX and " · " in new:
        new = new.rsplit(" · ", 1)[0]
    if new == old:
        return h
    h = h[: m.start(1)] + htmlmod.escape(new, quote=False) + h[m.end(1):]
    for a in ('property="og:title"', 'name="twitter:title"'):
        h = set_meta(h, a, new, old)
    return h


def main():
    root = pathlib.Path(__file__).resolve().parent
    n = {"locale_desc": 0, "hub_desc": 0, "title": 0}
    for path in sorted(root.rglob("*.html")):
        rel = path.relative_to(root)
        if rel.parts[0] in (".git", "og", "netlify"):
            continue
        h = path.read_text(encoding="utf-8")
        if 'rel="canonical"' not in h:
            continue
        orig = h
        lang = rel.parts[0] if rel.parts[0] in LANG_DIRS else "en"
        parts = rel.parts[1:] if lang != "en" else rel.parts

        if len(parts) == 1 and pathlib.Path(parts[0]).stem in HUBS:
            sub = re.search(r'<p class="hub-sub">(.*?)</p>', h, re.S)
            if sub:
                lead = strip_tags(sub.group(1)).strip()
                new = lead + ("" if lang == "zh" else " ") + HUB_TAIL[lang]
                if get_desc(h) != new:
                    h = set_desc(h, new)
                    n["hub_desc"] += 1

        if lang != "en" and len(parts) == 2:
            lead = re.search(r'<p class="hero-lead">(.*?)</p>', h, re.S)
            mine = get_desc(h)
            twins = [root.joinpath(*parts)] + [root / l / pathlib.Path(*parts) for l in LANG_DIRS if l != lang]
            shared = any(t.exists() and get_desc(t.read_text(encoding="utf-8")) == mine for t in twins)
            if lead and shared:
                h = set_desc(h, trim(strip_tags(lead.group(1))))
                n["locale_desc"] += 1

        h2 = fix_title(h)
        if h2 != h:
            n["title"] += 1
            h = h2
        if h != orig:
            path.write_text(h, encoding="utf-8")
    print("meta: {locale_desc} locale descriptions localized · {hub_desc} hub descriptions · {title} titles shortened".format(**n))
    return 0


if __name__ == "__main__":
    sys.exit(main())
