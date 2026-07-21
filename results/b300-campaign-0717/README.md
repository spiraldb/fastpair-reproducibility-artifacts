# b300-campaign-0717 — OP-cluster + fresh baselines (2026-07-17)

Single-session B300 campaign that measured the **output-positioning offset trade-off**
(OP-cluster) and refreshed the SM/DE baselines, alongside a base-throughput reconfirmation.

- **Box:** NVIDIA B300 SXM6 AC (compute cap 10.3, 275 GB, driver 580), Nebius uk-south1
  preemptible. See `run-env.txt`.
- **Rev:** `5e10231c5` on `mp/fastpair` (registry-driven `dump_columns.py` +
  `op_gpu_regen.cu` OP2 kernel + `ONPAIR_OFFSET_COST` hook).
- **Clocks:** boost/unlocked (headline convention, matches canonical `results/b300`).
- **Run:** value-ordered (novel legs first). The main run hit the 3 h `JOB_TIMEOUT` during the
  trailing chunk-size steelman; that leg + OP1 were recovered by separate focused runs (see the
  per-file †notes) and folded here, so the OP-cluster + all campaign legs are now complete in this dir.

## Files

| File | Experiment | Headline |
|---|---|---|
| `offset_cost.jsonl` (26 = 13 cols × 2 presets) | OP4 store: sidecar size (raw u64/u32 + BtrBlocks) + host gen time, per chunk | stored **0.37–1.08%** of compressed (median ~0.6%); raw-u64 2.5–7.3%; gen ~1–2.5 Gtok/s |
| `op_gpu_regen.jsonl` (13) | OP2 regen chunk_offsets on GPU (scan + CUB), byte-exact | **+15–19%** decode time on throughput-bound cols (dbtext launch-bound 94–151%, not throughput results) |
| `op1_row_decode.jsonl` (13) †OP1-run | OP1 row-partition decode: reuse the free per-row code offsets, generate output offsets on device (thread-per-row), byte-exact | **13/13 byte-exact**; decode 24–321 GB/s (median 98): wins on small/uniform rows (l_shipinstruct 321, l_comment 170, clickbench 143) but CRATERS on long text rows (fineweb 24.5 @ 3084 B/row, wiki 25.5) — the thread-per-row load-imbalance signature |
| `e2e_v2.jsonl` (13) | decode → in-HBM substring scan (rare-needle worst case) | e2e ≈ decode + ~22% |
| `gans_bitcomp.jsonl` (13) | nvCOMP SM codecs (gANS/Bitcomp) on the same bytes OnPair decodes | behind at equal-or-better ratio |
| `onpair_nvcomp_hw.json` (13) | hardware DE (Deflate/LZ4/Snappy), chunk-swept, same bytes | span 14–658 GB/s, median 215; ClickBench URL 418 (reproduces canonical `b300`) |
| `onpair_summary_*.json` (7) | base OnPair throughput sweep, bits 12+16, FAST=0 | reconfirmation of the canonical `b300` rates |
| `onpair_chunk_sweep.json` (130 = 13 cols × 5 sizes × 2 bits) †chunksweep-run | OnPair decode throughput vs chunk size (steelman: "1000 MB headline ≠ production chunk") | near-headline at 1000/100 MB, cliff below ~10 MB (launch-bound): ClickBench URL b16 **1087→1039→588→103→10** GB/s over 1000→100→10→1→0.1 MB |
| `onpair_metas.tar.gz` | per-cell meta.json backstop | — |
| `logs/` | build + run logs (nvcc, run.py, hooks) | provenance / debug |

**†OP1-run provenance:** `op1_row_decode.jsonl` is from a SEPARATE focused run (`b300-op1chunk`,
2026-07-18, rev `7a408d961`, same B300 box class), added here to keep the OP-cluster (OP1/OP2/OP4)
together for analysis. OP1's first on-box nvcc compile was clean; terra+sol reviewed + re-verified.

**†chunksweep-run provenance:** `onpair_chunk_sweep*.json` is from a SEPARATE focused run
(`b300-chunksweep`, 2026-07-18, rev `7a408d961`) after fixing a leg-selector bug (the campaign
now sources `.job_secrets`, so `CAMPAIGN_LEGS` takes effect — the earlier runs silently ran the
full set and the timeout kept cutting this leg). `chunksweep_census.txt` = that run's census.

## OP-cluster verdict (from this data)

Store (OP4) wins decisively: **~0.5–1% space ≪ ~15–19% decode time** to regenerate. OP2 is
the fallback for store-averse deployments. OP1 (reuse `code_offsets` / row-partition kernel)
is unbuilt — small-row niche only. OP3 (CPU regen + stream) ruled out (host gen ≈ 50 ms/GB ≫
~1 ms GPU decode). The stored sidecar is monotonic → BtrBlocks delta-compresses it ~5–7× over
raw u64. Note: measured OP2 (~15–19%) is above the ~10% first estimate.

## Data-accuracy flag

The fresh DE run shows **Snappy edging LZ4** as best codec on 5 columns (wiki, fineweb, email,
yago, hex) — the paper's §6 "Snappy … never leads" is contradicted by our own data (within
noise; soften to "Snappy tracks LZ4").

Not folded into figures yet — raw drop for review. Authoritative provenance index is
`experiments/MANIFEST.md`.
