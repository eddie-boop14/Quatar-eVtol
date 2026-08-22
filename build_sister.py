#!/usr/bin/env python3
"""Inject (or refresh) the sister-site band right before the footer.

Mirror of the loisirs74 ↔ loisirs73 pattern: each site carries one honest,
visible block naming its sibling — logo, what it is, link — on every page
that has a footer. Idempotent: the block lives between HTML markers and is
replaced in place on re-run. Run from the repo root, then ./guard.sh.
"""
import pathlib
import re
import sys

# ---- per-site config -------------------------------------------------------
SISTER_URL = "https://evtolemirates.com/"
SISTER_NAME = "UAE eVTOL"
SISTER_DOMAIN = "evtolemirates.com"

# The sister's roundel (its favicon.svg, electric palette), unique gradient id.
SISTER_LOGO = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="40" height="40" '
    'aria-hidden="true" style="flex:none;border-radius:9px">'
    '<defs><linearGradient id="sisg" x1="0" y1="0" x2="1" y2="1">'
    '<stop offset="0" stop-color="#0ea5c4"/><stop offset="1" stop-color="#22d3ee"/>'
    "</linearGradient></defs>"
    '<rect width="64" height="64" rx="14" fill="#0a1628"/>'
    '<circle cx="32" cy="32" r="25.5" fill="#22d3ee"/>'
    '<circle cx="32" cy="32" r="22.7" fill="#fefbf3"/>'
    '<circle cx="32" cy="32" r="19.8" fill="url(#sisg)"/>'
    '<circle cx="32" cy="32" r="7.4" fill="#fefbf3"/>'
    "</svg>"
)

I18N = {
    "en": (
        "Sister site",
        "The same primary-source reference, for the UAE: Joby in Dubai, Archer in "
        "Abu Dhabi, GCAA, vertiports and routes.",
    ),
    "fr": (
        "Site frère",
        "La même référence en sources primaires, pour les Émirats : Joby à Dubaï, "
        "Archer à Abou Dabi, GCAA, vertiports et routes.",
    ),
    "de": (
        "Schwesterseite",
        "Dieselbe Primärquellen-Referenz für die VAE: Joby in Dubai, Archer in "
        "Abu Dhabi, GCAA, Vertiports und Routen.",
    ),
    "ar": (
        "الموقع الشقيق",
        "المرجع نفسه القائم على المصادر الأولية، للإمارات: جوبي في دبي، آرتشر في أبوظبي، الهيئة العامة للطيران المدني، الفرتيبورت والمسارات.",
    ),
    "zh": (
        "姊妹站",
        "同样以一手来源为准的参考站点：迪拜 Joby、阿布扎比 Archer、GCAA、垂直起降场与航线。",
    ),
}
# ---------------------------------------------------------------------------

MARK_OPEN = "<!-- sister-site -->"
MARK_CLOSE = "<!-- /sister-site -->"
FOOTER = '<footer class="site">'
LANG_DIRS = {"ar", "fr", "de", "zh"}


def block(lang: str) -> str:
    label, desc = I18N[lang]
    href = SISTER_URL if lang == "en" else f"{SISTER_URL}{lang}/"
    return (
        f"{MARK_OPEN}\n"
        '<aside class="sister-site" style="background:var(--bone);border-top:1px solid var(--rule)">\n'
        '  <div class="inner" style="padding-top:1.15rem;padding-bottom:1.15rem">\n'
        f'    <a href="{href}" style="display:flex;align-items:center;gap:.9rem;'
        'text-decoration:none;color:var(--ink)">\n'
        f"      {SISTER_LOGO}\n"
        "      <span>\n"
        '        <span style="display:block;font-size:.68rem;letter-spacing:.14em;'
        f'text-transform:uppercase;color:var(--muted)">{label}</span>\n'
        '        <span style="display:block;font-weight:700">'
        f"{SISTER_NAME} — {SISTER_DOMAIN}</span>\n"
        '        <span style="display:block;font-size:.85rem;color:var(--muted)">'
        f"{desc}</span>\n"
        "      </span>\n"
        "    </a>\n"
        "  </div>\n"
        "</aside>\n"
        f"{MARK_CLOSE}\n"
    )


def lang_of(rel: pathlib.PurePath) -> str:
    head = rel.parts[0] if len(rel.parts) > 1 else ""
    return head if head in LANG_DIRS else "en"


def main() -> int:
    root = pathlib.Path(__file__).resolve().parent
    injected = refreshed = skipped = 0
    for path in sorted(root.rglob("*.html")):
        rel = path.relative_to(root)
        if rel.parts[0] == ".git":
            continue
        html = path.read_text(encoding="utf-8")
        if FOOTER not in html:
            skipped += 1
            continue
        blk = block(lang_of(rel))
        if MARK_OPEN in html:
            new = re.sub(
                re.escape(MARK_OPEN) + r".*?" + re.escape(MARK_CLOSE) + r"\n?",
                blk,
                html,
                count=1,
                flags=re.S,
            )
            refreshed += 1
        else:
            new = html.replace(FOOTER, blk + FOOTER, 1)
            injected += 1
        if new != html:
            path.write_text(new, encoding="utf-8")
    print(f"sister-site band: {injected} injected, {refreshed} refreshed, {skipped} skipped (no footer)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
