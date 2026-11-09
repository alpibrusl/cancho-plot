# cancho-plot: design

Written 2026-11-09, before any code (`CLAUDE.md`). Every claim is **[measured]** with its command, a **[choice]**, or **[open]**. Nothing is built.

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
