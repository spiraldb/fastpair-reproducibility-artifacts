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
  fig_teaser fig_sota fig_crossarch fig_sota_cpu fig_stagecost fig_costsurface
  fig_gatherwidth fig_ablation fig_compressibility fig_hierarchy fig_offtrade
  # appendix A. Added 2026-08-20: it was already shipping in the paper while being neither
  # rebuilt here nor covered by validate.py, so nothing protected its numbers from drift.
  fig_freqbars
  # extended-version figures (CPU deep-dive), regenerated for completeness; not referenced
  # in the main paper
  fig_crossstack fig_bitsweep fig_cputma
)
# RETIRED 2026-08-04, superseded by fig_crossarch: fig_b300_datasets (per-column B300 bars
# against the DE) and fig_scaling (three GPUs, one column). Both were earlier attempts at the
# per-column cross-architecture view that fig_crossarch now carries for all four GPUs and all
# ten columns, and neither is referenced by the paper. The scripts stay in figures/ as history;
# they are no longer rebuilt, so they are no longer held to current data.

command -v uv >/dev/null 2>&1 || { echo "FATAL: need 'uv' (https://docs.astral.sh/uv/)"; exit 2; }

# tab:datasets is the paper's one hand-maintained table. It has no figure to regenerate,
# so it is checked instead: every printed cell is re-derived from results/ and compared with
# what the paper prints. It drifted before this existed (2026-08-15: five cells, one of them
# a four-machine mean printed under a "B300 run" caption), which is exactly the failure a
# generator-less table invites.
echo "== checking tab:datasets against results/ =="
if ! uv run figures/tab_datasets.py --check; then
  echo "FATAL: tab:datasets disagrees with results/ (see above)"
  exit 1
fi

# Sections 2-4 assert dozens of numbers that were derived in ad-hoc sessions and typed into
# prose. paper_claims.py re-derives each from committed data and fails on drift, the same
# contract tab:datasets has. It caught four stale values on its first run, one of them an
# understatement by half (a preset penalty quoted as 28% whose true maximum is 51%), and two
# more that came from a reducer keyed on dataset_id where two ClickBench columns collide.
# The paper cites GENERATED MACROS for these numbers rather than transcribing them, so the check
# is not "does prose match data" -- it is "is the committed macro file what the data produces".
# Transcription is the step that kept going stale; removing it removes the failure mode.
echo "== regenerating the Section 3-4 claim macros from results/ =="
CLAIMS_TEX="${CLAIMS_TEX:-$HOME/repos/onpair-gpu-paper/sections/generated/claims.tex}"
uv run experiments/paper_claims.py --emit-tex /tmp/claims.regen.tex || {
  echo "FATAL: could not derive the claim macros"; exit 1; }
if [ -f "$CLAIMS_TEX" ] && ! diff -q "$CLAIMS_TEX" /tmp/claims.regen.tex >/dev/null; then
  echo "FATAL: $CLAIMS_TEX is stale. Diff:"
  diff "$CLAIMS_TEX" /tmp/claims.regen.tex || true
  exit 1
fi
echo "== re-deriving the declared Section 3-4 claims =="
if ! uv run experiments/paper_claims.py --check; then
  echo "FATAL: a Section 3-4 claim does not re-derive (see above)"
  exit 1
fi

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
