"""The gate of `plot --term svg` (docs/design.md section 13).

An independent implementation of the section (Python floats in the order the section gives, the ticks from exact fractions) renders 200 random charts and judges the program on them; the SVG
must be well-formed XML; hand-checked fragments, the refusals and garbage input; and every mutant of the sources (--mutants, needs CANCHO) must fail the gate.

    PLOT=build/plot python3 scripts/check_svg.py [--mutants]
"""
import os
import random
import subprocess
import sys
import tempfile
import xml.dom.minidom
from fractions import Fraction

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_dumb as d                                       # the ticks and the table reading are the same

ROOT = d.ROOT
PLOT = d.PLOT
COLORS = ["0550ae", "bc4c00", "1a7f37", "8250df", "cf222e"]


def fx(v):
    """2 decimals, correctly rounded from the double (a tie to the even digit), trailing zeros and a bare point dropped, -0 as 0"""
    t = "%.2f" % v
    if "." in t:
        t = t.rstrip("0").rstrip(".")
    return t


def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def render(xs, ys, names, W=640, H=400, title=None, lines=False, ann=None):
    """xs, ys: Fractions (exact decimals); the program reads them as doubles."""
    vl, hl, bands, diag = ann or ([], [], [], False)
    xa, ya = d.axis(list(xs) + list(vl), 6), d.axis([v for col in ys for v in col] + list(hl) + [e for b in bands for e in b], 5)
    fl = [float(v) for v in xs]
    fy = [[float(v) for v in col] for col in ys]
    xlo, xhi = float(xa[0]), float(xa[1])
    ylo, yhi = float(ya[0]), float(ya[1])
    xm, xe, xk0, xk1 = xa[3], xa[4], xa[5], xa[6]
    ym, ye, yk0, yk1 = ya[3], ya[4], ya[5], ya[6]
    ylabels = [(float(Fraction(k * ym) * Fraction(10) ** ye), d.label(k * ym, ye)) for k in range(yk0, yk1 + 1)]
    xlabels = [(float(Fraction(k * xm) * Fraction(10) ** xe), d.label(k * xm, xe)) for k in range(xk0, xk1 + 1)]
    g = max(len(t) for _, t in ylabels)
    left, top = 12 + 8 * g, (36 if title is not None else 12)
    x0, x1, y1, y2 = left, W - 16, top, H - 44
    if x1 - x0 < 20 or y2 - y1 < 20:
        return None
    pw, ph = float(x1 - x0), float(y2 - y1)
    X = lambda x: x0 + (x - xlo) / (xhi - xlo) * pw
    Y = lambda y: y1 + (yhi - y) / (yhi - ylo) * ph
    n, k = len(xs), len(ys)
    label = ((esc(title) + ": ") if title is not None else "") + "%d series, %d points" % (k, n)
    out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" role="img" aria-label="%s">' % (W, H, W, H, label),
           '<g fill="none" stroke="currentColor" stroke-width="1">',
           '<path d="M %s %s V %s H %s"/>' % (fx(x0), fx(y1), fx(y2), fx(x1))]
    for v, _ in ylabels:
        out.append('<path d="M %s %s h-4"/>' % (fx(x0), fx(Y(v))))
    for v, _ in xlabels:
        out.append('<path d="M %s %s v4"/>' % (fx(X(v)), fx(y2)))
    out += ['</g>', '<g font-family="sans-serif" font-size="12" fill="currentColor">']
    if title is not None:
        out.append('<text x="%s" y="20" text-anchor="middle" font-size="14">%s</text>' % (fx(W / 2), esc(title)))
    for v, t in ylabels:
        out.append('<text x="%s" y="%s" text-anchor="end">%s</text>' % (fx(x0 - 8), fx(Y(v) + 4), t))
    prev = None
    for v, t in xlabels:
        px = X(v)
        if prev is not None and px - prev < 8 * (len(t) + 1):
            continue
        out.append('<text x="%s" y="%s" text-anchor="middle">%s</text>' % (fx(px), fx(y2 + 18), t))
        prev = px
    for j, nm in enumerate(names):
        out.append('<text x="%s" y="%s">%s</text>' % (fx(x0 + 150 * j + 14), fx(H - 8), esc(nm)))
    out.append('</g>')
    dash = ' fill="none" stroke="currentColor" stroke-width="1" stroke-dasharray="4 3"/>'
    for lo, hi in bands:
        out.append('<rect x="%s" y="%s" width="%s" height="%s" fill="var(--band, currentColor)" fill-opacity="0.12"/>' % (fx(x0), fx(Y(float(hi))), fx(x1 - x0), fx(Y(float(lo)) - Y(float(hi)))))
    for v in hl:
        out.append('<path d="M %s %s H %s"%s' % (fx(x0), fx(Y(float(v))), fx(x1), dash))
    for v in vl:
        out.append('<path d="M %s %s V %s"%s' % (fx(X(float(v))), fx(y1), fx(y2), dash))
    t0, t1 = max(xlo, ylo), min(xhi, yhi)
    if diag and t0 < t1:
        out.append('<path d="M %s %s L %s %s" fill="none" stroke="currentColor" stroke-width="1" stroke-dasharray="1 3"/>' % (fx(X(t0)), fx(Y(t0)), fx(X(t1)), fx(Y(t1))))
    for j in range(k):
        pts = [(X(a), Y(b)) for a, b in zip(fl, fy[j])]
        if lines:
            dd = "M %s %s" % (fx(pts[0][0]), fx(pts[0][1])) + ("".join(" L %s %s" % (fx(a), fx(b)) for a, b in pts[1:]) if n > 1 else " h0")
            out.append('<path d="%s" fill="none" stroke="var(--series-%d, #%s)" stroke-width="1.5" stroke-linecap="round"/>' % (dd, j + 1, COLORS[j]))
        else:
            dd = " ".join("M %s %s h0" % (fx(a), fx(b)) for a, b in pts)
            out.append('<path d="%s" fill="none" stroke="var(--series-%d, #%s)" stroke-width="4" stroke-linecap="round"/>' % (dd, j + 1, COLORS[j]))
    for j in range(k):
        out.append('<rect x="%s" y="%s" width="10" height="10" fill="var(--series-%d, #%s)"/>' % (fx(x0 + 150 * j), fx(H - 17), j + 1, COLORS[j]))
    out.append("</svg>")
    return "\n".join(out) + "\n"


def run(exe, args, data):
    return subprocess.run([exe] + args, input=data.encode(), capture_output=True)


def gate(exe):
    bad = []
    # a hand-checked fragment: the axes of  x: 0 1 2, y: 0 1 2, 640x400, no title (ticks 0.0 .. 2.0 step 0.5; g = 3; x0 = 36, x1 = 624, y1 = 12, y2 = 356)
    p = run(exe, ["--x", "x", "--y", "y", "--term", "svg", "--with", "lines"], "x,y\n0,0\n1,1\n2,2\n")
    t = p.stdout.decode()
    for frag in ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 400" width="640" height="400" role="img" aria-label="1 series, 3 points">',
                 '<path d="M 36 12 V 356 H 624"/>',
                 '<path d="M 36 356 h-4"/>', '<path d="M 36 12 h-4"/>',                       # y = 0 at the bottom, y = 2 at the top
                 '<text x="28" y="360" text-anchor="end">0.0</text>',
                 '<path d="M 36 356 L 330 184 L 624 12" fill="none" stroke="var(--series-1, #0550ae)" stroke-width="1.5" stroke-linecap="round"/>',
                 '<rect x="36" y="383" width="10" height="10" fill="var(--series-1, #0550ae)"/>']:
        if frag not in t:
            bad.append("hand fragment missing: %s" % frag)
    rng = random.Random(20261111)
    for i in range(200):
        n = rng.randint(1, 30)
        k = rng.randint(1, 5)
        scale = rng.choice([Fraction(1, 100), Fraction(1), Fraction(250)])
        xs = [Fraction(rng.randint(-300, 300), rng.choice([1, 10, 100])) * scale for _ in range(n)]
        ys = [[Fraction(rng.randint(-300, 300), rng.choice([1, 10, 100])) * scale for _ in range(n)] for _ in range(k)]
        W, H = rng.randint(200, 900), rng.randint(120, 600)
        title = rng.choice([None, "t", "A & B <title> \"q\"", "x" * 60, "\u0100\u00e9"])
        names = ["s%d" % j if rng.random() < 0.7 else "n<%d>&" % j for j in range(k)]
        lines = rng.random() < 0.5
        ann, aflags = d.random_ann(rng, scale) if rng.random() < 0.5 else (None, [])
        header = "t," + ",".join(names)
        data = header + "\n" + "".join(d.dec(xs[r]) + "," + ",".join(d.dec(ys[j][r]) for j in range(k)) + "\n" for r in range(n))
        args = ["--x", "t", "--y", ",".join(names), "--term", "svg", "--size", "%dx%d" % (W, H)] + (["--title", title] if title is not None else []) + (["--with", "lines"] if lines else []) + aflags
        want = render(xs, ys, names, W, H, title, lines, ann)
        p = run(exe, args, data)
        got = p.stdout.decode()
        if want is None:
            if p.returncode != 2 or b"plot.size-invalid" not in p.stderr:
                bad.append("random %d: a plot area under 20 should be refused, exit %d" % (i, p.returncode))
            continue
        if p.returncode != 0 or got != want:
            at = next((j for j, (a, b) in enumerate(zip(got.split("\n"), want.split("\n"))) if a != b), 0)
            bad.append("random %d (%d points, %d series, %dx%d, lines %s): line %d\n got  %s\n want %s" % (i, n, k, W, H, lines, at, got.split("\n")[at][:200] if got else p.stderr[:100], want.split("\n")[at][:200]))
            if len(bad) > 2:
                break
            continue
        try:
            xml.dom.minidom.parseString(got)
        except Exception as e:
            bad.append("random %d is not well-formed XML: %s" % (i, e))
    # the edges: a plot area exactly 20 wide (g = 7: the labels 1000.00 .. 1000.05; W = 104), and labels exactly 8 (len + 1) apart (x 0..2, g = 3, 4 intervals of 32; W = 180)
    edge = [(104, [Fraction(0), Fraction(1)], [Fraction(100000, 100), Fraction(100005, 100)]), (180, [Fraction(0), Fraction(2)], [Fraction(0), Fraction(2)])]
    for W, xs, ys in edge:
        data = "x,y\n" + "".join("%s,%s\n" % (d.dec(xs[r]), d.dec(ys[r])) for r in range(2))
        p = run(exe, ["--x", "x", "--y", "y", "--term", "svg", "--size", "%dx300" % W], data)
        if p.returncode != 0 or p.stdout.decode() != render(xs, [ys], ["y"], W, 300):
            bad.append("edge W=%d: exit %d\n%s" % (W, p.returncode, p.stdout.decode()[:300]))
    p = run(exe, ["--x", "x", "--y", "y", "--term", "svg", "--size", "103x300"], "x,y\n0,1000\n1,1000.05\n")
    if p.returncode != 2 or b"plot.size-invalid" not in p.stderr:
        bad.append("W=103 with 7-character labels should leave 19 pixels: exit %d" % p.returncode)
    # ranges that only touch: x in [0, 2], y in [2, 4], so the diagonal has no length and is not drawn
    xs, ys = [Fraction(0), Fraction(2)], [[Fraction(2), Fraction(4)]]
    p = run(exe, ["--x", "x", "--y", "y", "--term", "svg", "--diag"], "x,y\n0,2\n2,4\n")
    if p.returncode != 0 or p.stdout.decode() != render(xs, ys, ["y"], 640, 400, None, False, ([], [], [], True)):
        bad.append("touching ranges with --diag:\n%s" % p.stdout.decode()[:300])
    ok = "x,y\n1,2\n3,4\n"
    refusals = [
        (["--x", "x", "--y", "y", "--term", "svg", "--title", "a\x1fb"], ok, "plot.text-invalid"),
        (["--x", "x", "--y", "y", "--term", "svg", "--title", "a\x7fb"], ok, "plot.text-invalid"),
        (["--x", "x", "--y", "y", "--term", "svg", "--title", "\u0100"], ok, None),                  # U+0100 is the bytes c4 80: bytes above 0x7f are text
        (["--x", "x", "--y", "y", "--term", "svg", "--size", "99x400"], ok, "plot.size-invalid"),
        (["--x", "x", "--y", "y", "--term", "svg", "--size", "2001x400"], ok, "plot.size-invalid"),
        (["--x", "x", "--y", "y", "--term", "svg", "--size", "640x99"], ok, "plot.size-invalid"),
        (["--x", "x", "--y", "y", "--term", "svg", "--size", "640x1201"], ok, "plot.size-invalid"),
        (["--x", "x", "--y", "y", "--term", "svg", "--size", "100x100", "--title", "t"], "x,y\n1,2\n3,4\n", None),     # the smallest size that fits is accepted
        (["--x", "x", "--y", "y", "--term", "svg", "--size", "60x20"], ok, "plot.size-invalid"),                          # a size that suits dumb but not svg
        (["--x", "x", "--y", "y", "--term", "svg", "--title", "a\x01b"], ok, "plot.text-invalid"),
        (["--x", "1", "--y", "2", "--term", "svg"], "x,y\x01\n1,2\n", "plot.text-invalid"),
        (["--x", "x", "--y", "y", "--term", "svg"], 'x,y\n1,"2"\n', "plot.csv-quote"),
        (["--x", "x", "--y", "y", "--term", "svg"], "", "plot.empty"),
        (["--x", "x", "--y", "y", "--term", "png"], ok, "plot.usage"),
    ]
    for args, data, rule in refusals:
        p = run(exe, args, data)
        if rule is None:
            if p.returncode != 0:
                bad.append("%r was refused: %r" % (args, p.stderr[:100]))
        elif p.returncode != 2 or p.stdout or ('"%s"' % rule).encode() not in p.stderr:
            bad.append("refusal %s %r: exit %d, stderr %r" % (rule, args, p.returncode, p.stderr[:100]))
    # one point as lines, a constant series, the widest numbers
    for data in ("x,y\n1,1\n", "x,y\n1,1\n1,1\n", "x,y\n-1e14,0\n1e14,1\n"):
        p = run(exe, ["--x", "x", "--y", "y", "--term", "svg", "--with", "lines"], data)
        if p.returncode != 0:
            bad.append("%r refused: %r" % (data, p.stderr[:100]))
    rng2 = random.Random(7)
    pieces = ["", "\n", "x,y\n", "x,y\r\n1,2\r\n", ",", "1,2\n", "a\n", "\x00", "x,y\n1,2", "1e5,1e5\n", "-0,0\n", "é,y\n", "x,x\n1,1\n"]
    for _ in range(100):
        data = "".join(rng2.choice(pieces) for _ in range(rng2.randint(0, 6)))
        args = rng2.choice([["--x", "x", "--y", "y"], ["--x", "1", "--y", "2"], ["--x", "x", "--y", "x,y"]]) + ["--term", "svg"] + rng2.choice([[], ["--with", "lines"], ["--size", "300x200"]])
        p = run(exe, args, data)
        if p.returncode not in (0, 2):
            bad.append("garbage %r %r: exit %d" % (args, data[:40], p.returncode))
    return bad


MUTANTS = [
    ('lib/plot/svg.cho', 'let ytop = y1f + (yhi2 - ann[17 + 2 * u])', 'let ytop = y1f + (yhi2 - ann[16 + 2 * u])'),
    ('lib/plot/svg.cho', 'let ybot = y1f + (yhi2 - ann[16 + 2 * u])', 'let ybot = y1f + (yhi2 - ann[17 + 2 * u])'),
    ('lib/plot/svg.cho', 'out = num(heap, out, ybot - ytop);', 'out = num(heap, out, ybot - ytop + 1.0);'),
    ('lib/plot/svg.cho', 'fill-opacity=\\"0.12\\"', 'fill-opacity=\\"0.2\\"'),
    ('lib/plot/svg.cho', 'var(--band, currentColor)', 'var(--bands, currentColor)'),
    ('lib/plot/svg.cho', 'stroke-dasharray=\\"4 3\\"/>");\n        out = nl(heap, out);\n        u = u + 1;\n    }\n    u = 0;\n    while u < ac[0] {', 'stroke-dasharray=\\"4 4\\"/>");\n        out = nl(heap, out);\n        u = u + 1;\n    }\n    u = 0;\n    while u < ac[0] {'),
    ('lib/plot/svg.cho', 'stroke-dasharray=\\"4 3\\"/>");\n        out = nl(heap, out);\n        u = u + 1;\n    }\n    var t0', 'stroke-dasharray=\\"4 4\\"/>");\n        out = nl(heap, out);\n        u = u + 1;\n    }\n    var t0'),
    ('lib/plot/svg.cho', 'stroke-dasharray=\\"1 3\\"', 'stroke-dasharray=\\"1 4\\"'),
    ('lib/plot/svg.cho', 'let yy = y1f + (yhi2 - ann[8 + u])', 'let yy = y1f + (yhi2 - ann[u])'),
    ('lib/plot/svg.cho', 'let xx = x0f + (ann[u] - xlo2)', 'let xx = x0f + (ann[8 + u] - xlo2)'),
    ('lib/plot/svg.cho', 'if ac[3] == 1 && t0 < t1 {', 'if ac[3] == 1 && t0 <= t1 {'),
    ('lib/plot/svg.cho', 'if ylo2 > t0 {', 'if ylo2 < t0 {'),
    ('lib/plot/svg.cho', 'if yhi2 < t1 {', 'if yhi2 > t1 {'),
    ('lib/plot/svg.cho', 'out = num(heap, out, x0f + (t1 - xlo2) / (xhi2 - xlo2) * pw);', 'out = num(heap, out, x0f + (t0 - xlo2) / (xhi2 - xlo2) * pw);'),
    ('lib/plot/svg.cho', 'while u < ac[2] {', 'while u < ac[2] - 1 {'),
    ('lib/plot/svg.cho', 'while u < ac[1] {', 'while u < ac[1] - 1 {'),
    ('lib/plot/svg.cho', 'while u < ac[0] {', 'while u < ac[0] - 1 {'),
        # not listed, equivalent: `end > 0` to `end > 1` in svg.num (the text always has a point, where the loop stops)
    ("lib/plot/svg.cho", "if end > 0 && int_of(sc[end - 1]) == '.' {", "if end > 1 && int_of(sc[end - 1]) == '.' && false {"),
    ("lib/plot/svg.cho", "out = buffer.append(heap, out, \"&amp;\");", "out = buffer.append(heap, out, \"&\");"),
    ("lib/plot/svg.cho", "out = buffer.append(heap, out, \"&lt;\");", "out = buffer.append(heap, out, \"<\");"),
    ("lib/plot/svg.cho", "out = buffer.append(heap, out, \"&gt;\");", "out = buffer.append(heap, out, \">\");"),
    ("lib/plot/svg.cho", "out = buffer.append(heap, out, \"&quot;\");", "out = buffer.append(heap, out, \"'\");"),
    ("lib/plot/svg.cho", "return \"bc4c00\";", "return \"bc4c01\";"),
    ("lib/plot/svg.cho", "return \"1a7f37\";", "return \"1a7f38\";"),
    ("lib/plot/svg.cho", "return \"8250df\";", "return \"8250de\";"),
    ("lib/plot/svg.cho", "return \"cf222e\";", "return \"cf222f\";"),
    ("lib/plot/svg.cho", "return \"0550ae\";", "return \"0550af\";"),
    ("lib/plot/svg.cho", "var top = 12;\n    if has_title {\n        top = 36;", "var top = 12;\n    if has_title {\n        top = 35;"),
    ("lib/plot/svg.cho", "let x0 = 12 + 8 * g;", "let x0 = 12 + 7 * g;"),
    ("lib/plot/svg.cho", "let x1 = w - 16;", "let x1 = w - 15;"),
    ("lib/plot/svg.cho", "let y2 = hh - 44;", "let y2 = hh - 43;"),
    ("lib/plot/svg.cho", "if x1 - x0 < 20 || y2 - y1 < 20 {", "if x1 - x0 < 21 || y2 - y1 < 20 {"),
    ("lib/plot/svg.cho", "if x1 - x0 < 20 || y2 - y1 < 20 {", "if x1 - x0 < 20 || y2 - y1 < 21 {"),
    ("lib/plot/svg.cho", "let yy = y1f + (yhi2 - ticks.value(q, ym, ye)) / (yhi2 - ylo2) * ph;\n        out = put(heap, out, \"<path d=\\\"M \");", "let yy = y1f + (ticks.value(q, ym, ye) - ylo2) / (yhi2 - ylo2) * ph;\n        out = put(heap, out, \"<path d=\\\"M \");"),
    ("lib/plot/svg.cho", "out = num(heap, out, yy + 4.0);", "out = num(heap, out, yy + 5.0);"),
    ("lib/plot/svg.cho", "out = numi(heap, out, x0 - 8);", "out = numi(heap, out, x0 - 7);"),
    ("lib/plot/svg.cho", "out = numi(heap, out, y2 + 18);", "out = numi(heap, out, y2 + 17);"),
    ("lib/plot/svg.cho", "out = num(heap, out, float_of(w) / 2.0);", "out = num(heap, out, float_of(w) / 3.0);"),
    ("lib/plot/svg.cho", "if !have_prev || xx - prev >= 8.0 * float_of(ln + 1) {", "if !have_prev || xx - prev > 8.0 * float_of(ln + 1) {"),
    ("lib/plot/svg.cho", "if !have_prev || xx - prev >= 8.0 * float_of(ln + 1) {", "if !have_prev || xx - prev >= 8.0 * float_of(ln) {"),
    ("lib/plot/svg.cho", "out = numi(heap, out, x0 + 150 * j + 14);", "out = numi(heap, out, x0 + 150 * j + 13);"),
    ("lib/plot/svg.cho", "out = numi(heap, out, hh - 8);", "out = numi(heap, out, hh - 9);"),
    ("lib/plot/svg.cho", "out = numi(heap, out, hh - 17);", "out = numi(heap, out, hh - 16);"),
    ("lib/plot/svg.cho", "out = numi(heap, out, x0 + 150 * j);", "out = numi(heap, out, x0 + 140 * j);"),
    ("lib/plot/svg.cho", "if lines && n == 1 {", "if lines && n == 2 {"),
    ("lib/plot/svg.cho", "out = put(heap, out, \" stroke-width=\\\"1.5\\\" stroke-linecap=\\\"round\\\"/>\");", "out = put(heap, out, \" stroke-width=\\\"2\\\" stroke-linecap=\\\"round\\\"/>\");"),
    ("lib/plot/svg.cho", "out = put(heap, out, \" stroke-width=\\\"4\\\" stroke-linecap=\\\"round\\\"/>\");", "out = put(heap, out, \" stroke-width=\\\"3\\\" stroke-linecap=\\\"round\\\"/>\");"),
    ("lib/plot/svg.cho", "let px = x0f + (xs[i] - xlo2) / (xhi2 - xlo2) * pw;", "let px = x0f + (xs[i] - xlo2) / (xhi2 - xlo2) * pw + 0.01;"),
    ("lib/plot/svg.cho", "let py = y1f + (yhi2 - ys[j * n + i]) / (yhi2 - ylo2) * ph;", "let py = y1f + (yhi2 - ys[j * n + i]) / (yhi2 - ylo2) * ph - 0.01;"),
    ("lib/plot/chart.cho", "if c < 32 || c == 127 {", "if c < 31 || c == 127 {"),
    ("lib/plot/chart.cho", "if c < 32 || c == 127 {", "if c < 32 || c == 128 {"),
    ("lib/plot/chart.cho", "if c < 32 || c == 127 {", "if c < 32 {"),
    ("lib/plot/chart.cho", "if has_title && has_control(title) {", "if has_title && has_control(title) && false {"),
    ("tools/plot/main.cho", "ok = sw >= 100 && sw <= 2000 && sh >= 100 && sh <= 1200;", "ok = sw >= 101 && sw <= 2000 && sh >= 100 && sh <= 1200;"),
    ("tools/plot/main.cho", "ok = sw >= 100 && sw <= 2000 && sh >= 100 && sh <= 1200;", "ok = sw >= 100 && sw <= 2001 && sh >= 100 && sh <= 1200;"),
    ("tools/plot/main.cho", "ok = sw >= 100 && sw <= 2000 && sh >= 100 && sh <= 1200;", "ok = sw >= 100 && sw <= 2000 && sh >= 101 && sh <= 1200;"),
    ("tools/plot/main.cho", "ok = sw >= 100 && sw <= 2000 && sh >= 100 && sh <= 1200;", "ok = sw >= 100 && sw <= 2000 && sh >= 100 && sh <= 1201;"),
    ("tools/plot/main.cho", "w = 640;\n        hh = 400;", "w = 640;\n        hh = 401;"),
]


def mutants():
    cancho = os.environ["CANCHO"]
    killed = survivors = 0
    srcs = d.SRCS
    for path, old, new in MUTANTS:
        with tempfile.TemporaryDirectory() as t:
            for f in srcs:
                src = open(os.path.join(ROOT, f)).read()
                if f == path:
                    assert old in src, "mutant text not found: %s" % old
                    src = src.replace(old, new, 1)
                os.makedirs(os.path.join(t, os.path.dirname(f)), exist_ok=True)
                open(os.path.join(t, f), "w").write(src)
            exe = os.path.join(t, "plot")
            p = subprocess.run([cancho, "build"] + [t + "/" + f for f in srcs] + ["--std", "-o", exe], capture_output=True)
            if p.returncode != 0:
                print("mutant did not build (rewrite it): %s -> %s\n%s" % (old, new, p.stderr.decode()[:200]))
                sys.exit(1)
            if not gate(exe):
                print("MUTANT SURVIVED: %s -> %s" % (old, new))
                survivors += 1
                continue
            killed += 1
    print("%d mutants killed, %d survived" % (killed, survivors))
    if survivors:
        sys.exit(1)


if __name__ == "__main__":
    bad = gate(PLOT)
    for b in bad:
        print("FAIL:", b)
    if bad:
        sys.exit(1)
    print("check_svg: ok (hand fragments, 200 random charts well-formed, 14 refusals, 100 garbage inputs)")
    if "--mutants" in sys.argv:
        mutants()
