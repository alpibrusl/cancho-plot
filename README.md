# cancho-plot

Plots as an agent-first command line, in [cancho](https://github.com/alpibrusl/cancho): the part of gnuplot that a report needs, built like its siblings
[cancho-table](https://github.com/alpibrusl/cancho-table) (`table`), [cancho-ml](https://github.com/alpibrusl/cancho-ml) (`ml`) and
[cancho-stats](https://github.com/alpibrusl/cancho-stats) (`stats`): one binary, data in on standard input, the plot out on standard output.

```
table --format csv ... | plot --x day --y net,margin --with lines --title "Net margin" > net.svg
table --format csv ... | plot --x day --y net --term dumb          # the same chart as text, for a terminal or a log
plot -c script.plot < data.csv                                       # a small gnuplot-like script: set, plot ... using 1:3 with lines
```

**Status.** `plot ticks LO HI [N]` (section 10) and the text chart of points from CSV (`plot --x COL --y COL --term dumb`, section 12) are built and gated; the rest is design: `docs/design.md`.

```
cancho build lib/plot/num.cho lib/plot/ticks.cho lib/plot/csv.cho lib/plot/dumb.cho tools/plot/main.cho --std -o build/plot      # or: cancho build --bin plot
PLOT=build/plot python3 scripts/check_ticks.py [--mutants]                                      # --mutants needs CANCHO=the compiler
PLOT=build/plot python3 scripts/check_dumb.py [--mutants]
```

 Authority: arguments, standard input, standard output and standard error, nothing else; no file, no network, no clock. Licence EUPL-1.2,
copyright Alpibru S.L.
