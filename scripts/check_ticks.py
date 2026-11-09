"""The gate of `plot ticks` (docs/design.md section 7, gate 1).

An independent implementation of the same rule in exact arithmetic (fractions) judges the program on a table of hand-checked cases and on 600 random ranges;
every refusal has an input; garbage arguments never end in anything but 0 or 2; and every mutant of the library (--mutants, needs CANCHO) must fail the gate.

    PLOT=build/plot python3 scripts/check_ticks.py [--mutants]
"""
import os
import random
import subprocess
import sys
import tempfile
from fractions import Fraction

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLOT = os.environ.get("PLOT", os.path.join(ROOT, "build", "plot"))


def oracle(lo, hi, n):
    """The ticks of [lo, hi] aimed at n intervals, as the program's labels. lo, hi: strings of decimals."""
    lo, hi = Fraction(lo), Fraction(hi)
    raw = (hi - lo) / n
    e = 0
    f = raw
    while f >= 10:
        f /= 10
        e += 1
    while f < 1:
        f *= 10
        e -= 1
    if f <= Fraction(3, 2):
        m = 1
    elif f <= 3:
        m = 2
    elif f <= 7:
        m = 5
    else:
        m, e = 1, e + 1
    unit = Fraction(m) * Fraction(10) ** e
    k = -((-lo) // unit)                     # ceil
    labels = []
    while k * unit <= hi:
        labels.append(label(k * m, e))
        k += 1
    return labels


def label(n, e):
    sign = "-" if n < 0 else ""
    n = abs(n)
    if e >= 0:
        return sign + (str(n) + "0" * e if n else "0")
    d = -e
    s = str(n).rjust(d + 1, "0")
    return sign + s[:-d] + "." + s[-d:]


HAND = [                                  # worked out by hand from the rule (docs/design.md section 5)
    ("0", "10", 5, "0 2 4 6 8 10"),       # raw 2 -> f 2 -> step 2
    ("0", "1", 5, "0.0 0.2 0.4 0.6 0.8 1.0"),
    ("-3", "7", 4, "-2 0 2 4 6"),         # raw 2.5 -> step 2
    ("0", "100", 5, "0 20 40 60 80 100"),
    ("0", "7", 3, "0 2 4 6"),             # raw 2.33 -> step 2
    ("0", "10", 3, "0 5 10"),             # raw 3.33 -> step 5
    ("0", "10", 1, "0 10"),               # raw 10 -> f 1 of the next power
    ("0", "9", 1, "0"),            # raw 9 -> f 9 -> step 10: only 0 lies in [0, 9]
    ("-1", "1", 4, "-1.0 -0.5 0.0 0.5 1.0"),
    ("0", "0.3", 6, "0.00 0.05 0.10 0.15 0.20 0.25 0.30"),
    ("0", "9", 6, "0 1 2 3 4 5 6 7 8 9"),   # raw 1.5: a tie goes to the smaller step, 1
    ("0.07", "0.12", 5, "0.07 0.08 0.09 0.10 0.11 0.12"),     # 0.07 * 100 = 7.000000000000001 in a float: the first tick is still 7
    ("0.24", "0.29", 5, "0.24 0.25 0.26 0.27 0.28 0.29"),     # 0.29 * 100 = 28.999999999999996: the last tick is still 29
    ("1000", "1003", 3, "1000 1001 1002 1003"),
    ("0.001", "0.0073", 5, "0.001 0.002 0.003 0.004 0.005 0.006 0.007"),
]


def ticks(exe, lo, hi, n):
    p = subprocess.run([exe, "ticks", lo, hi, str(n)], capture_output=True)
    return p


def gate(exe):
    bad = []
    for lo, hi, n, want in HAND:
        p = ticks(exe, lo, hi, n)
        got = p.stdout.decode().split()
        if p.returncode != 0 or got != want.split():
            bad.append("hand %s %s %d: %r != %r" % (lo, hi, n, got, want.split()))
    rng = random.Random(20261109)
    for i in range(600):
        scale = rng.choice([Fraction(1, 1000), Fraction(1), Fraction(1000), Fraction(1000000)])
        a = Fraction(rng.randint(-5000, 5000), 10 ** rng.randint(0, 3)) * scale
        b = a + Fraction(rng.randint(1, 20000), 10 ** rng.randint(0, 3)) * scale
        lo, hi, n = dec(a), dec(b), rng.randint(1, 12)
        want = oracle(lo, hi, n)
        p = ticks(exe, lo, hi, n)
        if p.returncode != 0 or p.stdout.decode().split() != want:
            bad.append("random %s %s %d: %r != %r" % (lo, hi, n, p.stdout.decode().split()[:6], want[:6]))
            if len(bad) > 3:
                break
    refusals = [(["ticks", "x", "1"], "plot.not-numeric"), (["ticks", "1", "1"], "plot.range-invalid"), (["ticks", "2", "1"], "plot.range-invalid"),
                (["ticks", "0", "1", "0"], "plot.range-invalid"), (["ticks", "0", "1", "101"], "plot.range-invalid"), (["ticks", "0", "1", "x"], "plot.range-invalid"),
                (["ticks", "0"], "plot.usage"), (["ticks"], "plot.usage"), ([], "plot.usage"), (["nope"], "plot.usage"), (["ticks", "0", "1", "2", "3"], "plot.usage"),
                (["ticks", "nan", "1"], "plot.not-numeric"), (["ticks", "0", "1e999"], "plot.not-numeric"), (["ticks", "-1e300", "1"], "plot.range-invalid"), (["ticks", "0", "1e-13"], "plot.range-invalid"),
                (["ticks", "1e14", "100000000000001"], "plot.range-invalid"), (["ticks", "-1e15", "1e15"], None)]
    for args, rule in refusals:
        p = subprocess.run([exe] + args, capture_output=True)
        if rule is None:                      # the widest range that is accepted
            if p.returncode != 0:
                bad.append("wide range refused: %r" % p.stderr[:80])
        elif p.returncode != 2 or p.stdout or ('"%s"' % rule).encode() not in p.stderr:
            bad.append("refusal %r: exit %d, stderr %r" % (args, p.returncode, p.stderr[:80]))
    pieces = ["", "0", "-1", "1e3", "1e-3", "9" * 30, "1e22", "1e23", "-1e300", "1e300", "0.0000001", "ticks", "--x", "é", "-", "+", ".", "1.", ".5", "1e", "0x10"]
    for _ in range(200):
        args = ["ticks"] + [rng.choice(pieces) for _ in range(rng.randint(0, 4))]
        p = subprocess.run([exe] + args, capture_output=True)
        if p.returncode not in (0, 2):
            bad.append("garbage %r: exit %d" % (args, p.returncode))
    return bad


def dec(x):
    """The shortest decimal text of a fraction whose denominator is a power of ten."""
    d = 0
    while (x * 10 ** d).denominator != 1:
        d += 1
    n = int(x * 10 ** d)
    return label(n, -d) if d else str(n)


MUTANTS = [
    ("lib/plot/ticks.cho", "if f < 1.5 + 1.0e-9 {", "if f < 1.4 + 1.0e-9 {"),
    ("lib/plot/ticks.cho", "if f < 1.5 + 1.0e-9 {", "if f < 1.5 {"),
    ("lib/plot/ticks.cho", "if f < 3.0 + 1.0e-9 {", "if f < 3.5 + 1.0e-9 {"),
    ("lib/plot/ticks.cho", "if f < 7.0 + 1.0e-9 {", "if f < 8.0 + 1.0e-9 {"),
    ("lib/plot/ticks.cho", "return (1, e + 1);", "return (1, e);"),
    ("lib/plot/ticks.cho", "return (5, e);", "return (2, e);"),
    # not listed, equivalent: `f >= 10.0` to `f > 10.0` (a raw step of exactly 10^e gives f = 10, which the last branch turns into (1, e + 1), the same answer as f = 1 at e + 1)
    ("lib/plot/ticks.cho", "let ca = a - 1.0e-9;", "let ca = a;"),
    ("lib/plot/ticks.cho", "let cb = b + 1.0e-9;", "let cb = b;"),
    ("lib/plot/ticks.cho", "first = first + 1;", "first = first + 2;"),
    ("lib/plot/ticks.cho", "last = last - 1;", "last = last - 2;"),
    # not listed, equivalent: the cap of `pow10` at 22 to 21 (the range guard of main.cho keeps every exponent within +-16, so the cap is never reached; it is there so that the function cannot loop on a wrong argument)
    ("lib/plot/ticks.cho", "if n != 0 {\n            var z = 0;", "if n != 5 {\n            var z = 0;"),
    # not listed, equivalent: `digits <= d` to `digits < d` (when they are equal the general path writes the same `0.5`)
    ("lib/plot/ticks.cho", "while pad > frac && pad > 1 {", "while pad >= frac && pad > 1 {"),
    ("lib/plot/ticks.cho", "b = buffer.push(heap, b, byte_of('-'));", "b = buffer.push(heap, b, byte_of('+'));"),
    # not listed, equivalent: `!(lo < hi)` to `lo > hi` (LO equal to HI is then refused by the width guard under the same rule tag; only the message differs)
    ("tools/plot/main.cho", "if n < 1 || n > 100 {", "if n < 0 || n > 100 {"),
    ("tools/plot/main.cho", "if n < 1 || n > 100 {", "if n < 1 || n > 101 {"),
]


def mutants():
    cancho = os.environ["CANCHO"]
    killed = survivors = 0
    for path, old, new in MUTANTS:
        with tempfile.TemporaryDirectory() as d:
            for f in ("lib/plot/num.cho", "lib/plot/ticks.cho", "tools/plot/main.cho"):
                src = open(os.path.join(ROOT, f)).read()
                if f == path:
                    assert old in src, "mutant text not found: %s" % old
                    src = src.replace(old, new, 1)
                os.makedirs(os.path.join(d, os.path.dirname(f)), exist_ok=True)
                open(os.path.join(d, f), "w").write(src)
            exe = os.path.join(d, "plot")
            p = subprocess.run([cancho, "build", d + "/lib/plot/num.cho", d + "/lib/plot/ticks.cho", d + "/tools/plot/main.cho", "--std", "-o", exe], capture_output=True)
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
    print("check_ticks: ok (%d hand cases, 600 random ranges, 17 refusals, 200 garbage argument lists)" % len(HAND))
    if "--mutants" in sys.argv:
        mutants()
