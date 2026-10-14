#!/usr/bin/env python3
"""Ping IndexNow (Bing, Yandex, Seznam, Naver…) with changed URLs.

The key file lives at the site root (KEY.txt, containing KEY), which is how the
engines verify we own the host. One POST to api.indexnow.org is shared with
every participating engine.

  python3 indexnow.py --all                  # every URL in sitemap.xml
  python3 indexnow.py --changed BASE HEAD    # pages touched between two commits
  add --dry-run to print the URL list without sending

Run by .github/workflows/indexnow.yml after each production deploy of main.
"""
import json
import pathlib
import re
import subprocess
import sys
import urllib.request

# ---- per-site config -------------------------------------------------------
HOST = "qatarevtol.com"
KEY = "4f659c51b867430a9ca1808071637e3d"
# ---------------------------------------------------------------------------
ENDPOINT = "https://api.indexnow.org/indexnow"
ROOT = pathlib.Path(__file__).resolve().parent
BATCH = 10000  # protocol maximum per request


def sitemap_urls():
    return re.findall(r"<loc>([^<]+)</loc>", (ROOT / "sitemap.xml").read_text(encoding="utf-8"))


def changed_urls(base, head):
    if set(base) <= {"0"}:  # first push of a branch: no "before" commit
        cmd = ["git", "show", "--name-only", "--diff-filter=AMR", "--format=", head]
    else:
        cmd = ["git", "diff", "--name-only", "--diff-filter=AMR", f"{base}..{head}"]
    out = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
    live = set(sitemap_urls())
    urls = []
    for f in out:
        if not f.endswith(".html"):
            continue
        p = f[: -len("index.html")] if f.endswith("index.html") else f
        u = f"https://{HOST}/{p}"
        if u in live:  # only canonical, sitemap-listed pages
            urls.append(u)
    return sorted(set(urls))


def submit(urls):
    for i in range(0, len(urls), BATCH):
        body = json.dumps({
            "host": HOST,
            "key": KEY,
            "keyLocation": f"https://{HOST}/{KEY}.txt",
            "urlList": urls[i:i + BATCH],
        }).encode()
        req = urllib.request.Request(ENDPOINT, data=body, method="POST",
                                     headers={"Content-Type": "application/json; charset=utf-8"})
        with urllib.request.urlopen(req, timeout=30) as r:
            print(f"indexnow: {len(urls[i:i + BATCH])} URLs → HTTP {r.status}")


def main(argv):
    dry = "--dry-run" in argv
    argv = [a for a in argv if a != "--dry-run"]
    if argv[:1] == ["--all"]:
        urls = sitemap_urls()
    elif argv[:1] == ["--changed"] and len(argv) == 3:
        urls = changed_urls(argv[1], argv[2])
    else:
        print(__doc__)
        return 2
    if not urls:
        print("indexnow: nothing to submit")
        return 0
    if dry:
        print("\n".join(urls))
        print(f"indexnow: {len(urls)} URLs (dry run)")
        return 0
    submit(urls)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
