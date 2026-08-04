#!/usr/bin/env bash
# experiments/verify.sh -- one command to reproduce the paper's data artifacts.
#
# Regenerates every data-driven figure from the committed results/ (no GPU, no cloud,
# no benchmark re-run) and then re-derives every headline number and asserts it against
# the paper's stated value. Exits nonzero if any figure fails to build or any number
# fails to re-derive. Run from anywhere:
#
#   bash experiments/verify.sh           # or: make verify
#
# Requires `uv` (https://docs.astral.sh/uv/); each figure script is PEP-723 self-contained.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# The figures the paper \includegraphics, rebuilt from results/. fig_hierarchy is a code-drawn
# schematic (no results dependency) but it has a script, so it rebuilds too. Output name in
# parens where it differs (fig_crossstack writes fig_crossstack_strip.pdf).
LIVE_FIGS=(
  # the 12 figures in the main paper. fig_sota also ASSERTS its own claim: it exits nonzero
  # if any FastPair mark fails to clear the same-device baseline frontier, so a data change
  # that broke the dominance claim fails this run rather than shipping quietly.
  fig_teaser fig_sota fig_crossarch fig_sota_cpu fig_scaling fig_stagecost fig_costsurface
  fig_gatherwidth fig_ablation fig_compressibility fig_hierarchy fig_offtrade
  # extended-version figures (CPU deep-dive + per-dataset breakdown), regenerated
  # for completeness; not referenced in the main paper
  fig_crossstack fig_bitsweep fig_cputma fig_b300_datasets
)

command -v uv >/dev/null 2>&1 || { echo "FATAL: need 'uv' (https://docs.astral.sh/uv/)"; exit 2; }

echo "== regenerating ${#LIVE_FIGS[@]} figures from results/ =="
figfail=0
for f in "${LIVE_FIGS[@]}"; do
  if uv run "figures/$f.py" >/tmp/verify_$f.log 2>&1; then
    echo "  ok   $f"
  else
    echo "  FAIL $f  (see /tmp/verify_$f.log)"; tail -3 /tmp/verify_$f.log | sed 's/^/        /'
    figfail=$((figfail+1))
  fi
done

echo
echo "== re-deriving headline numbers =="
uv run experiments/validate.py
valrc=$?

echo
if [ "$figfail" = 0 ] && [ "$valrc" = 0 ]; then
  echo "VERIFY OK -- all figures rebuilt and all headline numbers re-derive from committed data."
  exit 0
fi
echo "VERIFY FAILED -- figures_failed=$figfail validate_rc=$valrc"
exit 1
