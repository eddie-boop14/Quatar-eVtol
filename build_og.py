#!/usr/bin/env python3
"""Generate OG/Twitter card images and wire them into every canonical page.

W5.1/W5.2 of POA-citation-layer.md. One 1200x630 PNG per entity (from
entities.json), per section hub, plus site and dataset cards, drawn with the
site's own faces (Newsreader for the headline, JetBrains Mono for chrome)
converted from the repo's woff2 at build time. Injection is idempotent: the
tags live between HTML markers before </head> and are replaced on re-run.

Run from the repo root:  python3 build_og.py   — then ./guard.sh
Deps: pillow, fonttools, brotli.
"""
import html as htmlmod
import json
import pathlib
import re
import sys
import tempfile

from PIL import Image, ImageDraw, ImageFont

# ---- per-site config -------------------------------------------------------
DOMAIN = "qatarevtol.com"
SITE_NAME = "Qatar eVTOL"
SITE_TAGLINE = "The independent primary-source eVTOL reference for Qatar"
ACCENT = "#e85d04"       # ember — this site's palette
ACCENT_DEEP = "#c2410c"
LOCALE_OF = {"en": "en", "ar": "ar", "fr": "fr", "de": "de", "zh": "zh"}
# ---------------------------------------------------------------------------

NAVY, NAVY_RULE = "#0a1628", "#1e3a5f"
CREAM, MUTED = "#fefbf3", "#93a0b4"
W, H, PAD = 1200, 630, 64

STATUS_COLOR = {
    "operational": "#4ade80", "certified": "#4ade80",
    "trial_only": "#fbbf24",
    "under_construction": "#fb923c", "design_approved": "#fb923c",
    "announced": "#94a3b8", "planned": "#94a3b8",
    "orphaned": "#f87171", "decommissioned": "#f87171",
}
SECTIONS = {
    "aircraft": ("Aircraft", "aircraft"),
    "vertiports": ("Vertiports", "vertiport"),
    "routes": ("Routes", "route"),
    "operators": ("Operators", "operator"),
    "regulators": ("Regulators", "regulator"),
    "explainers": ("Explainers", "answer"),
}
LANG_DIRS = {"ar", "fr", "de", "zh"}
MARK_OPEN, MARK_CLOSE = "<!-- og-image -->", "<!-- /og-image -->"


def fonts():
    """woff2 -> static ttf, cached in the system temp dir (never committed)."""
    from fontTools.ttLib import TTFont
    from fontTools.varLib.instancer import instantiateVariableFont

    cache = pathlib.Path(tempfile.gettempdir()) / "og-fonts"
    cache.mkdir(exist_ok=True)
    out = {}
    for key, src, wght in (
        ("serif", "fonts/newsreader-wght-normal.woff2", 700),
        ("mono", "fonts/jetbrains-mono-wght-normal.woff2", 500),
        ("mono-bold", "fonts/jetbrains-mono-wght-normal.woff2", 700),
    ):
        dst = cache / f"{pathlib.Path(src).stem}-{wght}.ttf"
        if not dst.exists():
            f = TTFont(src)
            if "fvar" in f:
                instantiateVariableFont(f, {"wght": wght}, inplace=True)
            f.flavor = None
            f.save(dst)
        out[key] = str(dst)
    return out


F = None  # font path cache, filled in main()


def font(kind, size):
    return ImageFont.truetype(F[kind], size)


def roundel(draw, cx, cy, r):
    """The site favicon, drawn: navy tile omitted, rings only."""
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=ACCENT)
    for rr, col in ((r * 0.89, CREAM), (r * 0.78, ACCENT_DEEP), (r * 0.29, CREAM)):
        draw.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=col)


def wrap(draw, text, fnt, max_w):
    words, lines, cur = text.split(), [], ""
    for w_ in words:
        t = f"{cur} {w_}".strip()
        if draw.textlength(t, font=fnt) <= max_w or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w_
    if cur:
        lines.append(cur)
    return lines


def card(path, title, kicker, status=None, foot_right=""):
    img = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(img)

    # chrome: roundel + wordmark, top hairline of accent
    d.rectangle([0, 0, W, 6], fill=ACCENT)
    roundel(d, PAD + 26, PAD + 26, 26)
    d.text((PAD + 70, PAD + 8), SITE_NAME, font=font("mono-bold", 34), fill=CREAM)
    tag = "PRIMARY-SOURCE REFERENCE"
    ft = font("mono", 19)
    d.text((W - PAD - d.textlength(tag, font=ft), PAD + 16), tag, font=ft, fill=MUTED)

    # kicker
    y = 218
    if kicker:
        d.text((PAD, y), kicker.upper(), font=font("mono", 26), fill=ACCENT)
        y += 52

    # headline: shrink until it fits three lines
    for size in range(84, 47, -4):
        fh = font("serif", size)
        lines = wrap(d, title, fh, W - 2 * PAD)
        if len(lines) <= 3 and y + len(lines) * (size + 12) < H - 150:
            break
    for ln in lines[:3]:
        d.text((PAD, y), ln, font=fh, fill=CREAM)
        y += size + 12

    # bottom band
    by = H - 118
    d.rectangle([PAD, by, W - PAD, by + 2], fill=NAVY_RULE)
    if status:
        label = status.replace("_", " ").upper()
        col = STATUS_COLOR.get(status, MUTED)
        fp = font("mono-bold", 24)
        tw = d.textlength(label, font=fp)
        d.rounded_rectangle([PAD, by + 30, PAD + tw + 44, by + 82], radius=12, outline=col, width=3)
        d.text((PAD + 22, by + 41), label, font=fp, fill=col)
    if foot_right:
        fr = font("mono", 22)
        d.text((W - PAD - d.textlength(foot_right, font=fr), by + 48), foot_right, font=fr, fill=MUTED)

    img.save(path, "PNG", optimize=True)


def build_images(root, entities):
    og = root / "og"
    og.mkdir(exist_ok=True)
    made = 0
    for e in entities:
        kick = e["entity_type"]
        if e.get("city"):
            kick += f" · {e['city']}"
        card(
            og / f"{e['slug']}.png",
            e["name"],
            kick,
            status=e.get("status"),
            foot_right=f"as of {e['last_verified']} · {DOMAIN}",
        )
        made += 1
    from collections import Counter

    counts = Counter(e["entity_type"] for e in entities)
    for sec, (label, etype) in SECTIONS.items():
        card(
            og / f"section-{sec}.png",
            label,
            f"{counts.get(etype, 0)} documented · primary sources only",
            foot_right=DOMAIN,
        )
        made += 1
    card(og / "site.png", SITE_TAGLINE, f"{len(entities)} entities · every claim sourced", foot_right=DOMAIN)
    card(og / "dataset.png", "Open dataset — CC BY 4.0", "JSON · CSV · per-record sources and verification dates", foot_right=DOMAIN)
    return made + 2


def image_key(rel, slugs):
    parts = list(rel.parts)
    if parts and parts[0] in LANG_DIRS:
        parts = parts[1:]
    if not parts:
        return "site"
    stem = pathlib.Path(parts[-1]).stem
    if len(parts) == 1:
        if stem in ("index",):
            return "site"
        if stem == "data":
            return "dataset"
        return f"section-{stem}" if stem in SECTIONS else "site"
    return stem if stem in slugs else (f"section-{parts[0]}" if parts[0] in SECTIONS else "site")


def esc(s):
    return htmlmod.escape(s, quote=True)


def inject(root, entities):
    slugs = {e["slug"]: e for e in entities}
    wired = full_blocks = skipped = 0
    for path in sorted(root.rglob("*.html")):
        rel = path.relative_to(root)
        if rel.parts[0] in (".git", "og"):
            continue
        html = path.read_text(encoding="utf-8")
        # Root pages write rel-first, locale pages href-first + self-closing.
        m = re.search(r'<link rel="canonical" href="([^"]+)"', html) or re.search(
            r'<link href="([^"]+)" rel="canonical"', html
        )
        if not m or "</head>" not in html:
            skipped += 1
            continue
        canonical = m.group(1)
        key = image_key(rel, slugs)
        url = f"https://{DOMAIN}/og/{key}.png"
        ent = slugs.get(key)
        alt = (
            f"{ent['name']} — {ent['entity_type']}, {ent['status'].replace('_', ' ')}. {SITE_NAME} reference card."
            if ent
            else f"{SITE_NAME} — primary-source eVTOL reference card."
        )
        tags = [
            f'<meta property="og:image" content="{url}">',
            '<meta property="og:image:width" content="1200">',
            '<meta property="og:image:height" content="630">',
            f'<meta property="og:image:alt" content="{esc(alt)}">',
            f'<meta name="twitter:image" content="{url}">',
        ]
        if 'property="og:title"' not in html:
            title = re.search(r"<title>([^<]+)</title>", html)
            desc = re.search(r'<meta name="description" content="([^"]*)"', html)
            lang = rel.parts[0] if rel.parts[0] in LANG_DIRS else "en"
            tags = [
                f'<meta property="og:title" content="{esc(title.group(1).strip()) if title else esc(SITE_NAME)}">',
                f'<meta property="og:description" content="{desc.group(1) if desc else esc(SITE_TAGLINE)}">',
                '<meta property="og:type" content="website">',
                f'<meta property="og:url" content="{canonical}">',
                f'<meta property="og:locale" content="{LOCALE_OF[lang]}">',
                '<meta name="twitter:card" content="summary_large_image">',
            ] + tags
            full_blocks += 1
        block = MARK_OPEN + "\n" + "\n".join(tags) + "\n" + MARK_CLOSE + "\n"
        if MARK_OPEN in html:
            new = re.sub(re.escape(MARK_OPEN) + r".*?" + re.escape(MARK_CLOSE) + r"\n?", block, html, count=1, flags=re.S)
        else:
            new = html.replace("</head>", block + "</head>", 1)
        if new != html:
            path.write_text(new, encoding="utf-8")
        wired += 1
    return wired, full_blocks, skipped


def main():
    global F
    root = pathlib.Path(__file__).resolve().parent
    F = fonts()
    entities = json.loads((root / "entities.json").read_text())["entities"]
    n_img = build_images(root, entities)
    wired, full_blocks, skipped = inject(root, entities)
    print(f"og: {n_img} images · {wired} pages wired ({full_blocks} got full OG blocks) · {skipped} skipped (no canonical)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
