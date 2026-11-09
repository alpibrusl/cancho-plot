"""The gate of the landing page (docs/design.md section 16).

The page and its gallery are made again in a temporary directory and must be byte for byte the committed site/; the page must be well-formed XML, load nothing from outside (no script, no
stylesheet or image or font from another origin, no `src`), link only to this repository and to cancho, and show, for every gallery chart, the command that made it.

    PLOT=build/plot python3 scripts/check_site.py
"""
import os
import re
import subprocess
import sys
import tempfile
import xml.dom.minidom

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import make_gallery as g

SITE = os.path.join(ROOT, "site")


def files(base):
    out = {}
    for d, _, names in os.walk(base):
        for n in names:
            p = os.path.join(d, n)
            out[os.path.relpath(p, base)] = open(p, "rb").read()
    return out


def check():
    bad = []
    with tempfile.TemporaryDirectory() as t:
        g.build(t)
        fresh, kept = files(t), files(SITE)
    for name in sorted(set(fresh) | set(kept)):
        if name not in kept:
            bad.append("%s is made but not committed" % name)
        elif name not in fresh:
            bad.append("%s is committed but no longer made" % name)
        elif fresh[name] != kept[name]:
            bad.append("%s is not what the binary writes now" % name)
    page = kept.get("index.html", b"").decode()
    try:
        xml.dom.minidom.parseString(page)
    except Exception as e:
        bad.append("index.html is not well-formed: %s" % e)
    if re.search(r"<script|<link|<img|<iframe|<object|\bsrc=|@import|url\(", page):
        bad.append("the page loads something (script, link, img, src, @import or url())")
    for href in re.findall(r'href="([^"]*)"', page):
        local = not re.match(r"[a-z]+:", href)
        ok = local or href.startswith("https://github.com/alpibrusl/")
        if not ok:
            bad.append("an outside link: %s" % href)
        if local and not os.path.exists(os.path.join(SITE, href)):
            bad.append("a link to a file that is not there: %s" % href)
    shown = re.findall(r'<p class="cmd"><code>([^<]*)</code>', page)
    for (gid, title, text, data, args, kind), cmd in zip(g.GALLERY, shown):
        want = (g.shell(args) + " < " + data).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        if cmd != want:
            bad.append("the command shown for %s is %r, not %r" % (gid, cmd, want))
    if len(shown) != len(g.GALLERY):
        bad.append("%d commands shown for %d charts" % (len(shown), len(g.GALLERY)))
    # every chart in the page is an inline svg of the gallery file
    for gid, *_rest, kind in g.GALLERY:
        if kind == "svg" and kept.get("gallery/%s.svg" % gid, b"").decode().strip() not in page:
            bad.append("the page does not embed gallery/%s.svg" % gid)
    return bad


if __name__ == "__main__":
    bad = check()
    for b in bad:
        print("FAIL:", b)
    if bad:
        sys.exit(1)
    print("check_site: ok (%d charts embedded, page well-formed, nothing loaded from outside, every command shown)" % len(g.GALLERY))
