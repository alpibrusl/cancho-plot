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
