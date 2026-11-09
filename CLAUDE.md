# CLAUDE.md -- cancho-plot

Design before code: each verb gets a section in `docs/design.md` before its implementation, and every claim in it is either measured (with the command that
measures it) or marked as a choice or open.

- **Agent-first, like cancho-table, cancho-ml, cancho-stats and cancho-opt.** Data on standard input (CSV, TSV or JSON lines, as `table` writes them), the plot on standard
  output. An error is data: JSON on standard error with a stable `plot.<name>` rule tag, exit status 2 and a repair. No payload is ever logged.
- **Byte-stable.** The same input and flags give the same bytes. No clock, no random, no float formatting that depends on a platform.
- **The oracle is the text.** There is no gnuplot on the development machine (checked 2026-11-09); the gates compare against hand-computed geometry (ticks, scales, path
  data) and against the `--term dumb` rendering, which is exact. A comparison with gnuplot is added only when one is measured, in the section that makes the claim.
- **No source file over 2,000 lines. Every refusal has a rule tag. No input reaches a panic.**
- **Gates are written before the code they judge and must be able to fail** (mutants of the program that a gate has to kill).
- **Measured claims only.** A claim found false is corrected in place, in the document that made it.
- Licence EUPL-1.2, copyright Alpibru S.L. Commit trailer `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`; PRs stay draft until the maintainer says merge; no
  force-push to main.
