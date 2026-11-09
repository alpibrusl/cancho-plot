# cancho-plot

Plots as an agent-first command line, in [cancho](https://github.com/alpibrusl/cancho): the part of gnuplot that a report needs, built like its siblings
[cancho-table](https://github.com/alpibrusl/cancho-table) (`table`), [cancho-ml](https://github.com/alpibrusl/cancho-ml) (`ml`) and
[cancho-stats](https://github.com/alpibrusl/cancho-stats) (`stats`): one binary, data in on standard input, the plot out on standard output.

```
table --format csv ... | plot --x day --y net,margin --with lines --title "Net margin" > net.svg
table --format csv ... | plot --x day --y net --term dumb          # the same chart as text, for a terminal or a log
plot -c script.plot < data.csv                                       # a small gnuplot-like script: set, plot ... using 1:3 with lines
```

**Status.** Design only: `docs/design.md`. Nothing is built. Authority (planned): standard input and output, nothing else; no file, no network, no clock. Licence EUPL-1.2,
copyright Alpibru S.L.
