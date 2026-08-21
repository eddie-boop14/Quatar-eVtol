#!/usr/bin/env python3
"""Make .reveal content visible by default; let JS opt into hiding it.

.reveal{opacity:0} + JS adding .in meant every page's reveal content was
invisible to any agent that does not run JS. robots.txt invites nine AI
crawlers by name and most do not execute JavaScript.

Scoping to html.js inverts the default: no JS (or no IntersectionObserver)
means no hiding rule at all. The class is set from an inline head script
gated on IntersectionObserver, so the animation only arms when it can run.
"""
import pathlib, re, sys, collections

repo = pathlib.Path(sys.argv[1])
SCRIPT = ("<script>if('IntersectionObserver' in window)"
          "document.documentElement.classList.add('js')</script>")
st = collections.Counter()

for f in sorted(repo.rglob("*.html")):
    if ".git" in f.parts:
        continue
    s = orig = f.read_text(encoding="utf-8")
    if ".reveal.in{" not in s:
        st["skipped_no_js_reveal"] += 1      # 404.html self-reveals via CSS animation
        continue

    s, n1 = re.subn(r'(?<!\.js )\.reveal\{opacity:0', 'html.js .reveal{opacity:0', s)
    s, n2 = re.subn(r'(?<!\.js )\.reveal\.in\{',      'html.js .reveal.in{',      s)
    s, n3 = re.subn(r'(?<!\.js )\.reveal\{opacity:1', 'html.js .reveal{opacity:1', s)

    if SCRIPT not in s:
        assert "</head>" in s, f
        s = s.replace("</head>", SCRIPT + "</head>", 1)
        st["script_added"] += 1

    st["base_scoped"] += n1; st["in_scoped"] += n2; st["rmotion_scoped"] += n3
    if s != orig:
        f.write_text(s, encoding="utf-8"); st["files_changed"] += 1

for k, v in sorted(st.items()): print(f"  {k}: {v}")
