# `l40s-fsst12` — FSST-12 decoded by the shipped FastPair kernels

L40S (sm_89, GDDR6), Nebius eu-north1, 2026-08-12. Harness run `l40s-fsst12-20260812-225451`, vortex rev `2d909147f` (branch `mp/fsst12-bench`).

FSST-12 normalized into FastPair's decode ABI on the host (dense 12-bit codes unpacked to
`u16`, 8-byte symbols widened to 16-byte cells, per-code length table supplied) and decoded
by the **unmodified** shipped kernels. `fsst12_summary_*.json` are the FSST-12 cells;
`onpair_ref_*.json` are OnPair cells measured in the **same run on the same box**, so the two
codecs are compared without crossing sends.

- All 11 FSST-12 cells report `verified: true` (byte-exact against the CPU
  reference). `run_cell_fsst12` aborts a cell that fails validation rather than emitting a rate.
- **Two ratio fields.** `mem_ratio` is NATIVE: codes in FSST-12's own fixed 12-bit packing.
  `mem_ratio_container_matched` measures the code stream through the instrument OnPair's codes
  go through (BtrBlocks over a `u16` array). They agree to two decimals on the real text
  columns and diverge by up to 3.3x at low cardinality, where BtrBlocks bitpacks below 12 bits.
  Use the container-matched figure for codec-vs-codec claims against OnPair-in-Vortex.
- **Filenames are not scopes.** `run.py` writes one `summary.json` per invocation and the job
  snapshots it per dataset, so a file named for one dataset can contain cells for others. Key
  on each cell's own `dataset_id` / `column` / `bits` / `codec`. Verified free of duplicates.
- `codec` is `"fsst12"` or `"onpair"`. `figures/common.py:cell()` takes a `codec=` argument;
  records written before FSST-12 existed carry no `codec` key and default to OnPair.
