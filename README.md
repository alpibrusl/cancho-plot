# cancho-plot

Plots as an agent-first command line, in [cancho](https://github.com/alpibrusl/cancho): the part of gnuplot that a report needs, built like its siblings
[cancho-table](https://github.com/alpibrusl/cancho-table) (`table`), [cancho-ml](https://github.com/alpibrusl/cancho-ml) (`ml`) and
[cancho-stats](https://github.com/alpibrusl/cancho-stats) (`stats`): one binary, data in on standard input, the plot out on standard output.

```
table --format csv ... | plot --x day --y net,margin --with lines --term svg --title "Net margin" > net.svg
table --format csv ... | plot --x day --y net --term dumb          # the same chart as text, for a terminal or a log (--with lines joins the points)
plot -c script.plot < data.csv                                       # a small gnuplot-like script: set, plot ... using 1:3 with lines
```

**Status.** `plot ticks LO HI [N]` (section 10) and charts from CSV on standard input, as points or lines, as text (`--term dumb`, sections 11 and 12) or as SVG (`--term svg`, sections 13 and 14), with markers (`--vline`, `--hline`), bands (`--band`), the diagonal (`--diag`), bars with text categories (`--with bars`) and error bars (`--yerr`), are built and gated; the rest is design: `docs/design.md`. The landing page, with a gallery of what the binary writes, is published at https://alpibrusl.github.io/cancho-plot/ (it is `site/index.html`, deployed by `.github/workflows/pages.yml`) (`python3 -m http.server --directory site`).

```
cancho build lib/plot/*.cho tools/plot/main.cho --std -o build/plot      # or: cancho build --bin plot
PLOT=build/plot python3 scripts/check_ticks.py [--mutants]                                      # --mutants needs CANCHO=the compiler
PLOT=build/plot python3 scripts/check_dumb.py [--mutants]
PLOT=build/plot python3 scripts/check_svg.py [--mutants]
PLOT=build/plot python3 scripts/check_site.py                                                   # the landing page is what the binary writes now
cancho test lib/plot/*.cho tests/plot_test.cho --std                                            # the tests (and tests/plot_cases_test.cho) written in cancho (docs/design.md section 18)
CANCHO=... [MUTANTS=1] scripts/check.sh                                                       # all of it
```

 Authority: arguments, standard input, standard output and standard error, nothing else; no file, no network, no clock. Licence EUPL-1.2,
copyright Alpibru S.L.
