"""Makes the landing page (site/index.html) and its gallery from the binary: every chart on the page is what `build/plot` writes now.

    PLOT=build/plot python3 scripts/make_gallery.py [OUT]       # OUT defaults to site/; it writes OUT/data/*.csv (except holdout.csv, a real series), OUT/gallery/*, OUT/index.html

scripts/check_site.py makes the page again in a temporary directory and requires it to be byte for byte the committed one, so the page cannot go stale.
"""
import html
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLOT = os.environ.get("PLOT", os.path.join(ROOT, "build", "plot"))
SITE = os.path.join(ROOT, "site")


class Lcg:
    """integers only, so the data are the same on every machine"""
    def __init__(self, seed):
        self.s = seed

    def next(self, n):
        self.s = (self.s * 1103515245 + 12345) % 2147483648
        return (self.s >> 8) % n


def money(v):
    return "%.2f" % (v / 100.0)


def datasets():
    """name -> csv text"""
    r = Lcg(7)
    net = ["day,control,treated"]
    for day in range(60):
        base = 10000 + 150 * day
        c = base + r.next(1500) - 750
        t = base + r.next(1500) - 750 + (1400 if day >= 30 else 0) + (35 * (day - 30) if day >= 30 else 0)
        net.append("%d,%s,%s" % (day, money(c), money(t)))
    cal = ["forecast,realised"]
    for i in range(40):
        f = 50 + r.next(900)
        cal.append("%s,%s" % (money(f * 10), money(int(f * 9.2) + r.next(600) - 300)))
    est = ["week,estimate,floor"]
    for w in range(1, 13):
        est.append("%d,%s,%s" % (w, money(110 + 12 * w - (w * w) // 3 + r.next(25) - 12), money(125)))
    five = ["x,a,b,c,d,e"]
    for x in range(20):
        five.append("%d,%d,%d,%d,%d,%d" % (x, x, 2 * x - 5, (x * x) // 8, 20 - x, 8 + (3 * x) % 11))
    imp = "feature,importance,std\nx1,0.391,0.026\nx2,0.118,0.019\nx3,0.052,0.011\ng,0.007,0.004\n"
    folds = "fold,roc_auc,accuracy,f1\n1,0.914,0.800,0.810\n2,0.963,0.907,0.921\n3,0.947,0.853,0.874\n4,0.942,0.867,0.872\n"
    forest = "test,difference,half\nx1,-0.057,0.062\nx2,0.012,0.041\nx3,0.104,0.055\nx4,-0.021,0.030\n"
    return {"net.csv": "\n".join(net) + "\n", "calibration.csv": "\n".join(cal) + "\n", "estimate.csv": "\n".join(est) + "\n", "five.csv": "\n".join(five) + "\n", "importance.csv": imp, "folds.csv": folds, "forest.csv": forest}


# (id, title, text under it, data file, arguments, output kind)
GALLERY = [
    ("lines", "Two series, a title, and a marker where the service starts",
     "The net margin of the control and of the treated hotels per day. <code>--vline 30</code> draws the dashed marker; both axes widen to the next 1-2-5 tick.",
     "net.csv", ["--x", "day", "--y", "control,treated", "--with", "lines", "--term", "svg", "--title", "Net margin per hotel-day", "--vline", "30"], "svg"),
    ("diagonal", "Forecast against realised, with the diagonal",
     "Points, and <code>--diag</code> for the line where the forecast is exact. The range is the same on both axes, so the diagonal runs corner to corner.",
     "calibration.csv", ["--x", "forecast", "--y", "realised", "--term", "svg", "--title", "Calibration", "--diag"], "svg"),
    ("band", "A band and a floor",
     "An estimate against its floor. <code>--band 125,150</code> shades the target, <code>--hline 125</code> marks the floor; the y range grows to hold them.",
     "estimate.csv", ["--x", "week", "--y", "estimate", "--with", "lines", "--term", "svg", "--title", "Weekly estimate", "--band", "125,150", "--hline", "125"], "svg"),
    ("five", "Five series",
     "The most there is: five series, five colours. The colours are CSS variables (<code>--series-1</code> to <code>--series-5</code>), so a page themes them, as this one does for dark mode.",
     "five.csv", ["--x", "x", "--y", "a,b,c,d,e", "--with", "lines", "--term", "svg", "--size", "640x360"], "svg"),
    ("real", "A real series: 302 days of a holdout's margin",
     "The daily margin per hotel of a holdout in a simulated metasearch-bidding run (400 hotels, 330 days). Points, as they are; 302 rows, one second of work.",
     "holdout.csv", ["--x", "day", "--y", "margin", "--term", "svg", "--title", "Holdout margin per hotel-day"], "svg"),
    ("bars", "Bars with error bars: permutation importance",
     "The shape of what <code>ml importance</code> prints: a category on x (the cell's text), the importance as the bar, its standard deviation as the error bar (<code>--yerr std</code>). The y range includes 0.",
     "importance.csv", ["--x", "feature", "--y", "importance", "--with", "bars", "--yerr", "std", "--term", "svg", "--title", "Permutation importance (roc_auc)"], "svg"),
    ("grouped", "Grouped bars: three metrics in four folds",
     "Several series are grouped side by side in the order of <code>--y</code>: the metrics of each fold of <code>ml cv</code>.",
     "folds.csv", ["--x", "fold", "--y", "roc_auc,accuracy,f1", "--with", "bars", "--term", "svg", "--title", "Cross-validation by fold"], "svg"),
    ("forest", "Intervals: an estimate and its half-width, with the zero line",
     "Points with <code>--yerr</code> and <code>--hline 0</code>: the shape of the intervals <code>stats test</code> prints (an estimate, and low and high, here as a half-width). <code>--categories</code> puts the names of the tests on x.",
     "forest.csv", ["--x", "test", "--y", "difference", "--yerr", "half", "--categories", "--term", "svg", "--title", "Difference of means, 95% intervals", "--hline", "0"], "svg"),
    ("jsonimp", "Straight from ml importance: its JSON, no table in between",
     "The document <code>ml importance</code> printed on a 300-row table, read by path: <code>--json data.permutation.columns</code> is the array of objects, <code>--x column --y importance --yerr std</code> pick the fields. The same command works on the output of the tool.",
     "ml-importance.json", ["--json", "data.permutation.columns", "--x", "column", "--y", "importance", "--yerr", "std", "--with", "bars", "--term", "svg", "--title", "ml importance (permutation, roc_auc)"], "svg"),
    ("jsonforest", "An interval plot from stats test, asymmetric intervals included",
     "The document <code>stats test t2</code> printed: a row for each tested column, the estimate in <code>interval.estimate</code> and the ends of the 95% interval in <code>interval.low</code> and <code>interval.high</code> (<code>--ylo</code>, <code>--yhi</code>); nested fields are dotted paths, <code>--categories</code> puts the column names on x.",
     "stats-t2.json", ["--json", "data.tests", "--x", "column", "--y", "interval.estimate", "--ylo", "interval.low", "--yhi", "interval.high", "--categories", "--hline", "0", "--term", "svg", "--title", "stats test t2: difference of means by group"], "svg"),
    ("jsoncv", "Cross-validation folds from ml cv",
     "The document <code>ml cv</code> printed, one row for each fold in <code>data.results</code>; two metrics are nested fields (<code>metrics.roc_auc</code>, <code>metrics.accuracy</code>), the fold number is the category.",
     "ml-cv.json", ["--json", "data.results", "--x", "fold", "--y", "metrics.roc_auc,metrics.accuracy", "--with", "bars", "--term", "svg", "--title", "ml cv: metrics by fold"], "svg"),
    ("barstext", "Bars as text",
     "The same importance chart with <code>--term dumb</code>: each category's slot is shared by its bars, and the whisker is a <code>|</code> at the middle of the bar.",
     "importance.csv", ["--x", "feature", "--y", "importance", "--with", "bars", "--yerr", "std", "--term", "dumb", "--size", "56x12"], "txt"),
    ("text", "The same chart as text",
     "<code>--term dumb</code> draws in characters: for a terminal, a log, or a test. The same table as the first chart, lines joined with integers only.",
     "net.csv", ["--x", "day", "--y", "control,treated", "--with", "lines", "--term", "dumb", "--size", "72x16", "--vline", "30"], "txt"),
]
TICKS = [["ticks", "0", "1", "5"], ["ticks", "-3", "7", "4"], ["ticks", "0.001", "0.0073"], ["ticks", "0", "1000000"]]


def run(args, data=None):
    p = subprocess.run([PLOT] + args, input=data, capture_output=True)
    assert p.returncode == 0, "plot %s exited %d: %s" % (" ".join(args), p.returncode, p.stderr.decode()[:200])
    return p.stdout.decode()


def shell(args):
    """the command line as it is shown"""
    q = lambda a: a if all(c.isalnum() or c in "-,._" for c in a) else "'%s'" % a if "'" not in a else '"%s"' % a
    return "plot " + " ".join(q(a) for a in args)


def build(out):
    os.makedirs(os.path.join(out, "data"), exist_ok=True)
    os.makedirs(os.path.join(out, "gallery"), exist_ok=True)
    for name, text in datasets().items():
        open(os.path.join(out, "data", name), "w").write(text)
    if os.path.abspath(out) != os.path.abspath(SITE):
        for kept in ("holdout.csv", "ml-importance.json", "stats-t2.json", "ml-cv.json"):      # real data, not made here
            shutil.copy(os.path.join(SITE, "data", kept), os.path.join(out, "data", kept))
    cards = []
    for gid, title, text, data, args, kind in GALLERY:
        table = open(os.path.join(out, "data", data), "rb").read()
        result = run(args, table)
        open(os.path.join(out, "gallery", gid + "." + kind), "w").write(result)
        cmd = shell(args) + " < " + data
        if kind == "svg":
            body = '<div class="chart">' + result.split("\n", 0)[0] + "</div>"
        else:
            body = "<pre>" + html.escape(result, quote=False) + "</pre>"
        cards.append('<figure id="%s">\n<h3>%s</h3>\n<p>%s</p>\n%s\n<p class="cmd"><code>%s</code> <a href="data/%s">the table</a>%s</p>\n</figure>' % (
            gid, html.escape(title, quote=False), text, body, html.escape(cmd, quote=False), data,
            ' <a href="gallery/%s.svg">the svg</a>' % gid if kind == "svg" else ' <a href="gallery/%s.txt">the text</a>' % gid))
    ticks = []
    for a in TICKS:
        ticks.append("$ %s\n%s" % (shell(a), run(a)))
    page = PAGE.replace("@GALLERY@", "\n".join(cards)).replace("@TICKS@", html.escape("\n".join(ticks), quote=False))
    open(os.path.join(out, "index.html"), "w").write(page)


PAGE = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>cancho-plot</title>
<meta name="description" content="Plots as an agent-first command line, written in cancho: SVG and text charts from CSV on standard input."/>
<style>
:root{--bg:#ffffff;--fg:#1f2328;--muted:#59636e;--line:#d1d9e0;--card:#f6f8fa;--accent:#0550ae;--series-1:#0550ae;--series-2:#bc4c00;--series-3:#1a7f37;--series-4:#8250df;--series-5:#cf222e;--band:#0550ae}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#121212;--fg:#e6edf3;--muted:#9198a1;--line:#30363d;--card:#1b1f24;--accent:#79c0ff;--series-1:#79c0ff;--series-2:#ffa657;--series-3:#56d364;--series-4:#d2a8ff;--series-5:#ff7b72;--band:#79c0ff}}
:root[data-theme="dark"]{--bg:#121212;--fg:#e6edf3;--muted:#9198a1;--line:#30363d;--card:#1b1f24;--accent:#79c0ff;--series-1:#79c0ff;--series-2:#ffa657;--series-3:#56d364;--series-4:#d2a8ff;--series-5:#ff7b72;--band:#79c0ff}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:70rem;margin:0 auto;padding:0 16px 4rem}
header{padding:3.5rem 0 1.5rem}
h1{font-size:2.4rem;margin:0 0 .25rem;letter-spacing:-.02em}
h2{font-size:1.4rem;margin:3rem 0 .5rem}
h3{font-size:1.05rem;margin:0 0 .25rem}
p{margin:.4rem 0}
.lead{font-size:1.2rem;color:var(--muted);max-width:44rem}
a{color:var(--accent)}
code,pre{font:.9rem/1.45 ui-monospace,SFMono-Regular,Menlo,monospace}
pre{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:12px 14px;overflow-x:auto;margin:.5rem 0}
code{background:var(--card);border-radius:4px;padding:.05em .3em}
pre code{background:none;padding:0}
.gallery{display:grid;grid-template-columns:1fr;gap:20px}
@media (min-width:60rem){.gallery{grid-template-columns:1fr 1fr}}
figure{margin:0;border:1px solid var(--line);border-radius:10px;padding:14px 16px;background:var(--bg);min-width:0}
figure .chart svg{width:100%;height:auto;display:block;color:var(--fg)}
figure .cmd{font-size:.85rem;color:var(--muted)}
figure .cmd code{word-break:break-word}
.facts{display:grid;grid-template-columns:repeat(auto-fit,minmax(15rem,1fr));gap:12px;margin:1rem 0}
.facts div{border:1px solid var(--line);border-radius:8px;padding:10px 12px;background:var(--card)}
.facts strong{display:block}
footer{border-top:1px solid var(--line);margin-top:3rem;padding-top:1rem;color:var(--muted);font-size:.9rem}
</style>
</head>
<body>
<main>
<header>
<h1>cancho-plot</h1>
<p class="lead">Plots as a command line an agent can read. A table goes in on standard input; an SVG, or the same chart as text, comes out. Written in <a href="https://github.com/alpibrusl/cancho">cancho</a>, in the family of <code>table</code>, <code>ml</code> and <code>stats</code>.</p>
<pre><code>table --format csv ... | plot --x day --y net,margin --with lines --term svg --title "Net margin" &gt; net.svg
table --format csv ... | plot --x day --y net --term dumb          # the same chart as text</code></pre>
</header>

<section class="facts">
<div><strong>Byte-stable</strong>The same table and flags give the same bytes: no clock, no random, no ids. Labels are written from integers, never from float formatting.</div>
<div><strong>Errors are data</strong>A refusal is one JSON line on standard error with a rule tag such as <code>plot.not-numeric</code>, and exit status 2. No input reaches a crash.</div>
<div><strong>Little authority</strong>It reads standard input and writes standard output. No file, no network, no clock: the compiler checks that the program can do nothing else.</div>
<div><strong>Tested against a second implementation</strong>Every chart in the gates is also drawn by an independent program in exact arithmetic, and mutants of the source must make a gate fail.</div>
</section>

<h2>Gallery</h2>
<p>Everything below is what the binary writes, made by <code>scripts/make_gallery.py</code> and checked by <code>scripts/check_site.py</code>: if the tool changes, this page fails its check until it is made again.</p>
<section class="gallery">
@GALLERY@
</section>

<h2>Ticks</h2>
<p>The axis rule on its own: the 1-2-5 ticks of a range, written exactly.</p>
<pre><code>@TICKS@</code></pre>

<h2>What is there, and what is not</h2>
<p>Built: points and lines, bars with text categories (grouped for several series), error bars (<code>--yerr</code>), up to five series, a title, markers (<code>--vline</code>, <code>--hline</code>), bands (<code>--band</code>) and the diagonal (<code>--diag</code>), as SVG or as text. Intervals by their ends (<code>--ylo</code>, <code>--yhi</code>), text categories on points (<code>--categories</code>), and the JSON of <code>stats</code> and <code>ml</code> read directly (<code>--json PATH</code>). Not built yet: histograms, box plots, heatmaps, ROC and other curves, a gnuplot-like script, PNG. The plan for the statistics and machine-learning charts is section 19 of the design. The design, with what was measured and what was only chosen, is <a href="https://github.com/alpibrusl/cancho-plot/blob/main/docs/design.md">docs/design.md</a>.</p>

<footer>EUPL-1.2, copyright Alpibru S.L. &#183; <a href="https://github.com/alpibrusl/cancho-plot">github.com/alpibrusl/cancho-plot</a></footer>
</main>
</body>
</html>
'''


if __name__ == "__main__":
    build(os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else SITE)
    print("made", sys.argv[1] if len(sys.argv) > 1 else SITE)
