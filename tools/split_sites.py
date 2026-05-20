#!/usr/bin/env python3
"""Split the combined eVTOL build (site/) into two standalone sites: qatar/ and emirates/.

Reads the combined static build in ./site and regenerates ./qatar and ./emirates,
each rooted at its own domain, with only its own content, counts and sitemap.

Run from the repository root:  python3 tools/split_sites.py
Idempotent: it deletes and rebuilds the two output directories every run.
"""
import os, re, json, shutil, sys

SRC = "site"
LOCALES = ["", "ar", "de", "fr", "zh"]          # "" = English (root)
SECTIONS = ["aircraft", "routes", "vertiports", "operators", "regulators", "explainers"]
TOPLEVEL = ["index.html"] + [s + ".html" for s in SECTIONS]
LASTMOD = "2026-05-20"

SITES = {
    "qatar":    {"dir": "qatar",    "domain": "evtolquatar.com",
                 "brand": "Qatar eVTOL", "brand_em": "Qatar <em>eVTOL</em>",
                 "email": "hello@evtolquatar.com", "geo": "Qatar",
                 "keep_pillar": "pillar-qatar", "drop_pillar": "pillar-uae",
                 "dead_anchor": "#uae"},
    "emirates": {"dir": "emirates", "domain": "evtolemirates.com",
                 "brand": "UAE eVTOL", "brand_em": "UAE <em>eVTOL</em>",
                 "email": "hello@evtolemirates.com", "geo": "UAE",
                 "keep_pillar": "pillar-uae", "drop_pillar": "pillar-qatar",
                 "dead_anchor": "#qatar"},
}
OTHER = {"qatar": "emirates", "emirates": "qatar"}

# Pre-existing broken internal links in the build. slug -> (section, slug|None).
# None target => link is redirected to that section's listing page.
LINK_FIXUPS = {
    "dxb-to-palm-jumeirah": ("routes", "dxb-to-atlantis-the-royal"),  # real entity
    "auh-to-saadiyat":      ("routes", None),
    "auh-to-yas-island":    ("routes", None),
    "saudia-group":         ("operators", None),
}

# Optional /ar /de /fr /zh locale prefix in an internal URL.
LOC = r"(?:/(?:ar|de|fr|zh))?"

# Hub-stat chips are only shown for these statuses, in this order.
STAT_WHITELIST = ["operational", "under_construction", "announced", "planned"]
AR_DIGITS = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")

WARN = []


def localize_int(n, locale):
    return str(n).translate(AR_DIGITS) if locale == "ar" else str(n)


# --------------------------------------------------------------------------
# 1. Load the 49 entities from the homepage master-grid (the build's own truth)
# --------------------------------------------------------------------------
def load_entities():
    txt = open(os.path.join(SRC, "index.html"), encoding="utf-8").read()
    grid = txt.split('<section class="master-grid"', 1)[1].split("</section>", 1)[0]
    pat = re.compile(
        r'<a class="card[^"]*" href="/([a-z]+)/([a-z0-9-]+)\.html" '
        r'data-type="([^"]*)" data-country="([^"]*)" data-status="([^"]*)"')
    ents = {}
    for folder, slug, dtype, country, status in pat.findall(grid):
        ents[slug] = {"folder": folder, "slug": slug, "type": dtype,
                      "country": country, "status": status}
    return ents


def assign_site(country):
    if country == "Qatar":
        return "qatar"
    if country in ("UAE", "Saudi Arabia"):
        return "emirates"
    return "both"


# --------------------------------------------------------------------------
# 2. Link resolution / rewriting
# --------------------------------------------------------------------------
def resolve_href(href, site, keep):
    """Return a rewritten href, or None to leave it unchanged."""
    if not href.startswith("/"):
        return None
    body = href[1:]
    loc = ""
    m = re.match(r"^(ar|de|fr|zh)/(.*)$", body)
    if m:
        loc, body = m.group(1) + "/", m.group(2)
    locpfx = "/" + loc
    if body == "method":
        return locpfx + "#manifesto"
    if body == "contact":
        return "mailto:" + SITES[site]["email"]
    if body == "":
        return None
    base = body[:-5] if body.endswith(".html") else body
    if "/" not in base:
        return locpfx + base + ".html" if base in SECTIONS else None
    folder, _, slug = base.partition("/")
    if folder not in SECTIONS:
        return None
    if slug in LINK_FIXUPS:
        folder, slug = LINK_FIXUPS[slug]
        if slug is None:
            return locpfx + folder + ".html"
    if (folder, slug) in keep[site]:
        return locpfx + folder + "/" + slug + ".html"
    if (folder, slug) in keep[OTHER[site]]:
        return ("https://" + SITES[OTHER[site]]["domain"] + "/" + loc
                + folder + "/" + slug + ".html")
    WARN.append("unresolved link %s -> %s listing" % (href, folder))
    return locpfx + folder + ".html"


def rewrite_links(txt, site, keep):
    return re.sub(
        r'href="(/[^"]*)"',
        lambda m: 'href="%s"' % (resolve_href(m.group(1), site, keep) or m.group(1)),
        txt)


def normalize_jsonld_listing(txt, domain):
    # breadcrumb "item" URLs point at extensionless listing pages; add .html
    return re.sub(
        r'(https://' + re.escape(domain)
        + r'/(?:(?:ar|de|fr|zh)/)?(?:' + "|".join(SECTIONS) + r'))(?=")',
        r"\1.html", txt)


# --------------------------------------------------------------------------
# 3. Aggregate-page surgery
# --------------------------------------------------------------------------
def filter_cards_fragment(frag, keep_set):
    return re.sub(
        r'<a class="card [^"]*" href="' + LOC + r'/([a-z]+)/([a-z0-9-]+)\.html".*?</a>',
        lambda m: m.group(0) if (m.group(1), m.group(2)) in keep_set else "",
        frag, flags=re.S)


def surgery_homepage(txt, site, keep, entities_by_site):
    cfg = SITES[site]
    keep_set = keep[site]
    site_ents = entities_by_site[site]

    # 3a. drop the other country's pillar; filter master-grid cards (one per line)
    out = []
    for ln in txt.split("\n"):
        s = ln.strip()
        if s.startswith('<section class="pillar %s' % cfg["drop_pillar"]):
            continue
        m = re.match(r'<a class="card [^"]*" href="' + LOC
                     + r'/([a-z]+)/([a-z0-9-]+)\.html"', s)
        if m and (m.group(1), m.group(2)) not in keep_set:
            continue
        out.append(ln)
    txt = "\n".join(out)

    # 3b. pillar-global: keep only this site's cards + recompute its stats
    def fix_global(m):
        frag = filter_cards_fragment(m.group(0), keep_set)
        kept = {e["folder"] for e in site_ents
                if ("/%s/%s.html" % (e["folder"], e["slug"])) in frag}
        for sec in ("aircraft", "operators", "regulators"):
            if sec not in kept:
                frag = re.sub(
                    r'<a href="' + LOC + r'/%s\.html" class="pillar-stat".*?</a>' % sec,
                    "", frag, flags=re.S)
        return frag
    txt = re.sub(r'<section class="pillar pillar-global[^"]*".*?</section>',
                 fix_global, txt, flags=re.S)
    if site == "qatar":  # English-only retitle of the trimmed global pillar
        txt = txt.replace(">Aircraft, operators &amp; analysis<", ">Cross-Gulf analysis<")
        txt = txt.replace(
            ">Airframes, operators and explainer pieces that span both jurisdictions and beyond.<",
            ">Explainer pieces comparing Qatar with the wider Gulf.<")

    # 3c. map pins: keep only this site's vertiports
    keep_vp = {e["slug"] for e in site_ents if e["folder"] == "vertiports"}

    def fix_map(m):
        def keep_pin(pm):
            sm = re.search(r'href="' + LOC + r'/vertiports/([a-z0-9-]+)\.html"',
                           pm.group(0))
            return pm.group(0) if sm and sm.group(1) in keep_vp else ""
        return re.sub(r'<g class="map-pin[^"]*"[^>]*>.*?</g>', keep_pin,
                      m.group(0), flags=re.S)
    txt = re.sub(r'<section class="map-sect.*?</section>', fix_map, txt, flags=re.S)

    # 3d. counters-sect: recompute per-section totals
    for sec in SECTIONS:
        cnt = sum(1 for e in site_ents if e["folder"] == sec)
        txt = re.sub(
            r'(<a href="' + LOC + r'/%s\.html" class="counter[^"]*">.*?'
            r'<span class="counter-num" data-target=")\d+(")' % sec,
            r"\g<1>%d\2" % cnt, txt, flags=re.S)

    # 3e. filter-sect: total count + trim country options
    txt = txt.replace("49 total ", "%d total " % len(site_ents))
    drop_countries = ["Saudi Arabia", "UAE"] if site == "qatar" else ["Qatar"]
    for v in drop_countries:
        txt = re.sub(r'<option value="%s">.*?</option>' % re.escape(v), "", txt)

    # 3f. footer: drop the dead pillar anchor; hero/title geo rebrand (English only)
    txt = re.sub(r'<li><a href="%s">.*?</a></li>' % cfg["dead_anchor"], "", txt)
    txt = txt.replace('<div class="hero-eyebrow">Gulf · 2026',
                      '<div class="hero-eyebrow">%s · 2026' % cfg["geo"])
    txt = txt.replace("eVTOL Network · Gulf · 2026", "%s · 2026" % cfg["brand"])
    return txt


def surgery_listing(txt, section, site, keep, global_chip_statuses, locale):
    keep_set = keep[site]
    kept = []
    out = []
    for ln in txt.split("\n"):
        m = re.match(r'\s*<a class="hub-card[^"]*" href="' + LOC
                     + r'/([a-z]+)/([a-z0-9-]+)\.html"', ln)
        if m:
            if (m.group(1), m.group(2)) in keep_set:
                out.append(ln)
                kept.append(m.group(2))
        else:
            out.append(ln)
    txt = "\n".join(out)
    n = len(kept)

    # hero eyebrow "Label  count  word"
    txt = re.sub(r'(<div class="hub-eyebrow">[^<]*·\s*)\S+',
                 lambda m: m.group(1) + localize_int(n, locale), txt, count=1)
    if locale == "" and n == 1:
        txt = re.sub(r'(<div class="hub-eyebrow">[^<]*)1 entries</div>',
                     r"\g<1>1 entry</div>", txt)

    # hub-stats: recompute each chip by status, drop chips that fall to 0
    statuses = global_chip_statuses[section]
    counts = {st: sum(1 for s in kept
                      if ENTITIES[s]["status"] == st) for st in statuses}

    def fix_stats(m):
        chips = re.findall(r'<div class="hub-stat-chip[^"]*">.*?</div>', m.group(0))
        rebuilt = []
        for i, chip in enumerate(chips):
            st = statuses[i]
            c = counts.get(st, 0)
            if c == 0:
                continue
            rebuilt.append(re.sub(r'(<span class="hub-stat-num">)\d+(</span>)',
                                  r"\g<1>%d\2" % c, chip))
        return '<div class="hub-stats">' + "".join(rebuilt) + "</div>"
    txt = re.sub(r'<div class="hub-stats">.*?</div></div>',
                 lambda m: fix_stats(m) + "</div>", txt, count=1, flags=re.S)

    if n == 0:  # empty listing (Qatar has no operators) -> empty-state message
        txt = txt.replace(
            '<section class="hub-grid">',
            '<section class="hub-grid"><p class="hub-empty">'
            'Nothing is documented in this category yet.</p>', 1)
    return txt


# --------------------------------------------------------------------------
# 4. sitemap / robots / entities.json
# --------------------------------------------------------------------------
def write_sitemap(outdir, domain, site_ents):
    pages = [""] + [s + ".html" for s in SECTIONS]
    pages += sorted("%s/%s.html" % (e["folder"], e["slug"]) for e in site_ents)
    rows = []
    for page in pages:
        for loc in LOCALES:
            base = "https://%s/" % domain
            url = base + (loc + "/" if loc else "") + page
            alts = []
            for L in LOCALES:
                href = base + (L + "/" if L else "") + page
                alts.append('<xhtml:link rel="alternate" hreflang="%s" href="%s"/>'
                            % (L or "en", href))
            alts.append('<xhtml:link rel="alternate" hreflang="x-default" href="%s"/>'
                        % (base + page))
            rows.append("<url><loc>%s</loc><lastmod>%s</lastmod>%s</url>"
                        % (url, LASTMOD, "".join(alts)))
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
           'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
           + "\n".join(rows) + "\n</urlset>\n")
    open(os.path.join(outdir, "sitemap.xml"), "w", encoding="utf-8").write(xml)


def write_robots(outdir, domain):
    open(os.path.join(outdir, "robots.txt"), "w", encoding="utf-8").write(
        "User-agent: *\nAllow: /\n\nSitemap: https://%s/sitemap.xml\n" % domain)


def write_entities(outdir, site_slugs):
    data = json.load(open(os.path.join(SRC, "entities.json"), encoding="utf-8"))
    data["entities"] = [e for e in data["entities"] if e["slug"] in site_slugs]
    json.dump(data, open(os.path.join(outdir, "entities.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)


# --------------------------------------------------------------------------
# 5. Build one site
# --------------------------------------------------------------------------
def transform(txt, relpath, site, keep, entities_by_site, global_chip_statuses):
    cfg = SITES[site]
    segs = relpath.split("/")
    locale = segs[0] if segs[0] in ("ar", "de", "fr", "zh") else ""
    if locale:
        segs = segs[1:]
    fname = segs[-1]
    is_home = segs == ["index.html"]
    is_listing = (len(segs) == 1 and fname.endswith(".html")
                  and fname[:-5] in SECTIONS)

    # structural surgery first (operates on original markup)
    if is_home:
        txt = surgery_homepage(txt, site, keep, entities_by_site)
    elif is_listing:
        section = fname[:-5]
        txt = surgery_listing(txt, section, site, keep, global_chip_statuses, locale)

    # text rewrites
    txt = txt.replace("evtol-network.example", cfg["domain"])
    txt = txt.replace("eVTOL <em>Network</em>", cfg["brand_em"])
    txt = txt.replace("eVTOL Network", cfg["brand"])
    txt = rewrite_links(txt, site, keep)
    txt = normalize_jsonld_listing(txt, cfg["domain"])
    return txt


def build_site(site, entities_by_site, keep, global_chip_statuses):
    cfg = SITES[site]
    outdir = cfg["dir"]
    if os.path.exists(outdir):
        shutil.rmtree(outdir)
    site_ents = entities_by_site[site]
    site_slugs = {e["slug"] for e in site_ents}

    # collect source relpaths: top-level pages + this site's detail pages
    relpaths = []
    for loc in LOCALES:
        pre = (loc + "/") if loc else ""
        for tl in TOPLEVEL:
            relpaths.append(pre + tl)
        for e in site_ents:
            relpaths.append("%s%s/%s.html" % (pre, e["folder"], e["slug"]))

    for rel in relpaths:
        src = os.path.join(SRC, rel)
        txt = open(src, encoding="utf-8").read()
        txt = transform(txt, rel, site, keep, entities_by_site, global_chip_statuses)
        dst = os.path.join(outdir, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        open(dst, "w", encoding="utf-8").write(txt)

    # custom 404 page — site root, not localised, kept out of the sitemap
    src404 = os.path.join(SRC, "404.html")
    extra = 0
    if os.path.exists(src404):
        txt = open(src404, encoding="utf-8").read()
        txt = transform(txt, "404.html", site, keep, entities_by_site,
                        global_chip_statuses)
        open(os.path.join(outdir, "404.html"), "w", encoding="utf-8").write(txt)
        extra = 1

    write_sitemap(outdir, cfg["domain"], site_ents)
    write_robots(outdir, cfg["domain"])
    write_entities(outdir, site_slugs)
    return len(relpaths) + extra


# --------------------------------------------------------------------------
# 6. Verification crawl: every internal link must resolve to a real file
# --------------------------------------------------------------------------
def verify(site):
    outdir = SITES[site]["dir"]
    domain = SITES[site]["domain"]
    broken = []
    for root, _, files in os.walk(outdir):
        for f in files:
            if not f.endswith(".html"):
                continue
            txt = open(os.path.join(root, f), encoding="utf-8").read()
            for href in re.findall(r'href="(/[^"#]*)"', txt):
                target = href.lstrip("/")
                if target == "" or target.endswith("/"):
                    target += "index.html"
                if not os.path.exists(os.path.join(outdir, target)):
                    broken.append("%s/%s -> %s" % (root, f, href))
    leftover = []
    for root, _, files in os.walk(outdir):
        for f in files:
            if f.endswith((".html", ".xml", ".json", ".txt")):
                if "evtol-network.example" in open(os.path.join(root, f),
                                                   encoding="utf-8").read():
                    leftover.append(os.path.join(root, f))
    return broken, leftover


def check_counts(site, entities_by_site):
    """Every homepage/listing must show exactly this site's card set."""
    outdir = SITES[site]["dir"]
    site_ents = entities_by_site[site]
    bad = []
    for loc in LOCALES:
        pre = (loc + "/") if loc else ""
        home = open(os.path.join(outdir, pre + "index.html"), encoding="utf-8").read()
        grid = home.split('<section class="master-grid"', 1)[1].split("</section>", 1)[0]
        if grid.count('<a class="card ') != len(site_ents):
            bad.append("%sindex.html master-grid=%d expected=%d"
                       % (pre, grid.count('<a class="card '), len(site_ents)))
        for sec in SECTIONS:
            want = sum(1 for e in site_ents if e["folder"] == sec)
            page = open(os.path.join(outdir, pre + sec + ".html"),
                        encoding="utf-8").read()
            got = page.count('<a class="hub-card')
            if got != want:
                bad.append("%s%s.html cards=%d expected=%d" % (pre, sec, got, want))
    return bad


# --------------------------------------------------------------------------
def main():
    if not os.path.isdir(SRC):
        sys.exit("error: ./%s not found (run from repo root)" % SRC)
    global ENTITIES
    ENTITIES = load_entities()
    print("loaded %d entities from the build" % len(ENTITIES))

    keep = {"qatar": set(), "emirates": set()}
    entities_by_site = {"qatar": [], "emirates": []}
    for e in ENTITIES.values():
        s = assign_site(e["country"])
        targets = ["qatar", "emirates"] if s == "both" else [s]
        for t in targets:
            keep[t].add((e["folder"], e["slug"]))
            entities_by_site[t].append(e)

    global_chip_statuses = {}
    for sec in SECTIONS:
        present = {e["status"] for e in ENTITIES.values() if e["folder"] == sec}
        global_chip_statuses[sec] = [s for s in STAT_WHITELIST if s in present]

    for site in ("qatar", "emirates"):
        n = build_site(site, entities_by_site, keep, global_chip_statuses)
        print("built %-9s %3d entities, %3d pages -> %s/"
              % (site, len(entities_by_site[site]), n, SITES[site]["dir"]))

    ok = True
    for site in ("qatar", "emirates"):
        broken, leftover = verify(site)
        bad = check_counts(site, entities_by_site)
        print("verify %-9s broken-links=%d  leftover-domain=%d  card-count-errors=%d"
              % (site, len(broken), len(leftover), len(bad)))
        for b in broken[:20]:
            print("   BROKEN", b)
        for l in leftover[:20]:
            print("   LEFTOVER", l)
        for b in bad[:20]:
            print("   COUNT", b)
        ok = ok and not broken and not leftover and not bad

    if WARN:
        seen = sorted(set(WARN))
        print("link fixups applied (%d distinct):" % len(seen))
        for w in seen:
            print("  ", w)
    print("OK" if ok else "FAILED VERIFICATION")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
