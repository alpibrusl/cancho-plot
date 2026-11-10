# cancho-plot: design

Written 2026-11-09, before any code (`CLAUDE.md`). Every claim is **[measured]** with its command, a **[choice]**, or **[open]**. Slice 1 (ticks) is built: section 10.

## 1. Why

`metasearch-bidding` lost its charts when the Python was removed: the report writes `report.md` and `metrics.json` and says "the charts are not made". The Python drew
`net.svg`, `hold.svg`, `season.svg`, `cal.svg` and others with a 35-line `svg_lines` and embedded them in `report.html`. A plot belongs in a tool the siblings can feed, not in
one client: `table` produces the series, `stats` the intervals, `ml` the curves and calibration, and one binary draws them.

## 2. What exists [measured]

- `cancho-ui` has `Chart { kind: "line"|"bar" }` (`cancho-ui/docs/charts.md`): one series, drawn in the browser by the page's JavaScript from state. It cannot write a file and it
  is not a command line.
- There is no gnuplot on the development machine: `which gnuplot` finds nothing (2026-11-09). So gnuplot cannot be the oracle yet **[open: install and compare]**.
- cancho's `std` has `fmt`, `math` and `buffer`; no SVG module. Float formatting must be byte-stable across platforms **[open: measure `std.fmt`'s output for the shortest round-trip form]**.

## 3. Scope [choice]

First version, what the report needs: lines (several series, shared x), points, bars, a histogram (`--bins`), vertical markers (`--vline`), a diagonal (`--diag`), shaded bands
(`--band lo,hi`), error bars from two columns, titles and axis labels, "nice" ticks, a legend. Output: **SVG** (text) and `--term dumb` (text). Not in scope: PNG or any raster
(needs a rasterizer), 3-D, polar, animation, interactive output.

## 4. Command line [choice]

`plot [FLAGS] < data` reads CSV, TSV or JSON lines (detected from the first line, or `--format`). Columns by name or by 1-based number. Flags: `--x COL`, `--y COL[,COL..]`,
`--with lines|points|bars|steps|hist`, `--title`, `--xlabel`, `--ylabel`, `--xrange a:b`, `--yrange a:b`, `--logx`, `--logy`, `--size WxH`, `--term svg|dumb`, `--vline X`, `--band`.
`plot -c FILE` runs a script of the gnuplot subset: `set title "..."`, `set xrange [a:b]`, `plot "-" using 1:3 with lines title "net", "-" using 1:4 with points` (the data is the
standard input; a path is refused with `plot.file-not-allowed` while the authority is stdin and stdout only). **[open: which subset exactly; start with the flag form and add the
script when the flags are gated]**.

## 5. Output rules [choice]

- Numbers in the SVG are written with at most 2 decimals, rounded half to even, never in exponent form, so the file is byte-stable.
- Colours are CSS custom properties (`var(--series-1)` with a fallback), so a page can theme them; the default palette has contrast of at least 3:1 against white and against
  `#121212` (WCAG 1.4.11) **[open: measure]**.
- Each SVG has `role="img"` and an `aria-label` with the title and the number of points, as `cancho-ui` charts do.
- A series of more than `--max-points` (default 5,000) points is refused with `plot.too-many-points`, not silently thinned.

## 6. Errors [choice]

Rule tags: `plot.usage`, `plot.column-missing`, `plot.not-numeric`, `plot.empty`, `plot.too-many-points`, `plot.range-invalid`, `plot.log-nonpositive`, `plot.file-not-allowed`,
`plot.format-unknown`. Exit status 2; JSON on standard error with `rule`, `message` and `repair`.

## 7. Gates, before the code [choice]

1. **Ticks**: the "nice number" algorithm on 200 ranges against values computed by hand and kept in `tests/golden`; mutants of the step choice and of the rounding must fail.
2. **Dumb terminal**: exact text output for 10 small data sets, kept as files.
3. **SVG**: path data for 6 small charts compared byte for byte; the same input twice gives the same bytes.
4. **Refusals**: every rule tag has an input that triggers it; random bytes and truncated files never panic (`scripts/check_cli.py`).
5. **The report**: `metasearch-bidding`'s `report` calls `plot` for its charts; its test compares the chart's data (the points), not pixels.

## 8. Order [choice]

1. Ticks and scales (library, no I/O). 2. `--term dumb` (it makes every later step testable as text). 3. SVG lines. 4. The other kinds. 5. The script form. 6. The report integration
in `metasearch-bidding`.

## 9. Open

Whether to install gnuplot and compare; the exact gnuplot subset; float formatting (section 2); the palette; whether `plot` should also read `stats`' JSON (intervals) directly.

## 10. Slice 1: `plot ticks LO HI [N]`, built [measured]

**The rule.** The raw step is (HI - LO) / N, written f * 10^e with f in [1, 10). f up to 1.5 gives a step of 1 * 10^e, up to 3 gives 2, up to 7 gives 5, and above that 1 * 10^(e+1); a tie
goes to the smaller step (a tolerance of 1e-9 makes 0.9 / 6 a tie). The ticks are the multiples of the step inside [LO, HI], the range being widened by 1e-9 of a step at each end. A tick
is the integer k * m and the exponent e, and its text is made from those two integers, never from a float: the labels are exact and fixed in length (`0.0 0.2 0.4`, not `0 0.2 0.4`).
This is a **[choice]** of the usual 1-2-5 rule, not gnuplot's own (section 2).

**The guard.** Tick numbers are integers and powers of ten up to 10^22 are exact floats, so a range is refused (`plot.range-invalid`) unless it lies within 1e15 of zero, is at least 1e-12
wide, and is no more than 1e12 times narrower than its distance from zero. The garbage-argument gate found this: `ticks -1e300 -1` ended in a trap (`truncate` of a float beyond an int).

**The gate** (`scripts/check_ticks.py`, `PLOT=build/plot`): 15 hand-checked cases, 600 random ranges against an independent implementation in exact fractions, 17 refusals each with its
rule tag, 200 garbage argument lists that must end in 0 or 2, and `--mutants` (needs `CANCHO`): 15 mutants of the library, all killed; three more are equivalent and are listed in the
script with the reason. **A bug the first version had, found by the gate** once the tolerance mutants were added: the tolerance guarded only one side, so `ticks 0.24 0.29 5` lost
the tick 0.29 (0.29 * 100 is 28.999999999999996 in a float); both ends are widened now, and the two cases are in the table.

**Not yet:** `--term dumb`, the SVG, the other kinds, the script form, the data input.

## 11. Slice 2: `plot --term dumb`, points from CSV on standard input [choice, before the code]

The text terminal comes first because it makes every later drawing step testable as exact text (section 8).

    plot --x COL --y COL[,COL..] [--term dumb] [--size WxH] [--title TEXT] < data.csv

**Input.** CSV with a header line (`,` between cells, `\n` or `\r\n` between lines); a column is named by its header or numbered from 1. A cell with a double quote is refused
(`plot.csv-quote`: quoted cells wait for a reader that handles them); a cell that is not a decimal number as JSON writes it is refused with its line (`plot.not-numeric`); a short line is
`plot.csv-shape`. At most 5 series (`plot.too-many-series`), at most 5,000 rows (`plot.too-many-points`). No row, or no column of that name: `plot.empty`, `plot.column-missing`.

**Axes.** Each axis takes the range of its data. That range gets the step of section 10 (aimed at 5 intervals for y and 6 for x) and is widened to the multiples of the step that enclose it; a
constant series is first widened by 1 each way. The axis labels are the ticks (section 10) inside the widened range, which are all its multiples.

**The grid.** `--size WxH` is the plot area in characters, default 60x20, W from 10 to 200, H from 5 to 60 (`plot.size-invalid`). A point (x, y) falls in column floor((x - xlo) * W / (xhi - xlo)) and
row floor((yhi - y) * H / (yhi - ylo)), both clamped to the last cell (tolerance 1e-9 of a cell); row 0 is the top. A series is drawn with `*`, `+`, `x`, `o`, `#` in the order of `--y`; a later series
overwrites an earlier one in a shared cell.

**The page.** Optional title line (the title centred over the plot area, left padding (W - len) / 2 rounded down, no padding when it is longer than W); then H rows; then the x axis; then the x labels; then the
legend. A row is the y label of the tick in that row if it has one (right-aligned in a gutter as wide as the longest label that is drawn, blank otherwise; when two ticks fall in one row, which happens at small heights, the higher one is drawn), a space, `|`, and the W cells. The axis row is the gutter's
width of spaces, a space, `+` and W `-`. A tick lands in the row (or column) of its value by the rule above, the top and the bottom ones being rows 0 and H-1. The x labels line has each label
centred on its column (start = column - len / 2 rounded down, from the first cell of the plot area), and a label is dropped if it would touch the previous one (less than one space between). The start is clamped to the plot area: from 0 to W minus the length. The legend is one line, `* NAME  + NAME` (two spaces between), the names being the headers. Trailing spaces are removed from every line; each ends with `\n`.

**Gate.** `scripts/check_dumb.py`: an independent implementation in exact fractions renders 200 random charts and 3 hand-drawn ones (written out in the script, drawn by hand from this section), plus the
refusals and garbage input; mutants of the library must be killed.

## 12. Slice 2, built [measured]

`plot --x COL --y COL[,COL..] [--size WxH] [--title TEXT] [--term dumb] < table.csv` draws the chart of section 11. `scripts/check_dumb.py` (`PLOT=build/plot`): 3 hand-drawn charts, 200 random charts
(1 to 5 series, `\n` and `\r\n`, columns by name and by number, titles from blank to 200 bytes) against an independent implementation in exact fractions, 4 rounding traps (0.29 * 100 is
28.999999999999996 and 0.07 * 100 is 7.000000000000001 in a float), 26 refusals each with its rule tag, the line number that `plot.not-numeric` and `plot.csv-shape` carry, 5,000 rows accepted,
200 garbage tables that must end in 0 or 2; `--mutants` (needs `CANCHO`): 40 mutants, all killed; one more is equivalent and is explained in the script.

**What building it found.** (1) Standard input is read with `read_bytes` into a buffer, but the arrays of the points must be on the heap (`box_slice`): a region is one 64 KiB chunk and 5,000 rows of
six series do not fit (the first run trapped, "region chunk exhausted"). (2) The gutter was first sized from every tick, including ones dropped when two ticks fall in one row, and the independent
implementation drew it from the drawn ones: the text of section 11 now says "drawn", and the program does. (3) The first set of mutants left twelve alive: the gate had no table with CRLF line endings, none with
five series, none that named a column by its number, no value that a float multiplies to just above or below a whole number, and nothing that read the line number in a refusal. Each of those is a case now.

**Not yet:** lines, bars, the histogram; `--term svg`; the script form; `--x` as an index when it is omitted.

## 13. Slice 3: lines for both terminals, and `--term svg` [choice, before the code]

    plot --x COL --y COL[,COL..] [--with points|lines] [--term dumb|svg] [--size WxH] [--title TEXT] < table.csv

`--with` defaults to `points`. `--size` is characters for `dumb` (default 60x20, section 11) and pixels for `svg` (default 640x400, W from 100 to 2000, H from 100 to 1200). Bytes below 0x20 or
0x7f in the title or in the header cells that name a series are refused with `plot.text-invalid` (a terminal and an XML file are both hurt by them).

**Lines in `dumb`.** Consecutive points of a series, in the order of the table, are joined in cell space. From cell (c0, r0) to (c1, r1), with dc = c1 - c0, dr = r1 - r0 and n = max(|dc|, |dr|), the
cells are, for i from 0 to n, (c0 + sign(dc) * ((2 |dc| i + n) div 2n), r0 + sign(dr) * ((2 |dr| i + n) div 2n)): integers only, `div` the floor of non-negative integers, so a half goes up. n = 0 is the
one cell. Series are drawn in order and a later glyph overwrites an earlier one, as for points.

**`svg`: the layout** (every number in user units = pixels). g is the length of the longest y tick label (all ticks, here nothing collides). left = 12 + 8 g, right = 16, top = 36 with a title and 12
without, bottom = 44. x0 = left, x1 = W - 16, y1 = top, y2 = H - 44; the plot area must be at least 20 wide and 20 high (`plot.size-invalid` otherwise). The ranges and ticks are those of section 11. In
doubles, in this order: X(x) = x0 + (x - xlo) / (xhi - xlo) * (x1 - x0) and Y(y) = y1 + (yhi - y) / (yhi - ylo) * (y2 - y1), with xlo, xhi, ylo, yhi the widened axis ends (the correctly rounded value
of the tick, section 10).

**`svg`: the text.** One element a line, in this order: the root `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 W H" width="W" height="H" role="img" aria-label="L">` where L is
the escaped title and `: ` if there is one, then `K series, N points` (`1 series` for one); the axes group `<g fill="none" stroke="currentColor" stroke-width="1">` with the path
`M x0 y1 V y2 H x1`, one path `M x0 Y h-4` for each y tick and `M X y2 v4` for each x tick; the text group `<g font-family="sans-serif" font-size="12" fill="currentColor">` with the title
(`<text x="W/2" y="20" text-anchor="middle" font-size="14">`), the y labels (`x="x0 - 8" y="Y + 4" text-anchor="end"`), the x labels (`x="X" y="y2 + 18" text-anchor="middle"`; a label is
left out when X is less than 8 (len + 1) pixels after the previous one drawn, len being its length), and the legend names (`x="x0 + 150 j + 14" y="H - 8"`); then for each series a path with
`fill="none" stroke="var(--series-J, #HEX)"`, J from 1 and HEX one of `0550ae`, `bc4c00`, `1a7f37`, `8250df`, `cf222e`: for lines `d="M X Y L X Y .."` with `stroke-width="1.5" stroke-linecap="round"` (one
point is `M X Y h0`), for points `d="M X Y h0 M X Y h0 .."` with `stroke-width="4" stroke-linecap="round"`; then the legend swatches `<rect x="x0 + 150 j" y="H - 17" width="10" height="10" fill=".."/>`; then
`</svg>`. A number is written with 2 decimals, correctly rounded from the double (a tie goes to the even digit), trailing zeros and a bare point dropped (every coordinate is at least 12, so a `-0` cannot come up). Text is escaped (`&`, `<`,
`>`, `"` as `&amp;`, `&lt;`, `&gt;`, `&quot;`). No clock, no id, no random: the same table and flags give the same bytes.

**Gate.** `scripts/check_dumb.py` gains `--with lines`; `scripts/check_svg.py` renders with an independent implementation (Python floats in the order above, ticks from fractions) 200 random charts and
hand-checked fragments, and the refusals; mutants of the sources must be killed. The SVG is also well-formed XML (`xml.dom.minidom` in the gate, not in the tool).

## 14. Slice 3, built [measured]

`--with lines` for both terminals and `--term svg`, as section 13 says; the sources are now `num`, `ticks`, `csv`, `axis` (what the terminals share), `dumb`, `svg`, `chart` (reading the table and
choosing the terminal) and `tools/plot/main.cho`. Gates: `check_dumb.py` (lines as well as points in its 200 random charts; 32 refusals), `check_svg.py` (hand fragments worked out from the
layout, 200 random charts compared line by line with an independent implementation and parsed as XML, 14 refusals, 100 garbage tables), `check_ticks.py`. Mutants: `check_svg.py` 41 killed, 0
survived, plus one equivalent in the script; `check_dumb.py` 46 killed (the 8 new ones are for the line segments; two more are equivalent and explained in the script), `check_ticks.py` 15. **Correction:** `cancho.toml` first pinned `695e8f9e`, the compiler of the checkout, but every gate was run with `9934b11f`; the pin says what was run.

**What the first mutants found, fixed by a case each.** (1) No chart had a plot area of exactly 20 pixels, so `< 20` and `< 21` looked the same: 7-character labels at W = 104 now. (2) No x labels
were exactly `8 (len + 1)` pixels apart: x from 0 to 2 at W = 180 now. (3) Only one control byte was refused, so the edges 0x1f and 0x7f were free; and no title had a byte above 0x7f, so `U+0100` (c4 80)
now has to be accepted. (4) One piece of the specification was dead: a coordinate is never below 12, so `-0` cannot be written; the branch that handled it is gone and the design says why.

**Limits.** The geometry is computed in doubles in the order of section 13; the oracle repeats the same operations on Python floats, which are the same IEEE doubles, so this checks the arithmetic is
as written, not that another order would give other digits. `dumb` counts a title by bytes, not characters, so a UTF-8 title is centred a little to the left of true. Colours are CSS variables with a
fallback (`var(--series-1, #0550ae)`); their contrast against white and against `#121212` is not measured yet.

**Not yet:** bars, the histogram, shaded bands, vertical markers, error bars, the diagonal; the script form; an index for `--x` when it is omitted; reading `stats` JSON directly.

## 15. Slice 4: markers, bands and the diagonal [choice, before the code]

    plot ... [--vline X[,X..]] [--hline Y[,Y..]] [--band LO,HI]... [--diag]

At most 8 values for each of `--vline` and `--hline`, at most 4 `--band`s (the flag may be repeated), `--diag` takes no value. A value that is not a number is `plot.not-numeric`, more than the maximum
is `plot.usage`, a band with LO above HI is `plot.range-invalid`.

**The ranges.** The x range is that of the data and of the `--vline` values; the y range is that of the data, the `--hline` values and the band ends. So a marker is always inside the chart. Everything else
(constant ranges, the guard, ticks) is as before.

**`dumb`.** Under the series, in this order, later over earlier: each band fills the rows from the row of HI to the row of LO, whole width, with `:`; each `--hline` fills its row with `-`; each
`--vline` fills its column with `|`; the diagonal joins, with the segment rule of section 13, the cell of (t0, t0) to the cell of (t1, t1), where t0 is the larger of the two lower axis ends, t1 the
smaller of the two upper ones, and nothing is drawn unless t0 < t1; it is written with `/`.

**`svg`.** After the text group and before the series, in the same order: for each band `<rect x="x0" y="Y(HI)" width="x1 - x0" height="Y(LO) - Y(HI)" fill="var(--band, currentColor)"
fill-opacity="0.12"/>`; for each `--hline` `<path d="M x0 Y H x1" fill="none" stroke="currentColor" stroke-width="1" stroke-dasharray="4 3"/>`; for each `--vline` `<path d="M X y1 V y2" ../>` with
the same attributes; the diagonal `<path d="M X(t0) Y(t0) L X(t1) Y(t1)" fill="none" stroke="currentColor" stroke-width="1" stroke-dasharray="1 3"/>`, with t0 and t1 as above. Numbers as in
section 13.

**Gate.** The two oracles gain the annotations (random ones in the random charts, edge cases listed); mutants of the new code must be killed.

## 16. The landing page [choice]

`site/index.html`, one static file with no script: what `plot` is, the three outputs (text, SVG, ticks), a gallery, and the gates. The gallery's charts are real output of the binary: `scripts/make_gallery.py` runs `build/plot` on the tables in `site/data/` and writes `site/gallery/*.svg` and `*.txt`, and the page embeds those files
inline, so the page shows exactly what the tool wrote. `scripts/check_site.py` checks that every gallery file is what the binary writes now (so the page cannot go stale), that the page is well-formed XML
and has no external reference, and that every command it shows is one of the commands that produced a file.

## 17. Slices 4 and 16, built [measured]

**Markers, bands, the diagonal** (section 15) in both terminals, through `axis.extent` (the one place that widens the ranges). The oracles draw them in half of the 200 random charts of each gate (up to 8
verticals, 8 horizontals, 4 bands, the diagonal), one hand-drawn chart pins their cells, the refusals are 45 for `dumb` and 14 for `svg`. Mutants: `check_dumb.py` 73 killed, `check_svg.py` 58 killed,
0 survived; equivalent ones are listed in the scripts with their reason (`c != 2` to `c < 2` in `--band`, and a leftward step of the diagonal that the code does not have: its columns only grow).
**What the mutants found.** Two ranges that only touch (x in [0, 2], y in [2, 4]) make a diagonal of no length: `t0 <= t1` and `t0 < t1` looked the same until that chart was in both gates. A branch of the
diagonal for a leftward step could never run (the survivor that showed it), so it is not there.

**The landing page** (section 16): `site/index.html` and `site/gallery/`, made by `scripts/make_gallery.py` from the binary, checked by `scripts/check_site.py` (the page and gallery made again must be the
committed ones, byte for byte; well-formed XML; no script, link, image, `src` or `url()`; links only to this repository and to files that exist; the command shown under each chart is the one that made it).
The check was seen to fail twice while it was written: a gallery file that no longer matched the binary, and a page that did not embed a gallery file. The page uses `<!DOCTYPE html>` in capitals
because the check parses it as XML. The data are made with integers only (a linear congruential generator), so they are the same on every machine; one chart is a real series, 302 days of a holdout's
margin from `metasearch-bidding`. To serve it: `python3 -m http.server --directory site`.

`scripts/check.sh` runs all of it: build, `cancho fmt --check`, the 2,000-line limit, the four checks, and with `MUTANTS=1` the mutants. The one known gap in the gallery is the palette's contrast, not
measured (section 14).

**Not yet:** bars, the histogram, error bars, series from a column of categories (`--by`), the script form. `--by` would be the next thing a report asks for: its tables are long (a row per day and arm), and
`plot` only reads wide ones (a column per series, one x for all).

## 18. The tests in cancho [measured]

Added after the gates above were written in Python: `tests/plot_test.cho` and `tests/plot_cases_test.cho`, run by `cancho test lib/plot/*.cho tests/plot_test.cho --std` and the same with `tests/plot_cases_test.cho` (one at a time: both define `same`; it is in `scripts/check.sh`, and `cancho.toml`
has the two `[[test]]`). **No Python was added for this.** A `test_*` function gets a heap and nothing else, so these test the library (`ticks`, `axis`, `dumb`, `svg`, `chart.draw`) and not the binary: the
tick cases of the gate, the four hand-drawn charts, the SVG fragments worked out from the layout, every code `chart.draw` answers with, the 5,000-row and 5-series limits, the control-byte edges (0, 9, 31,
127 refused; 32, 126, 128, 196 accepted), the size edges of the SVG (a plot area of 20 wide, 36 of margin and 16 on the right, so a width of 72), and 15 charts whose expected text was written out once from
the Python oracle (rounding traps, ranges that only touch, five series, zigzag lines, a blank title, markers beyond the data). 21 + 21 tests.

**How good they are, measured.** The 129 distinct mutants of the library that the three Python gates list were applied to the cancho tests alone, each test file run on its own, a build error never counted as a kill, the unmutated
sources required to pass first (a throwaway script, not kept). The first 12 tests killed 84; with the cases above, 122, then 128, then **all 129**: the survivors were cases the gates reach by chance in 200 random charts and the tests did
not (a diagonal between two axes that only touch, a bound of the band that widens the range, a float row trap, a line of another slope, and tick marks that come out in the wrong order: a mutant that mirrors them leaves the *set* of marks
unchanged, so the test checks their order). **Correction:** one measurement along the way said 129 of 129 when it had not measured anything: both test files had been given to one `cancho test`, which refuses them (both define
`same`), and a build error looks like a failure; that is why the script now reports a build error as such and `check.sh` runs the files one at a time. The 18 mutants of `tools/plot/main.cho` (flag parsing and sizes) are not reachable
from a `test_*` function; the Python gates are what covers them.

**What this does not replace.** The random charts (600 ranges, 200 charts per terminal, compared with the oracle in exact fractions), the XML check, the refusals through the binary with their exit status, the garbage
tables, and the landing page's freshness. Those stay in the Python scripts, which are not ported and not extended.

## 19. Plots for cancho-stats and cancho-ml [design, measured shapes; nothing built]

**What the two tools print, measured** (2026-11-10, `stats` 0.1.0 and `ml` 0.1.0, a 300-row table of two features, a group and a 0/1 target, and the 302-day series of the gallery). Both print one JSON document
(`stats.v1`, `ml.v1`: `ok`, `command`, `schema`, `data`, `meta`); `ml` writes every decimal as a string with its digits exact, `stats` writes JSON numbers.

| command | what it prints that can be drawn | chart |
|---|---|---|
| `stats describe --bins N [--by COL]` | per column `histogram {bins, edges[N+1], counts[N]}`, `quantiles [{p, value}]`, `min`, `max`, `mean`, `sd` | histogram; box plot (min, quartiles, max); one of each per group |
| `stats test t2/t1/paired/prop ...` | per test `interval {estimate, low, high, level}`, `p_value`, `effect_size {name, value}` | interval (forest) plot: one row per test, a dot and a bar; the zero line |
| `stats corr` | `pairs [{x, y, r, p_value}]` | matrix of `r` (heatmap), or bars of `r` |
| `ml eval` | `metrics {accuracy, precision, recall, f1, roc_auc, log_loss}` (strings) | bars of metrics |
| `ml cv` | `results [{repeat, fold, train, test, metrics{..}}]` | metric by fold: points with the mean as a line; box over folds |
| `ml importance` | `importance.columns [{column, importance, rank}]` and `permutation.columns [{column, importance, std, rank}]` | horizontal bars, with `std` as error bars |
| `ml calibrate` | calibration bins (to be read: `--prob-bins`) | reliability diagram: observed against predicted, the diagonal |
| `ml predict --proba` | `data.rows [[label, probability]]`, `columns` | ROC and precision-recall curves, a histogram of the probabilities, once `plot` computes them |
| `ml runs compare/list` | tracked runs and their metrics | bars; points over runs |

**What `plot` lacks for them**, in the order of how many of the charts need it:
1. **Bars** (`--with bars`): a category on x (the cell's text, not a number), one bar a category, grouped for several series, from a baseline that includes 0; also horizontal (`--horizontal`) for long names.
2. **Intervals / error bars**: `--yerr COL` (symmetric) or `--ylo COL --yhi COL`, drawn on points, lines and bars. The forest plot is points with intervals and a `--vline 0`.
3. **A histogram** from edges and counts (steps, bars on a numeric x), and from raw values (`--hist COL --bins N`, with the bins `stats` would choose, so the two agree).
4. **JSON input.** `plot --json PATH...` reads the documents above: a path to an array of objects (`data.columns.0.histogram`, `data.tests`, `data.importance.columns`), and the columns to use as `--x`/`--y`. Strings holding decimals (`ml`) are numbers here. A pipe `stats ... | plot ...` is then the whole interface.
5. **Heatmap** (`--with heat`: x, y, value; a cell a rectangle, the value a colour ramp, the value written when it fits) for correlations and confusion matrices.
6. **Box plot** (`--with box`: five numbers a row, whiskers, optional points).
7. **Curves computed by plot**: ROC and precision-recall from a label and a score column (sorting, exact integer counts, the area as a check against `roc_auc`), the empirical CDF and a Q-Q plot from one column. These are statistics, so each has to be measured against `ml`'s and `stats`' own numbers (the ROC area against `roc_auc`).
8. **`--by COL`** (a series for each value of a column), which the report already needed.

**Constraints that carry over.** Same rules as sections 1 to 18: a refusal is a rule tag; the same table gives the same bytes; both terminals draw every kind; **no Python**: the tests are `cancho test` cases (expected text derived by hand from the layout rules, or from the tool's own printed numbers) plus the binary's own refusals, and
each new kind gets a mutant check by the same throwaway measurement as section 18, a kill rate stated as measured. The first gate for ROC is `ml eval`'s `roc_auc` to every digit it prints.

**Order proposed.** (a) bars with categories, grouped, both terminals, and error bars on them (items 1 and 2: this alone draws feature importance, metrics, folds and the forest plot); (b) JSON input for `stats describe` histograms and `ml` documents (items 4 and 3 from edges);
(c) heatmap and box (5, 6); (d) the curves (7) and `--by` (8). Each is a section here before its code, as the others were.

## 20. Slice 5a: bars with categories, and error bars [choice, before the code]

    plot --x COL --y COL[,COL..] --with bars [--yerr COL[,COL..]] ...

**Bars.** With `--with bars` each row of the table is a category: the cell of `--x` is its label, as text (quotes and bytes below 0x20 or 0x7f are refused as before), and the category's place is its row, 0 to n-1.
Several series are grouped side by side, in the order of `--y`. The y range of the data **includes 0**, so a bar is drawn from 0 to its value (downward when it is negative). No numeric x axis: the labels of the categories take its place.
Labels are cut to 10 bytes; one is left out when it would come less than one space (`dumb`) or less than 8 (len + 1) pixels (`svg`) after the previous one drawn.

**Error bars.** `--yerr COL[,COL..]`: one column of half-lengths for each series, in order (a different count is `plot.usage`; a cell that is not a number is `plot.not-numeric`; a negative one is `plot.range-invalid`).
They apply to every kind: on a point at the point's x, on a bar at the middle of the bar. The y range includes value - err and value + err. **Not yet:** asymmetric intervals, horizontal bars (`--horizontal`).

**`dumb`.** Let n be the categories and W the width; a category's slot is the columns from s = floor(i W / n) to e = floor((i + 1) W / n), of width sw = e - s. With k series the group is bw = floor((sw - g) / k) columns a
bar, where g is 1 when sw > k and 0 when sw = k, and starts at s + floor((sw - k bw) / 2). A chart where floor(W / n) < k is refused: `plot.size-invalid`. Bar j of category i fills, in its columns, the rows from the row of its value to the row of 0, both ends
included (so a bar of height 0 is one row), with the glyph of series j; the rows are those of section 11. Error bars: the `|` glyph in the rows from the row of value + err to the row of value - err, at the column bs + floor(bw / 2) of the bar (bs its first column), drawn after all the bars, over them; for points and lines at the column of the point, drawn **before** the series, so that the point stays visible (a change made when a real interval plot hid its points: section 24). Labels
are centred on s + floor(sw / 2), cut and placed as section 11 places the x labels (start = centre - floor(len / 2), clamped to the area). The y axis, the legend and the rest are as before.

**`svg`.** sw = (x1 - x0) / n, the group is 0.8 sw wide and centred, a bar bw = 0.8 sw / k; bar j of category i starts at x0 + i sw + 0.1 sw + j bw (doubles, in this order) and is `<rect x y width height fill="var(--series-J, #HEX)"/>` with y the smaller of
Y(v) and Y(0) and the height their difference; the rects come after the annotations of section 15. Error bars come after the series: one path for each series, `M cx Y(v+e) V Y(v-e) M cx-3 Y(v+e) h6 M cx-3 Y(v-e) h6` for each point
(cx the middle of the bar, or X(x)), with `fill="none" stroke="currentColor" stroke-width="1"`. The x ticks of the axis group are a mark at the middle of each category, `M cx y2 v4`; the labels are `<text x="cx" y="y2 + 18" text-anchor="middle">`. A bar narrower than 1 pixel is refused with `plot.size-invalid`.

**Gate.** `cancho test`, as section 18: hand-worked charts for both terminals (one series, two series, a negative bar, error bars on bars and on points, a category label that is dropped), every new refusal, and the
size edges; then the throwaway mutant measurement of section 18 on the new code, with the rate stated.

## 21. Slice 5a, built [measured]

`--with bars` and `--yerr` as section 20 says, in both terminals, through the same functions as before: `chart.draw` reads a category's label as text (`cs`, the spans of the labels) and the half-lengths after the series
(`ys` holds the k series and then the k columns of errors), `axis.extent` includes 0 for bars and value +- err, `dumb.slot` places a group of bars, and `svg.render` draws the rects and the one path of error bars for each series.
**No Python was added.** `ac` grew from 4 to 8 integers (`ac[4]` bars, `ac[5]` the number of error series), so every `alloc_slice[r](4, 0)` of the tests became 8; the one stale assertion in `check_dumb.py` (`--with bars` is now valid,
so the refusal uses `pie`) was changed in place.

**Tests:** 17 new `cancho test` cases in `tests/plot_test.cho`, every chart worked out by hand from the rules and then compared with the program: one series, error bars on bars, grouped, a negative bar, a slot exactly as wide as the
series (no gap), cut and dropped labels, the width refusals, error bars on points in both terminals, the svg rects and paths with their numbers (65.4, 235.2, ...), every refusal. Writing them found nothing wrong in the program,
and one of my hand-derived expectations wrong (I had used a bar of 2 for a table that says 1.5); the program was right.

**Measured, as in section 18:** 42 mutants of the new code against the cancho tests alone: the first tests killed 35; the 7 survivors were a slot as wide as the series, a label of exactly 11 bytes, a baseline that is a row off, an `--yerr` with
more columns than series, and a bar of exactly one pixel; with a test for each, **40 of 42 are killed** and the 2 left are equivalent: `xs[row] = float_of(row)` (for bars `xs` is only used for the range guard) and the svg label
cut written as `if ln > 9 { ln = 10; }` (a mutant of the condition only, which cannot change what the body gives for 10 and 11).

**Limits.** A point chart still needs a numeric x: a forest plot with the names of the tests on x waits for categories outside bars (the gallery's uses the number of the test). Horizontal bars (long names) and asymmetric intervals
(`--ylo`, `--yhi`) are not built. The category slot is the row, so a table must be in the order to draw.

**Gallery:** four charts were added (permutation importance with error bars, grouped bars of cross-validation folds, an interval plot with the zero line, bars as text); their data have the shape `ml importance`, `ml cv` and
`stats test` print, written by `make_gallery.py`, not read from those tools: reading their JSON is slice (b).

## 22. cancho-opt [measured, not supported yet]

`opt minimize` prints one JSON object when it ends: `method`, `x`, `fun`, `nfev`, `nit`, `converged` (BFGS adds `jac`; SPSA says `completed`). Measured 2026-11-10 with a build of `cancho-opt` at its pin, Nelder-Mead on Rosenbrock from (-1.2, 1):
`fun` 8.2e-10 after 159 evaluations and 85 iterations, and nothing else: **it prints no iteration, so there is no convergence curve to draw**. What can be drawn today is what a table of several runs holds (a row for each method, start or seed:
`fun` and `nfev` as bars, in log scale once `--logy` is built), and that is the input slice (a) already reads. A convergence plot (`fun` and the step by iteration, the simplex shrinking, the BFGS gradient norm) needs `opt` to write a trace, for instance
`--trace FILE` with a row for each iteration: a change to cancho-opt, to be designed there, with `plot --x iter --y fun --logy` as its reader. The same holds for cancho-rl and cancho-solve: a training or solve log with a row for each step is what `plot` reads.
Also seen while measuring: `opt minimize --method spsa --x0 -1.2,1 --objective rosenbrock --maxiter 50` with the default gains ends at x = -3.8e42 (it diverges); that belongs to cancho-opt, not to plot.

## 23. Slice 5b: JSON input, and intervals that are not symmetric [choice, before the code]

    <tool printing JSON> | plot --json PATH --x FIELD --y FIELD[,..] [--yerr F[,..] | --ylo F[,..] --yhi F[,..]] [--with ..] ...

**Why.** `stats` and `ml` print a JSON document, not a table (section 19). Reading it directly makes `ml importance --model-file m ... | plot --json data.importance.columns --x column --y importance --with bars` the whole interface, with no
CSV in between and no script.

**PATH.** Dot-separated components from the root: a key, or a non-negative whole number (an index into an array); `.` is the root. The value there must be (A) an array of objects, a row each, or (B) an object with `columns` (an array of
strings) and `rows` (an array of arrays), the form `ml predict` and the `trace` of section 12 of cancho-opt's design use. Anything else is `plot.json-path` (also a missing key or index).

**FIELD.** In form A a dotted path into the row (`interval.estimate`, `metrics.roc_auc`), in form B a column name. A value is read as a number (an integer, or a float as the text the document holds; **`ml` writes numbers as strings, and a string that is a
decimal is a number here**) or as text for a category (no quote, comma or byte below 0x20 or 0x7f: `plot.json-value`). A missing field, or `null`, is `plot.json-field`, with the row. `true` and `false` are refused as `plot.json-value`. At most 5,000 rows (`plot.too-many-points`);
a document that is not JSON is `plot.json-invalid`; a document over 16 MiB is refused as the table is.

**Meaning.** The rows are made into the table the other forms read (a header with the fields as written, a row each), and then everything is as for a CSV: the same refusals, the same charts, the same bytes. A float is written back as the shortest text that reads
as the same number, so what is drawn is what the document says.

**Asymmetric intervals, for CSV and JSON alike.** `--ylo` and `--yhi` take one field each for each series (the absolute low and high of the interval, as `stats test` prints `interval.low` and `interval.high`): the whisker runs from low to high. A
`low` above the value or a `high` below it is `plot.range-invalid`; a count that is not the series' is `plot.usage`; with `--yerr` too, `plot.usage`. They apply wherever `--yerr` does, and the y range includes them. `--yerr` stays the half-length on both sides.

**Not in this slice.** Histograms from `stats describe` (a bar for each bin between two edges: slice c), a key with a dot in its name (it cannot be addressed), several documents on the input, `--json` with `--term` unchanged.

**Gate.** `cancho test` as before: hand-made documents for each shape (A with nested fields, B, the strings of `ml`, a category), every refusal, the real documents of `stats` and `ml` printed by the tools on a 300-row table (kept as test data and
compared by hand-derived charts), and the measurement of the mutants of the new code against the tests alone, the rate stated.

## 24. Slice 5b, built [measured]

`--json PATH` (`plot.jsontable`: the document made into the table the other forms read, with the number text copied from the tape, so what is drawn is what the document says), `--ylo` with `--yhi` (the error arrays now hold how far below and above each value:
`ys` is the k series, then k columns of `down`, then k of `up`), and `--categories` (text on x for points and lines: a point at the middle of its slot, the label under it). The new refusals: `plot.json-invalid`, `plot.json-path`, `plot.json-field`,
`plot.json-value` (the last two with their row), `plot.usage` for the combinations of `--yerr`, `--ylo` and `--yhi`. **No Python was added**; the gates that exist were not touched.

**What the real tools gave.** `ml importance`, `stats test t2` and `ml cv` were run on a 300-row table and their documents are in `site/data/*.json`; the gallery draws all three straight from them (`--json data.permutation.columns --x column --y importance
--yerr std`; `--json data.tests --x column --y interval.estimate --ylo interval.low --yhi interval.high --categories`; `--json data.results --x fold --y metrics.roc_auc,metrics.accuracy`). Two things the real documents showed the design had wrong: a forest plot has the *names*
of the tests on x, so categories could not stay bars-only (`--categories`), and in the text terminal a whisker drawn after the point hid it, so for points and lines the whiskers are now drawn before the series (section 20 says so).

**Tests and measure.** 53 + 21 `cancho test` cases (section 18's way): hand-made documents of every shape and every refusal, the real documents of `ml` and `stats` (the table they become, exactly), intervals by their ends in both terminals with the numbers worked out by hand (the whisker of
`y = 1` from 0.5 to 1.8 at 177.12 and 356), categories on points, lines and error bars, the limits (5,000 and 5,001 rows; nine-digit indexes). Mutants of the new code against these tests alone: 36; the first tests killed 25, with a test for each survivor 33,
and the 3 left are equivalent: `c < 32` to `c < 31` in the reader (the JSON reader itself refuses a raw byte 0x1f in a string, which a test checks), `parse(..) <= 0` to `< 0` (parse answers a positive count or a negative error, never 0), and the check for a double quote in a plain
string, which a plain string cannot hold (the check was removed: dead code). The new flags' *plumbing* in `tools/plot/main.cho` (`--json`, `--ylo`, `--yhi`, `--categories`) is not reachable from a `test_*` function and has no test: it was run by hand on the three real documents (the gallery's commands) and
by `check_site.py`, which draws them again every time.

**Not yet:** histograms from `stats describe` edges and counts (slice c), `--logy`, horizontal bars, a key with a dot, several documents.

## 25. Slice 5c: histograms from edges and counts [choice, before the code]

    plot --x LO --xhi HI --y COUNT[,COUNT..] --with hist ...
    stats describe --bins N --cols C FILE | plot --json data.columns.0.histogram --x lo --xhi hi --y count --with hist

**What `stats` prints** (measured, `stats describe --bins 10 --cols x1,x2` on a 300-row table): per column `histogram {"bins": N, "edges": [N+1 numbers], "counts": [N integers]}`, not an array of objects. So the JSON reader learns a third shape (C): an object with arrays
`edges` and `counts`, `len(edges) = len(counts) + 1`, is read as N rows with the columns `lo` (edges[i]), `hi` (edges[i+1]) and `count` (counts[i]). Anything else with those keys is `plot.json-path`.

**The chart.** One bar for each row, from `--x` (its lower edge) to `--xhi` (its upper edge) on a numeric x axis, at the height of each `--y` series (normally one); the y range includes 0; the x range is the lowest lower edge to the highest upper one, with the ticks of section 10. More than one series are drawn in order,
a later over an earlier; in `svg` with `fill-opacity="0.6"` when there are two or more. `--yerr`, `--ylo`, `--yhi` and `--categories` with `hist` are `plot.usage`. A row whose upper edge is not above its lower edge is `plot.range-invalid`; the bars may leave gaps between them.

**`dumb`.** For a bin from `lo` to `hi`: t(v) = (v - xlo) * W / (xhi - xlo) + 1e-9, the columns are from c0 = floor(t(lo)) up to but not including c1 = floor(t(hi)), both clamped to the width (so the last edge ends at W), and c1 is at least c0 + 1; when it spans 3 columns or more the last is left empty, so two bins can be told apart. The rows are
those of the bars of section 20: from the row of the value to the row of 0, both included, with the glyph of the series.

**`svg`.** Bin i is `<rect x="X(lo)" y="min(Y(v), Y(0))" width="X(hi) - X(lo) - g" height="|Y(0) - Y(v)|" fill="var(--series-J, #HEX)"/>` with g = 1 when X(hi) - X(lo) > 3 and 0 otherwise (doubles, section 13's formulas), after the annotations, in place of the series paths.

**Gate.** `cancho test`, hand-worked: three bins in both terminals, a bin of one column, two series, every refusal, the JSON shape C (with the real document of `stats` as test data); then the mutant measurement as in sections 18 and 24.

## 26. Slice 5c, built [measured]

`--with hist` with `--xhi` (section 25), in both terminals, and the third JSON shape (an object with `edges` and `counts`: the columns `lo`, `hi`, `count`). `axis.extent` takes the x range to the highest upper edge, which `chart.draw` stores after the error columns in `ys`.
**No Python added.** `chart.draw` took one more argument (`xhi`), so the tests' calls changed; the Python gates were not touched and still pass.

**Real document.** `stats describe --bins 10 --cols x1,x2` on the 300-row table is `site/data/stats-describe.json`; the gallery draws its first column's histogram as svg and as text straight from it (`--json data.columns.0.histogram --x lo --xhi hi --y count --with hist`).

**Tests and measure.** 64 + 21 `cancho test` cases now; the histogram ones are worked out by hand: three bins (with the 3-column bin that leaves its last column empty), a bin narrower than a column, the svg rects (`X(v) = 20 + 151 v`), two series, a bin 3.5 pixels wide, every refusal, the JSON shape with
the real histogram, and three cases the mutants asked for: an edge that a float puts under its column (0.29 * 100 is 28.999999999999996, so the edge is column 29 only with the slack), a lower edge a billionth of a column from the end, and a baseline one row off. Mutants of the new code against the tests alone: 31; the first tests killed 24, with a test for each survivor 29, and 2 are
equivalent: the `kh > 0` of the refusal for a histogram with intervals (the checks before it already refuse `--ylo`/`--yhi` without a matching `--yerr`, so it cannot be the only one that fires) and `edges >= 0 && counts >= 0` to `||` in the reader (an object with only one of them is refused as not rows either way).
Left out as equivalent without a test: the index `2 * ac[5]` of the upper edges, which is 0 for a histogram (it takes no intervals).

**Not yet:** box plots and heatmaps (the rest of slice c, a design of their own), the curves computed by `plot` (ROC, empirical CDF, Q-Q), `--logy`, `--by`, horizontal bars.

## 27. Slice 5d-1: box plots [choice, before the code]

    plot --x LABEL --y MIN,Q1,MEDIAN,Q3,MAX --with box ...
    stats describe --quantiles 0.25,0.5,0.75 --cols a,b | plot --json data.columns --x name --y min,quantiles.0.value,quantiles.1.value,quantiles.2.value,max --with box

**Input.** One row for each box: the label of the category in `--x` (text, as for bars), and exactly five columns in `--y`, in this order: the lower whisker, the first quartile, the median, the third quartile, the upper whisker (a different count of columns is `plot.usage`).
A row that is not in order, lower <= q1 <= median <= q3 <= upper, is `plot.range-invalid`, with its line. This is the shape `stats describe` prints (`min`, `quantiles` of 0.25, 0.5 and 0.75 by their position in the list, `max`), so the JSON fields above are dotted paths with an index. The y range is that of the five columns (it does not include 0).

**`dumb`.** A box takes the slot of its category and one column group (section 20's `slot` with one series: first column `gs`, width `bw`). In this order, later over earlier: the whisker, the glyph `|` at column gs + floor(bw / 2) from the row of the upper whisker to the row of the lower one; the box, the glyph `#` in the columns gs to gs + bw - 1, from the row of the
third quartile to the row of the first, both included; the median, the glyph `=` in the same columns on the row of the median. No legend (a box has no series). A chart where floor(W / n) < 1 is `plot.size-invalid`.

**`svg`.** Slot sw = (x1 - x0) / n, centre cx = x0 + (i + 0.5) sw (doubles, as before), box width 0.5 sw. After the annotations: for each box `<rect x="cx - 0.25 sw" y="Y(q3)" width="0.5 sw" height="Y(q1) - Y(q3)" fill="var(--series-1, #0550ae)" fill-opacity="0.35" stroke="currentColor" stroke-width="1"/>`;
then one path of the whiskers and caps, `M cx Y(q3) V Y(upper) M cx Y(q1) V Y(lower) M cx-6 Y(upper) h12 M cx-6 Y(lower) h12` for each box, `fill="none" stroke="currentColor" stroke-width="1"`; then one path of the medians, `M cx-0.25 sw Y(median) h 0.5 sw` for each box, `fill="none" stroke="currentColor" stroke-width="2"`. The category marks and labels are those of bars. No legend swatch or name, and the `aria-label` says `N boxes`.
A box narrower than 2 pixels is `plot.size-invalid`.

**Gate.** `cancho test`: hand-worked charts in both terminals, the order refusals, the count refusal, the JSON path with indexes on a real `stats describe` document; the mutant measurement as in sections 18, 24 and 26.

## 28. Slice 5d-1, built [measured]

`--with box` as section 27 says, in both terminals; the category axis of bars is reused (`ac[4] == 3` counts as a category chart), the y range is the five columns' own (it does not start at 0), and no legend is written. **No Python added.**
The real document: `stats describe --bins 10 --quantiles 0.25,0.5,0.75 --cols x1,x2` (`site/data/stats-describe.json`), drawn by the gallery as svg and as text with `--json data.columns --x name --y min,quantiles.0.value,quantiles.1.value,quantiles.2.value,max`.

**Tests and measure.** 71 + 21 `cancho test` cases now. The box ones are worked out by hand: two boxes in text (the whisker, the `#` box, the `=` median, no legend line) and in svg with their numbers (`Y(v) = 12 + 68.8 (5 - v)`; rects at 95.5 and 397.5, whisker and median paths), a box far from 0, every
order refusal (each neighbouring pair of the five numbers in turn, equal numbers allowed), the count, intervals and categories refused, the size edges (a column for each box in text; 2 pixels in svg: 80 wide takes 11 boxes, 79 does not), and the JSON path with indexes (`quantiles.0.value`) on the shape of the real document.
Writing them found one thing in the program: the text chart printed an empty line where the legend would have been (the test said no line; the program is fixed). Mutants of the box code against the tests alone: 37 first; the first tests killed 31; with a test for each survivor and two checks removed as dead code
(`kh > 0` in the refusal, which `ke > 0` and the checks before it already cover, here and in the histogram's; and the legend count in `dumb`, made redundant by dropping the line), every mutant that still applies is killed: 32 of 32 in the main run and the 5 for the rewritten refusals.

**Not yet:** heatmaps, the curves computed by `plot` (ROC, empirical CDF, Q-Q), `--logy`, `--by`, horizontal bars.

## 29. Slice 5d-2: heatmaps [choice, before the code]

    plot --x XCOL --y YCOL --z VALUE --with heat ...
    stats corr --cols a,b,c FILE | plot --json data.pairs --x x --y y --z r --with heat

**Input.** One row for each cell: a label for the column in `--x`, a label for the row in `--y` (one column: a different count is `plot.usage`), and a number in `--z` (a flag the histogram's `--xhi` shares: it is the one extra column a kind takes). Labels are text (the checks of bars apply); the categories of each axis are
numbered in the order in which they first appear, and may be at most 50 each, 2,500 rows in all (`plot.too-many-points`). A cell given twice is `plot.duplicate-cell`; a cell not given is blank. `--yerr`, `--ylo`, `--yhi`, `--xhi` and `--categories` with `heat` are `plot.usage`.
This is the long form `stats corr` prints (`pairs` of `x`, `y`, `r`) and the one a confusion matrix has as rows `actual,predicted,count`.

**Scale.** vmin and vmax are the least and greatest value; t = (v - vmin) / (vmax - vmin), and 0.5 for all cells when vmax = vmin. The two numbers are written under the chart as the cells' own text (the text of the first cell that holds each).

**`dumb`.** With nx columns of cells and ny rows, a cell is cw = floor(W / nx) columns by ch = floor(H / ny) rows, at least 1 each (`plot.size-invalid` otherwise); the chart is nx cw by ny ch. A cell holds the glyph of level min(9, floor(10 t)) in the ramp `.,:-=+*#%@` (counted from 0: t = 0.5 is level 5, `+`; the lowest level is a visible glyph, so a cell that is not given, a space, can be told from a low one: the first draft had a space for level 0 and a real corr matrix showed a minimum as a hole). A row is
its label (the first 10 bytes, right-aligned in a gutter as wide as the longest label, on the first line of its block, blank on the others), a space, `|`, the cells. Then the axis row, `+` and nx cw `-`, in the gutter's width of spaces plus a space; the labels of the columns on one line, each cut to 10 bytes and centred
on the middle of its block, left out when it would touch the one before (section 11's rule); then the line `min V  max V`. The title is as before.

**`svg`.** The margins of section 13 (left = 12 + 8 g with g the longest label cut to 10, top 36 or 12, bottom 44, right 16; a plot area under 20 is `plot.size-invalid`). Cell (i, j) is `<rect x="x0 + i sw" y="y1 + j sh" width="sw" height="sh" fill="var(--series-1, #0550ae)" fill-opacity="O"/>`, sw = (x1 - x0) / nx, sh = (y2 - y1) / ny, O = 0.05 + 0.9 t (two decimals). Where
sw is at least 30 and sh at least 14, the value is written in the cell, `<text x="centre" y="centre + 4" text-anchor="middle">`, as the cell's own text cut to 6 bytes. The row labels are at x0 - 8 (`text-anchor="end"`, y the centre + 4), the column labels at y2 + 18 (the rule of bars), and the line `min V  max V` at x0, y = H - 8.

**Gate.** `cancho test`: hand-worked charts in both terminals (three by three with a blank cell, a constant matrix, one cell), every refusal, the JSON path on a real `stats corr` document; the mutant measurement as before.

## 30. Slice 5d-2, built [measured]

Heatmaps are built as section 29 says, in `lib/plot/heat.cho`, with the parsing in `chart.cho` and the flag `--with heat --z COL`. 85 `cancho test` cases pass in all (`tests/plot_test.cho` and `tests/plot_cases_test.cho`, run one file at a time).

**Mutants.** 41 single-line mutants of `heat.cho` and of the heat paths of `chart.cho`: 39 killed, 2 survive, and both are equivalent:

- `if lv > 9 { lv = 9; }` to `lv >= 9`: the body then assigns 9 to 9.
- `if start > total - ln { start = total - ln; }` to `>=`: the body then assigns `total - ln` to itself.

A first run killed 34 of 41; the seven that lived were real gaps, and tests were added for them.

**Gallery.** `jsonheat` (svg) and `heattext` (dumb) draw the real `stats corr` document in `site/data/stats-corr.json`.

## 31. Slice 5e: curves that plot computes (ECDF, ROC, Q-Q) [choice, before the code; built and measured in section 32]

**Why in plot.** `ml` prints a score and `roc_auc`; the curve itself is a computation over the rows, which only the table has. A curve is a transformation of a table into a table, so it is written as CSV and the chart reads it as any other (no new drawing code).

**The flag.** `--curve ecdf|roc|qq`, with `--x COL` (the column the curve is about) and, for roc only, `--y COL`. The chart is then drawn from the computed table: lines for ecdf and roc, points for qq. `--json PATH` composes (the document is turned into a table first, then the curve is computed). Everything else (`--term`, `--size`, `--title`, markers, `--diag`) works as before.

**ECDF.** `--x v`. Sort the n values; for each distinct value v one row, (v, k / n) with k the count of values at or below v. Header `value,F`. The line joins the points; it is not a true staircase (a staircase would need 2 rows for each value, over the 5,000-row limit).

**ROC.** `--x label --y score`; the label is exactly 0 or 1 (`plot.roc-label` otherwise, with the line), and both classes must be present (`plot.roc-classes`). With P positives and N negatives, walk the distinct scores from the highest; after each score, one row (FP / N, TP / P), after the first row (0, 0). Tied scores cross together, so a tie between a 1 and a 0 gives the diagonal step. The area is the trapezoid sum over the rows, written with three decimals in the name of the y series: `tpr auc 0.750`. Claim: this is the Mann-Whitney statistic (the share of pairs of a positive and a negative in which the positive scores higher, a tie counting one half), which is what `roc_auc` of `ml` is. The `ml` binary is not built in this checkout, so the equality is checked against the pair count worked by hand (88 of 100 pairs, 0.880, for the gallery table), not against `ml`. Hand-worked: scores 0.8 (1), 0.4 (0), 0.35 (1), 0.1 (0) give the rows (0,0) (0,.5) (.5,.5) (.5,1) (1,1) and area 0.75.

**Q-Q (normal).** `--x v`. The sorted values against the standard normal quantiles at (i + 0.5) / n for i from 0. Header `theoretical,sample`. The quantile is Acklam's rational approximation (relative error under 1.2e-9, far below what a chart shows); known values are tested to 1e-5.

**Numbers in the computed table.** Values the user gave are written as they read back exactly (a whole number as digits, else the shortest decimal that round-trips); values plot computed (F, FPR, TPR, the quantile) with nine decimals, trailing zeros dropped.

**Limits and refusals.** 4,999 rows at most (the ROC adds a row), else `plot.too-many-points`. Every existing table refusal keeps its tag (`plot.csv-quote`, `plot.csv-shape`, `plot.not-numeric`, `plot.column-missing`, `plot.empty`), with the line of the row.

**Not in this slice:** `--by` (one curve for each group), `--logy`, a staircase ECDF, and the scores of `ml` read directly from its JSON (ml prints the area, not the scores).

## 32. Slice 5e, built [measured]

`--curve ecdf|roc|qq` is built as section 31 says: `lib/plot/curve.cho` turns the table into the CSV of the curve, and `main.cho` feeds it to the same chart code (lines for ecdf and roc, points for qq). `tests/plot_curve_test.cho` has 15 `cancho test` cases, all hand-worked: the ECDF steps (and a reversed input of 8 values, which runs the shell sort at three gaps), the ROC for 2 and 2, perfect, reversed, tied, unequal classes (1 positive and 2 negatives; 1 and 3, area 2/3 shown as 0.667), the area as the pair count (88 of 100, 0.880) for the gallery table, Q-Q for one value and for three, the known quantiles (0.5, 0.975, 0.9, 0.001, 0.999, 0.02, 0.98, to 1e-5), every refusal code with its line, and the row limit on both sides (4,999 accepted, 5,000 refused).

**A bug the limit test found.** The first version held the values and labels in a region, which is 64 KiB in all; at 4,999 rows the two arrays are 80 KB and the program trapped with exit 132 (no rule tag, which the rules forbid). The arrays are on the heap now (`box_slice`), and the test with 4,999 rows is what keeps it so. The CLI was checked by hand at 4,999 rows (all three curves, exit 0) and at 5,000 (refused with `plot.too-many-points`, exit 2).

**Mutants.** 43 single-line mutants of `curve.cho`: 38 killed, 5 survive. The first run killed 32 of 43; the six real gaps (the boundary at 4,999, the rates divided by the class sizes when the classes differ, the rounding of the area, nine decimals, and a value past 1e15) each have a test now. The five that live give the same output by construction:

- `gap = n / 2` to `gap - 1` in the shell sort: any decreasing gap sequence that ends at 1 sorts.
- `v[j - gap] > tv` to `>=`: equal values may swap, and equal values give the same rows (ECDF and Q-Q write equal values the same; the ROC crosses tied scores together).
- `let low = 0.02425`, `p < low`, `p > 1.0 - low`: where Acklam's two formulas meet; both are accurate to 1.2e-9 on either side, so moving or sharpening the cut changes the quantile by less than the tests can read (1e-5) and far less than a chart shows. These three are not proved equivalent; they are below the resolution of the check.

**Not measured:** the ROC area against `ml`'s `roc_auc` (the `ml` binary is not built in this checkout; the pair count is the definition, worked by hand).

**Gallery.** `roc`, `ecdf` and `qq` draw `site/data/scores.csv` (20 hand-written example rows, said to be so on the page, not the output of a model).

## 33. Slice 5f: `--logy` and `--by` [choice, before the code]

**`--logy`.** The y axis in log10. For lines and points only: with `--with bars|hist|box|heat`, error bars (`--yerr`, `--ylo`), or `--diag`, a usage refusal (`plot.usage`, code 11): a bar's base at zero has no place on a log axis, and the diagonal y = x is not straight on it. Every plotted y value, and every `--hline` and `--band` value, must be above 0, else `plot.log-nonpositive` with the line of the first offending row (0 for a marker). The values are replaced by their log10 before anything else, so the data, the markers and the bands all go through the one transform.

*Range and ticks.* The range is widened to whole exponents (floor of the low, ceil of the high; one decade when they are equal), and the ticks are at whole exponents, with the step 1, 2 or 5 decades that section 10 picks for the span (never a fraction of a decade: a step below 1 is made 1). A tick at the exponent x is labelled with the number 10^x: digits for 1 to 1000000 (`1`, `10`, `1000000`), `0.1` to `0.000001`, and `1e7`, `1e-7` beyond. Claim to measure: the tick labels of a table that spans 1 to 1000 are `1 10 100 1000` and the point at 100 is at the same height as the tick `100`.

**`--by COL`.** One series for each value of the column COL (text, the same cell rules as categories: no quote, no comma, no control byte), taken from a long table. Series share the x column in this program, so a group must give the same x values as the first group, in the same order: the first group's rows set the x values; any other group with another count, or another x at the same position, is `plot.by-misaligned` with the line of the first row that differs. At most 5 groups (`plot.too-many-series`), named by their text in order of first appearance. `--y` takes one column; `--by` is not combined with `--curve`, intervals, or `bars|hist|box|heat`. `--json` composes (the by field is read with the others). Not in this slice: groups with different x values (it needs a per-series x in the drawing code).

**Gate.** `cancho test`: hand-worked charts with `--logy` in both terminals (the axis of 1 to 1000, a single decade, a half-decade range widened to whole exponents), every refusal; `--by` pivots by hand, every refusal; mutants as before.

## 34. Slice 5f, built [measured]

`--logy` and `--by COL` are built as section 33 says: the log transform is in `chart.cho` (before the ranges), the whole-exponent ticks and widening in `axis.cho`, the power-of-ten labels in `ticks.cho` (`label_log`), the pivot in `lib/plot/by.cho`. `tests/plot_log_test.cho` has 12 `cancho test` cases (85 + 21 + 15 + 12 in the four files).

**Measured.** The claim of section 33 holds: for a table of 1, 10, 100, 1000 the y labels are `1 10 100 1000`, and in the text chart the point at 100 and the `--hline 10` marker lie on the rows of their ticks; in the svg the labels are at y = 360, 245.33, 130.67 and 16 for a plot area from 12 to 356 (three equal decades of 114.67). A band from 10 to 100 fills the rows from the tick 100 down to the tick 10.

**Found while writing the tests, not changed:** the widening of the range to whole exponents in `axis.extent` only matters when all the values are equal (a single decade, 10 to 100, and not 1 to 100): for any other range, `enclose` with a step of whole exponents gives the same axis. It is kept because the single-decade rule is the stated one and has its test.

**Mutants.** 52 single-line mutants of the new code (`label_log`, the log part of `axis.cho`, the transform and refusal in `chart.cho`, all of `by.cho`): 48 killed, 4 survive, all equivalent:

- `x < 0 && x >= -6` to `x <= 0 && ...` in `label_log`: x = 0 is answered by the branch before.
- `ac[8] == 1` to `ac[8] != 0` in `extent`: `ac[8]` is 0 or 1.
- `if b == a` to `b <= a`: `b` is never below `a` there.
- `seen[g1] != m` to `seen[g1] < m`: a group with more rows than the first is refused in the pass before, so only fewer are left.

The first run killed 35 of 52; the 13 real gaps (a second series; either end of a band, and the transform of a band; the single decade; the row limit of `--by` on both sides; a missing x or y column; a row too many whose x is 0) each have a test now. Not measured: `--logy` against a plot of the same data made in another tool.

**Gallery.** `logby`: two runs on a log axis, from `site/data/converge.csv` (a small hand-written example of two solvers, said so on the page; not a measurement of any solver).

**Still open:** `--by` with groups that have different x values (needs a per-series x in the drawing code), horizontal bars, a staircase ECDF, and the trace of `opt` (section 22) once `opt` prints it.
