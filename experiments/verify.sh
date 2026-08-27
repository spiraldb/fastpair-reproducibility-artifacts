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

# THE FIGURE LIST IS DERIVED FROM THE PAPER, NOT MAINTAINED BESIDE IT. This was a hand-written
# list, and it drifted until it named the RETIRED figure family: of the nine figures the paper
# prints, this loop rebuilt two. The consequence was not cosmetic -- figures/fig_perf_real.py
# carries the per-column dominance assertion behind Section 5's central claim ("no baseline
# configuration reaches those rates at an equal or better compression ratio") and it was never
# executed, while fig_sota, whose assertion this file's comment advertised, is not in the paper at
# all. Coverage was exactly inverted. So: ask the paper.
PAPER_DIR="${PAPER_DIR:-$HOME/repos/onpair-gpu-paper}"
# bash 3.2 (the macOS default) has no `mapfile`, and a subshell pipeline cannot populate an array
# in the parent. Build it with a plain loop over a temp file instead.
paper_figs(){
  grep -ho 'includegraphics\[[^]]*\]{[^}]*}' "$PAPER_DIR"/sections/*.tex "$PAPER_DIR"/main.tex 2>/dev/null \
    | sed -e 's/.*{//' -e 's/}$//' -e 's#.*/##' -e 's/\.pdf$//' | sort -u
}
LIVE_FIGS=()
MISSING_GEN=()
while read -r f; do
  [ -n "$f" ] || continue
  if [ -f "figures/$f.py" ]; then LIVE_FIGS+=("$f"); else MISSING_GEN+=("$f"); fi
done <<EOF
$(paper_figs)
EOF
if [ "${#LIVE_FIGS[@]}" -eq 0 ]; then
  echo "FATAL: derived no figures from $PAPER_DIR -- set PAPER_DIR to the paper repo"; exit 2
fi
# A figure the paper prints with no generator here is reported, not silently skipped: a code-drawn
# schematic is legitimate, a missing generator for a data figure is a hole.
for f in "${MISSING_GEN[@]:-}"; do
  [ -n "$f" ] && echo "  note: $f is printed by the paper and has no generator here"
done
echo "== figure set derived from the paper: ${LIVE_FIGS[*]} =="

command -v uv >/dev/null 2>&1 || { echo "FATAL: need 'uv' (https://docs.astral.sh/uv/)"; exit 2; }

# tab:datasets is the paper's one hand-maintained table. It has no figure to regenerate,
# so it is checked instead: every printed cell is re-derived from results/ and compared with
# what the paper prints. It drifted before this existed (2026-08-15: five cells, one of them
# a four-machine mean printed under a "B300 run" caption), which is exactly the failure a
# generator-less table invites.
# NOT tab_datasets.py --check. That gate passed green while the paper carried an FSST-12 ratio on
# the wrong basis, because it validates a HARDCODED SNAPSHOT of the retired TEN-column table
# against the retired ten-column corpus -- and its snapshot even holds the CORRECT value for the
# cell the paper gets wrong (l_shipinstruct FSST-12: 11.4 in the snapshot, 3.4 in the paper). It
# had no contact with the current table at all, and its green tick is what made the gap invisible.
# The live fifteen-column table comes from tab_datasets_suite.py, so that is what gets checked.
echo "== regenerating tab:datasets rows from ${CLAIM_LEG:-results/suite-paper-20260821} =="
if ! uv run figures/tab_datasets_suite.py > /tmp/tab_datasets.regen 2>/tmp/tab_datasets.err; then
  echo "FATAL: could not regenerate the tab:datasets rows"; cat /tmp/tab_datasets.err; exit 1
fi
# Compare against the rows the paper actually prints. Extracted by row label rather than by
# position, so reordering the table is not a failure and a changed number is.
if ! uv run experiments/check_tab_datasets.py /tmp/tab_datasets.regen; then
  echo "FATAL: tab:datasets in the paper disagrees with what the data produces"; exit 1
fi

# Sections 2-4 assert dozens of numbers that were derived in ad-hoc sessions and typed into
# prose. paper_claims.py re-derives each from committed data and fails on drift, the same
# contract tab:datasets has. It caught four stale values on its first run, one of them an
# understatement by half (a preset penalty quoted as 28% whose true maximum is 51%), and two
# more that came from a reducer keyed on dataset_id where two ClickBench columns collide.
# The paper cites GENERATED MACROS for these numbers rather than transcribing them, so the check
# is not "does prose match data" -- it is "is the committed macro file what the data produces".
# Transcription is the step that kept going stale; removing it removes the failure mode.
# THE LEG IS NAMED, not defaulted. paper_claims.py still defaults to results/campaign-20260820,
# the pre-suite campaign, and its unread-leg guard then refuses to derive anything -- so this step
# exited non-zero for every caller of `make verify` until the leg was named here. Name it, and a
# future campaign changes one line rather than being papered over with --allow-unconsumed.
CLAIM_LEG="${CLAIM_LEG:-results/suite-paper-20260821}"
echo "== regenerating the Section 3-5 claim macros from ${CLAIM_LEG} =="
CLAIMS_TEX="${CLAIMS_TEX:-$HOME/repos/onpair-gpu-paper/sections/generated/claims.tex}"
uv run experiments/paper_claims.py --suite-root "$CLAIM_LEG" --emit-tex /tmp/claims.regen.tex || {
  echo "FATAL: could not derive the claim macros"; exit 1; }
if [ -f "$CLAIMS_TEX" ] && ! diff -q "$CLAIMS_TEX" /tmp/claims.regen.tex >/dev/null; then
  echo "FATAL: $CLAIMS_TEX is stale. Diff:"
  diff "$CLAIMS_TEX" /tmp/claims.regen.tex || true
  exit 1
fi
echo "== re-deriving the declared Section 3-5 claims =="
if ! uv run experiments/paper_claims.py --suite-root "$CLAIM_LEG" --check; then
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
