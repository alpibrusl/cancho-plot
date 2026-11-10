#!/bin/sh
# The gate: CANCHO=<compiler> [MUTANTS=1] scripts/check.sh
# Checks the effect rows, builds `plot`, runs the tests written in cancho (`cancho test`), checks the format and the size of every source (no file over 2,000 lines), runs the four checks, and with MUTANTS=1 kills the mutants of the three that have them.
set -eu
: "${CANCHO:?set CANCHO to the compiler cancho.toml pins}"
here=$(cd "$(dirname "$0")/.." && pwd)
cd "$here"
mkdir -p build
"$CANCHO" check lib/plot/*.cho tools/plot/main.cho --std
"$CANCHO" build --bin plot >/dev/null
"$CANCHO" fmt --check lib tools tests
for f in lib/plot/*.cho tools/plot/main.cho tests/plot_test.cho tests/plot_cases_test.cho tests/plot_curve_test.cho; do
  [ "$(wc -l < "$f")" -le 2000 ] || { echo "FAIL: $f is over 2000 lines" >&2; exit 1; }
done
for t in tests/plot_test.cho tests/plot_cases_test.cho tests/plot_curve_test.cho; do
  "$CANCHO" test lib/plot/*.cho "$t" --std
done
export PLOT="$here/build/plot"
for g in ticks dumb svg; do
  if [ -n "${MUTANTS:-}" ]; then python3 scripts/check_$g.py --mutants; else python3 scripts/check_$g.py; fi
done
python3 scripts/check_site.py
echo "gate: ok"
