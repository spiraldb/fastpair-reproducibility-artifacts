# results/b300-e1e3 — review-response experiments E1 (batching) + E3 (drain counterfactual)

One B300 session, **Nebius uk-south1 preemptible**, boost clocks, 2026-07-20. Rev
**`f38924aea`** (branch `mp/onpair-drain-baseline` = the campaign branch's fixed Unit-B
batch bench + the E3 direct-store kernel). GPU: **NVIDIA B300 SXM6 (sm_103)**, driver
580.159.04, CUDA 13.0, 275 GB. Launcher: `~/agents/harness/runs/launch-b300-e1e3-preempt.sh`
(on-box legs `leg_batch` + `leg_directstore` in `jobs/onpair-campaign.sh`,
`CAMPAIGN_LEGS="batch directstore"`). Both experiments are **byte-exact validated**.

**Provenance note:** `run-env.txt` records `vortex_rev: fe4a84d65` — this is the *informational
default* baked into `jobs/onpair-bench.sh` (`VORTEX_REV:-fe4a84d65`), NOT the rev actually run. The
staged tree is the git-archive of **`f38924aea`** (`STAGE_REV` in the launcher), which is what
carries the E1 `batch_decode.cu`/`onpair_shmem_4tpt_multidict.cu` and E3
`onpair_shmem_4tpt_directstore.cu` code; `fe4a84d65` does not. The decode kernels are byte-identical
across the lineage (see `experiments/MANIFEST.md`), so throughput is unaffected, but the env label is
stale. (Fix for future runs: have the campaign launcher pass `VORTEX_REV=$STAGE_REV` into the job.)

These two experiments answer content-review findings **M2** (deployability / launch-bound) and
**M3** (the drain needs a byte-exact counterfactual). Neither changes a headline number — the
paper's reported decode always uses the shipped staged, coalesced drain; `directstore` is a
diagnostic counterfactual, excluded from the "best shipped" selection.

## E3 — byte-exact direct-store drain counterfactual — `onpair_summary_directstore_*.json`

`onpair_shmem_4tpt_directstore` keeps the shipped kernel's gather + warp prefix-scan but writes
each token **directly to global memory, byte by byte** (per-lane, scattered, uncoalesced) instead
of staging to shared scratch and flushing an aligned `uint4` coalesced drain. Both are byte-exact
(`verified: true`). The summaries carry both `onpair_shmem_4tpt_directstore` and the shipped
`onpair_shmem_4tpt` per cell; the drain benefit is `X = 100*(directstore_ms/4tpt_ms - 1)`:

| Column | Preset | shipped 4tpt (ms) | directstore (ms) | slowdown |
|---|---|---:|---:|---:|
| ClickBench URL | FP-12 | 1.214 | 2.134 | 1.8× |
| ClickBench URL | FP-16 | 0.977 | 2.576 | 2.6× |
| TPC-H l_comment | FP-12 | 0.856 | 2.223 | 2.6× |
| TPC-H l_comment | FP-16 | 1.053 | 2.826 | 2.7× |
| TPC-H ps_comment | FP-12 | 0.736 | 2.396 | 3.3× |
| TPC-H ps_comment | FP-16 | 0.922 | 2.863 | 3.1× |

The staged, coalesced drain is **1.8–3.3× faster** than the naive byte-exact alternative: naive
per-byte global stores suffer write amplification (each byte store pulls a 32-byte sector), the
write-side mirror of the gather's read amplification. `directstore` uses zero shared memory (higher
occupancy ceiling), so the slowdown is despite an occupancy advantage — it is the write
amplification, not an occupancy artifact. Consumed by §5.2/§4.2 (`tab:drain`).

## E1 — batched many-small-row-group decode — `batch_multidict.jsonl`

A within-body pilot for the launch-bound caveat (§6.4): a file's worth of small row-groups (239
independently-dicted ~4 MB row-groups from a 1 GB sample), decoded four ways — N sequential
launches, N over K=8 streams, a CUDA graph, and one multi-dictionary grid. All four **byte-exact**.
Aggregate GB/s:

| Column | sequential | streams | CUDA graph | multidict |
|---|---:|---:|---:|---:|
| TPC-H l_comment | 413 | 901 | 528 | 890 |
| ClickBench URL | 453 | 916 | 539 | 876 |

Batching (streams or one-grid multidict) recovers **~2×** over naive per-row-group sequential
launches — recovering most of the 1000 MB single-chunk headline from the small-row-group cliff
(`onpair_chunk_sweep`, `b300-campaign-0717`). Claim scope: "batching **can** restore utilization,"
not a production-path result (hardcoded 512-thread `split8read`; whole-sequence makespan on a
synthetic sliced corpus). Consumed by §6.4.

## Files
- `onpair_summary_directstore_{clickbench,tpch-sf10}.json` — full per-kernel summaries (directstore + shipped 4tpt).
- `batch_multidict.jsonl` — one JSON record per column (the four launch strategies + byte-exact flags + n_row_groups).
- `run-env.txt`, `CAMPAIGN_CENSUS.txt`, `batch.log`, `directstore.runlog` — environment + run diagnostics.
