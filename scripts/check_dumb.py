"""The gate of `plot --term dumb` (docs/design.md section 11).

An independent implementation of the section in exact fractions draws 200 random charts and judges the program on them; five charts drawn by hand from the section are written out below; every
refusal has an input; garbage input ends in 0 or 2; and every mutant of the sources (--mutants, needs CANCHO) must fail the gate.

    PLOT=build/plot python3 scripts/check_dumb.py [--mutants]
"""
import json
import os
import random
import subprocess
import sys
import tempfile
from fractions import Fraction

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLOT = os.environ.get("PLOT", os.path.join(ROOT, "build", "plot"))
GLYPHS = "*+xo#"


def label(n, e):
    sign = "-" if n < 0 else ""
    n = abs(n)
    if e >= 0:
        return sign + (str(n) + "0" * e if n else "0")
    d = -e
    s = str(n).rjust(d + 1, "0")
    return sign + s[:-d] + "." + s[-d:]


def step(span, n):
    raw = span / n
    e = 0
    f = raw
    while f >= 10:
        f /= 10
        e += 1
    while f < 1:
        f *= 10
        e -= 1
    if f <= Fraction(3, 2):
        return 1, e
    if f <= 3:
        return 2, e
    if f <= 7:
        return 5, e
    return 1, e + 1


def axis(vals, n):
    """(lo, hi, unit, m, e, first k, last k): the widened range of the values and its ticks."""
    lo, hi = min(vals), max(vals)
    if lo == hi:
        lo, hi = lo - 1, hi + 1
    m, e = step(hi - lo, n)
    unit = Fraction(m) * Fraction(10) ** e
    k0 = lo // unit
    k1 = -((-hi) // unit)
    return k0 * unit, k1 * unit, unit, m, e, k0, k1


def cell(v, lo, hi, size):
    """floor((v - lo) * size / (hi - lo)), clamped to the last cell"""
    c = int((v - lo) * size // (hi - lo))
    return max(0, min(size - 1, c))


def row(v, lo, hi, size):
    """floor((hi - v) * size / (hi - lo)), clamped to the last row (row 0 is the top)"""
    return max(0, min(size - 1, int((hi - v) * size // (hi - lo))))


def render(xs, ys, names, W=60, H=20, title=None):
    xa, ya = axis(xs, 6), axis([v for col in ys for v in col], 5)
    xlo, xhi, _, xm, xe, xk0, xk1 = xa
    ylo, yhi, _, ym, ye, yk0, yk1 = ya
    grid = [[" "] * W for _ in range(H)]
    for s, col in enumerate(ys):
        for x, y in zip(xs, col):
            grid[row(y, ylo, yhi, H)][cell(x, xlo, xhi, W)] = GLYPHS[s]
    ylabels = {}
    for k in range(yk0, yk1 + 1):
        v = k * ya[2]
        ylabels[row(v, ylo, yhi, H)] = label(k * ym, ye)
    g = max(len(t) for t in ylabels.values())
    out = []
    if title is not None:
        out.append(" " * (g + 2) + " " * max(0, (W - len(title)) // 2) + title)
    for r in range(H):
        out.append(ylabels.get(r, "").rjust(g) + " |" + "".join(grid[r]))
    out.append(" " * g + " +" + "-" * W)
    line = [" "] * W
    prev_end = -2
    for k in range(xk0, xk1 + 1):
        t = label(k * xm, xe)
        col = cell(k * xa[2], xlo, xhi, W)
        start = max(0, min(W - len(t), col - len(t) // 2))
        if start < prev_end + 1 or len(t) > W:
            continue
        line[start:start + len(t)] = list(t)
        prev_end = start + len(t)
    out.append(" " * (g + 2) + "".join(line))
    out.append("  ".join("%s %s" % (GLYPHS[i], n) for i, n in enumerate(names)))
    return "\n".join(l.rstrip() for l in out) + "\n"


HAND = [
    ("x,y\n0,0\n1,1\n2,2\n", ["--x", "x", "--y", "y", "--size", "10x5"],
     "2.0 |         *\n1.5 |\n1.0 |     *\n0.5 |\n0.0 |*\n    +----------\n     0.0 1.0\n* y\n"),
    ("x,y1,y2\n0,0,2\n1,1,1\n2,2,0\n", ["--x", "1", "--y", "y1,y2", "--size", "10x5", "--title", "T"],
     "         T\n2.0 |+        *\n1.5 |\n1.0 |     +\n0.5 |\n0.0 |*        +\n    +----------\n     0.0 1.0\n* y1  + y2\n"),
    ("a,b\n5,3\n5,3\n", ["--x", "a", "--y", "b", "--size", "10x5"],                  # constant: widened by 1 each way
     "4.0 |\n3.5 |\n3.0 |     *\n2.5 |\n2.0 |\n    +----------\n     4.0 5.0\n* b\n"),
]


def plot(exe, args, data):
    return subprocess.run([exe] + args, input=data.encode(), capture_output=True)


def dec(x):
    d = 0
    while (x * 10 ** d).denominator != 1:
        d += 1
    n = int(x * 10 ** d)
    return label(n, -d) if d else str(n)


def gate(exe):
    bad = []
    for data, args, want in HAND:
        p = plot(exe, args, data)
        if p.returncode != 0 or p.stdout.decode() != want:
            bad.append("hand %r: got\n%s\nwant\n%s" % (args, p.stdout.decode(), want))
    rng = random.Random(20261110)
    for i in range(200):
        n = rng.randint(1, 40)
        k = rng.randint(1, 5)
        scale = rng.choice([Fraction(1, 100), Fraction(1), Fraction(250)])
        xs = [Fraction(rng.randint(-300, 300), rng.choice([1, 10, 100])) * scale for _ in range(n)]
        ys = [[Fraction(rng.randint(-300, 300), rng.choice([1, 10, 100])) * scale for _ in range(n)] for _ in range(k)]
        W, H = rng.randint(10, 80), rng.randint(5, 30)
        title = rng.choice([None, "t", " ", "A longer title here", "x" * 90, "y" * 200])
        names = ["s%d" % j for j in range(k)]
        nl = rng.choice(["\n", "\r\n"])
        data = "t," + ",".join(names) + nl + nl.join(dec(xs[r]) + "," + ",".join(dec(ys[j][r]) for j in range(k)) for r in range(n)) + rng.choice(["", nl])
        numeric = rng.random() < 0.3                                      # the columns by number, the last one included
        args = (["--x", "1", "--y", ",".join(str(j + 2) for j in range(k))] if numeric else ["--x", "t", "--y", ",".join(names)]) + ["--size", "%dx%d" % (W, H)] + (["--title", title] if title is not None else [])
        p = plot(exe, args, data)
        want = render(xs, ys, names, W, H, title)
        if p.returncode != 0 or p.stdout.decode() != want:
            bad.append("random %d (%d points, %d series, %dx%d): exit %d\n%s\nwant\n%s" % (i, n, k, W, H, p.returncode, p.stdout.decode()[:400], want[:400]))
            if len(bad) > 2:
                break
    traps = [([Fraction(0), Fraction(1)], [[Fraction(29, 100), Fraction(34, 100)]]),     # 0.29 * 100 = 28.999999999999996: the axis starts at 0.29
             ([Fraction(0), Fraction(1)], [[Fraction(2, 100), Fraction(7, 100)]]),       # 0.07 * 100 = 7.000000000000001: the axis ends at 0.07
             ([Fraction(29, 100), Fraction(34, 100)], [[Fraction(0), Fraction(1)]]),
             ([Fraction(2, 100), Fraction(7, 100)], [[Fraction(0), Fraction(1)]])]
    for xs, ys in traps:
        data = "x,y\n" + "".join("%s,%s\n" % (dec(xs[r]), dec(ys[0][r])) for r in range(2))
        p = plot(exe, ["--x", "x", "--y", "y", "--size", "20x8"], data)
        want = render(xs, ys, ["y"], 20, 8)
        if p.returncode != 0 or p.stdout.decode() != want:
            bad.append("trap %r %r:\n%s\nwant\n%s" % (xs, ys, p.stdout.decode(), want))
    p = plot(exe, ["--x", "x", "--y", "y", "--title", "t" * 200], "x,y\n1,2\n3,4\n")
    if p.returncode != 0:
        bad.append("a title of 200 bytes refused")
    ok = "x,y\n1,2\n3,4\n"
    refusals = [
        (["--x", "x", "--y", "y"], 'x,y\n1,"2"\n3,4\n', "plot.csv-quote"),
        (["--x", "x", "--y", "y"], "x,y\n1,a\n3,4\n", "plot.not-numeric"),
        (["--x", "x", "--y", "y"], "x,y\n1\n3,4\n", "plot.csv-shape"),
        (["--x", "x", "--y", "y"], "x,y\n", "plot.empty"),
        (["--x", "x", "--y", "y"], "", "plot.empty"),
        (["--x", "q", "--y", "y"], ok, "plot.column-missing"),
        (["--x", "x", "--y", "q"], ok, "plot.column-missing"),
        (["--x", "9", "--y", "y"], ok, "plot.column-missing"),
        (["--x", "x", "--y", "y,y,y,y,y,y"], ok, "plot.too-many-series"),
        (["--x", "x", "--y", "y", "--size", "9x20"], ok, "plot.size-invalid"),
        (["--x", "x", "--y", "y", "--size", "201x20"], ok, "plot.size-invalid"),
        (["--x", "x", "--y", "y", "--size", "60x4"], ok, "plot.size-invalid"),
        (["--x", "x", "--y", "y", "--size", "60x61"], ok, "plot.size-invalid"),
        (["--x", "x", "--y", "y", "--size", "60"], ok, "plot.size-invalid"),
        (["--x", "x", "--y", "y", "--term", "png"], ok, "plot.usage"),
        (["--y", "y"], ok, "plot.usage"),
        (["--x", "x"], ok, "plot.usage"),
        (["--x", "x", "--y", "y", "--nope"], ok, "plot.usage"),
        (["--x", "x", "--y", "y", "--title"], ok, "plot.usage"),
        (["--x", "x", "--y", "y"], "x,y\n" + "1,2\n" * 5001, "plot.too-many-points"),
        (["--x", "x", "--y", "y"], "x,y\n1e300,1\n-1e300,2\n", "plot.range-invalid"),
        (["--x", "x", "--y", "y"], "x,y\n100000000000000,1\n100000000000001,2\n", "plot.range-invalid"),         # 1e14 wide a range only 1 wide
        (["--x", "x", "--y", "y"], "x,y\n2000000000000000,1\n3000000000000000,2\n", "plot.range-invalid"),     # beyond 1e15 of zero but not narrow
        (["--x", "0", "--y", "y"], ok, "plot.column-missing"),
        (["--x", "3", "--y", "y"], ok, "plot.column-missing"),
        (["--x", "x", "--y", "y", "--title", "t" * 201], ok, "plot.usage"),
    ]
    for args, data, rule in refusals:
        p = plot(exe, args, data)
        if p.returncode != 2 or p.stdout or ('"%s"' % rule).encode() not in p.stderr:
            bad.append("refusal %s %r: exit %d, stderr %r" % (rule, args, p.returncode, p.stderr[:100]))
    for data, rule, line in (("x,y\n1,2\n3,4\n5,a\n", "plot.not-numeric", 4), ("x,y\n1,2\n3\n", "plot.csv-shape", 3), ("x,y\r\n1,b\r\n", "plot.not-numeric", 2)):
        p = plot(exe, ["--x", "x", "--y", "y"], data)
        if ('"line":%d}' % line).encode() not in p.stderr or ('"%s"' % rule).encode() not in p.stderr:
            bad.append("line of %s: %r" % (rule, p.stderr[:160]))
    p = plot(exe, ["--x", "x", "--y", "y"], "x,y\r\n1,2\r\n3,4\r\n")
    if p.returncode != 0:
        bad.append("CRLF table refused: %r" % p.stderr[:100])
    # 5,000 rows are accepted
    p = plot(exe, ["--x", "x", "--y", "y"], "x,y\n" + "".join("%d,%d\n" % (i, i * 2) for i in range(5000)))
    if p.returncode != 0:
        bad.append("5000 rows refused: %r" % p.stderr[:100])
    pieces = ["", "\n", "x,y\n", "x,y\r\n1,2\r\n", ",", ",,\n", "1,2\n", "a\n", "\x00", "x,y\n1,2", "9" * 40 + ",1\n", "1e5,1e5\n", "-0,0\n", "é,y\n", "x,x\n1,1\n"]
    for _ in range(200):
        data = "".join(rng.choice(pieces) for _ in range(rng.randint(0, 6)))
        args = rng.choice([["--x", "x", "--y", "y"], ["--x", "1", "--y", "2"], ["--x", "x", "--y", "x,y"], ["--x", "y", "--y", "y", "--size", "10x5"]])
        p = plot(exe, args, data)
        if p.returncode not in (0, 2):
            bad.append("garbage %r %r: exit %d" % (args, data[:40], p.returncode))
    return bad


MUTANTS = [
    ("lib/plot/dumb.cho", "(v - lo) * float_of(size) / (hi - lo) + 1.0e-9", "(v - lo) * float_of(size) / (hi - lo)"),
    ("lib/plot/dumb.cho", "(hi - v) * float_of(size) / (hi - lo) + 1.0e-9", "(hi - v) * float_of(size) / (hi - lo)"),
    ("lib/plot/dumb.cho", "(hi - v) * float_of(size) / (hi - lo)", "(v - lo) * float_of(size) / (hi - lo)"),
    ("lib/plot/dumb.cho", "if c > size - 1 {\n        return size - 1;", "if c > size - 2 {\n        return size - 2;"),
    ("lib/plot/dumb.cho", "if c < 0 {\n        return 0;", "if c < 1 {\n        return 1;"),
    ("lib/plot/dumb.cho", "while n > 0 && int_of(bs[n - 1]) == ' ' {", "while n > 1 && int_of(bs[n - 1]) == ' ' {"),
    ("lib/plot/dumb.cho", "if lo == hi {\n        lo = lo - 1.0;\n        hi = hi + 1.0;", "if lo == hi {\n        lo = lo - 2.0;\n        hi = hi + 2.0;"),
    ("lib/plot/dumb.cho", "if far > 1.0e15 || span < 1.0e-12 || far / span > 1.0e12 {", "if far > 1.0e15 || span < 1.0e-12 {"),
    ("lib/plot/dumb.cho", "if far > 1.0e15 || span < 1.0e-12 || far / span > 1.0e12 {", "if far > 1.0e16 || span < 1.0e-12 || far / span > 1.0e12 {"),
    ("lib/plot/dumb.cho", "return (ticks.value(k0, m, e), ticks.value(k1, m, e), m, e, k0, k1);", "return (ticks.value(k0 + 1, m, e), ticks.value(k1, m, e), m, e, k0, k1);"),
    ("lib/plot/dumb.cho", "let (xlo2, xhi2, xm, xe, xk0, xk1) = axis(xl0, xh0, 6);", "let (xlo2, xhi2, xm, xe, xk0, xk1) = axis(xl0, xh0, 5);"),
    ("lib/plot/dumb.cho", "let (ylo2, yhi2, ym, ye, yk0, yk1) = axis(yl0, yh0, 5);", "let (ylo2, yhi2, ym, ye, yk0, yk1) = axis(yl0, yh0, 6);"),
    ("lib/plot/dumb.cho", "let glyphs = \"*+xo#\";", "let glyphs = \"*+xo@\";"),
    ("lib/plot/dumb.cho", "grid[row * w + col] = glyphs[j];", "grid[row * w + col] = glyphs[0];"),
    ("lib/plot/dumb.cho", "var pad = (w - len(title)) / 2;", "var pad = (w - len(title)) / 3;"),
    ("lib/plot/dumb.cho", "var line = spaces(heap, buffer.empty(heap, 64), g + 2);\n                var pad", "var line = spaces(heap, buffer.empty(heap, 64), g + 1);\n                var pad"),
    ("lib/plot/dumb.cho", "if yrow[t] == row {\n                        which = t;", "if yrow[t] == row && which < 0 {\n                        which = t;"),
    ("lib/plot/dumb.cho", "line = spaces(heap, line, g - lw);", "line = spaces(heap, line, g - lw + 1);"),
    ("lib/plot/dumb.cho", "line = buffer.push(heap, line, byte_of('+'));", "line = buffer.push(heap, line, byte_of('|'));"),
    ("lib/plot/dumb.cho", "var start = col - ln / 2;", "var start = col - ln / 2 + 1;"),
    ("lib/plot/dumb.cho", "if start > w - ln {\n                start = w - ln;", "if start > w - ln + 1 {\n                start = w - ln + 1;"),
    ("lib/plot/dumb.cho", "if ln <= w && start >= prev_end + 1 {", "if ln <= w && start >= prev_end {"),
    ("lib/plot/dumb.cho", "if ln <= w && start >= prev_end + 1 {", "if ln <= w && start >= prev_end + 2 {"),
    ("lib/plot/dumb.cho", "prev_end = start + ln;", "prev_end = start + ln + 1;"),
    ("lib/plot/dumb.cho", "line = buffer.append(heap, line, \"  \");", "line = buffer.append(heap, line, \" \");"),
    ("lib/plot/dumb.cho", "if code == 0 && n > 5000 {", "if code == 0 && n > 4999 {"),
    ("lib/plot/dumb.cho", "if ycount > 5 {", "if ycount > 4 {"),
    ("lib/plot/dumb.cho", "line = row + 2;", "line = row + 1;"),
    ("lib/plot/csv.cho", "if i > from && int_of(text[i - 1]) == 13 {", "if i > from && int_of(text[i - 1]) == 14 {"),
    ("lib/plot/csv.cho", "if v >= 1 && v <= n {", "if v >= 1 && v < n {"),
    # not listed, equivalent: `v >= 1` to `v >= 0` in csv.column (the spec 0 would give column -1, which is also what "not there" answers)
    ("lib/plot/ticks.cho", "let a = over(lo, e) / unit + 1.0e-9;", "let a = over(lo, e) / unit;"),
    ("lib/plot/ticks.cho", "let b = over(hi, e) / unit - 1.0e-9;", "let b = over(hi, e) / unit;"),
    ("lib/plot/ticks.cho", "if float_of(first) > a {\n        first = first - 1;", "if float_of(first) > a {\n        first = first - 2;"),
    ("lib/plot/ticks.cho", "if float_of(last) < b {\n        last = last + 1;", "if float_of(last) < b {\n        last = last + 2;"),
    ("lib/plot/ticks.cho", "    return n / pow10(0 - e);", "    return n * pow10(0 - e);"),
    ("tools/plot/main.cho", "if len(value) > 200 {", "if len(value) > 199 {"),
    ("tools/plot/main.cho", "if sw < 10 || sw > 200 || sh < 5 || sh > 60 {", "if sw < 11 || sw > 200 || sh < 5 || sh > 60 {"),
    ("tools/plot/main.cho", "if sw < 10 || sw > 200 || sh < 5 || sh > 60 {", "if sw < 10 || sw > 201 || sh < 5 || sh > 60 {"),
    ("tools/plot/main.cho", "if sw < 10 || sw > 200 || sh < 5 || sh > 60 {", "if sw < 10 || sw > 200 || sh < 6 || sh > 60 {"),
    ("tools/plot/main.cho", "if sw < 10 || sw > 200 || sh < 5 || sh > 60 {", "if sw < 10 || sw > 200 || sh < 5 || sh > 61 {"),
]


def mutants():
    cancho = os.environ["CANCHO"]
    killed = survivors = 0
    srcs = ["lib/plot/num.cho", "lib/plot/ticks.cho", "lib/plot/csv.cho", "lib/plot/dumb.cho", "tools/plot/main.cho"]
    for path, old, new in MUTANTS:
        with tempfile.TemporaryDirectory() as d:
            for f in srcs:
                src = open(os.path.join(ROOT, f)).read()
                if f == path:
                    assert old in src, "mutant text not found: %s" % old
                    src = src.replace(old, new, 1)
                os.makedirs(os.path.join(d, os.path.dirname(f)), exist_ok=True)
                open(os.path.join(d, f), "w").write(src)
            exe = os.path.join(d, "plot")
            p = subprocess.run([cancho, "build"] + [d + "/" + f for f in srcs] + ["--std", "-o", exe], capture_output=True)
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
    print("check_dumb: ok (%d hand charts, 200 random charts, 26 refusals, 200 garbage inputs)" % len(HAND))
    if "--mutants" in sys.argv:
        mutants()
