# MANIFEST — every result, where it came from, what consumes it

The authoritative result→provenance map. For each measurement artifact under `results/`:
the bench source, the code revision, the box, the run config, the reduction, and which
figure/number it backs. Reproduction methodology is in [`METHODOLOGY.md`](METHODOLOGY.md);
re-derivation of the headline numbers is automated in [`validate.py`](validate.py).

Code lives in two pinned places: the **Vortex** harness — the frozen snapshot
**`github.com/mprammer/vortex` @ `mp/fastpair`** (a single flattened commit, `9b4714c2a`; GPU decode kernels +
the encoder that produces the bench inputs) — and the standalone benches snapshotted under
[`bench/`](bench). The decode kernels are **byte-identical** across the revision lineage
`fe4a84d65 → 550c3c3ca → 49174a3a6 → 62336963e` that produced the committed results (e2e results
from `6ee03c1d8`); only the bench harness changed (raw per-iteration logging + min reduction;
dataset adds; the e2e bench; the 2026-06-27 **gold re-run** — DE chunk-size sweep + zero-perf
kernel hardening — at `62336963e`; the occurrence-weighted `dict_mean_len` fix at `4edc9a1a6`;
the Snappy DE leg at `ba16fad7f`, canonical CPU bench at `175f504`), and `mp/fastpair` carries
those same kernels. So decode throughput is comparable
across every GPU run regardless of which of these revs its `run-env.txt` records.

## GPU decode matrix (the evaluation)

| Result | Box | Rev | Config | Reduction | Consumed by |
|---|---|---|---|---|---|
| `a100/onpair_summary_*.json` | A100-SXM4-40GB, Lambda, 2026-06-05 | fe4a84d65 (+gap-fill 550c3c3ca) | bits 12+16, 1000 MB chunk, 100 iters, kernel-only, `--gpu-validate` | best **shipped** kernel = decoded_bytes / min(decode_ns_iters) | `fig:payoff`, `fig:scaling`, GSST check |
| `l40s/onpair_summary_*.json` | L40S (Ada, GDDR6), Lambda, 2026-06-26 | 49174a3a6 lineage | same | same | `fig:payoff` (GDDR6 leg) |
| `h100/onpair_summary_*.json` | H100 80GB HBM3, Nebius eu-north1, 2026-06-08 | 550c3c3ca | `FAST=0` (adds software Zstd + naive ref), all 8 datasets | same | `fig:payoff`, `fig:scaling`, software multiple |
| `b300/onpair_summary_*.json` | B300 SXM6 (sm_103), Nebius, 2026-06-27 | 62336963e (gold) †| `FAST=0`, **unlocked/boost clocks** (headline), all datasets | same | `fig:payoff`, `fig:teaser`, `fig:scaling`, `fig:gatherwidth`, `fig:stagecost`, DE/software multiples — **the canonical GPU** |
| `b300-locked/onpair_summary_*.json` | B300 SXM6, Nebius, 2026-06-27 | 62336963e (gold) | `FAST=0`, **locked clocks** (tput mode), all datasets | same | extended-version, clock-pinned sibling of `b300` |
| `b200/`, `gh200/` | B200 Nebius / GH200 Lambda | 550c3c3ca / fe4a84d65 | superseded | — | retained raw only (not in figures) |

† The 2026-06-27 **gold re-run** staged fork `62336963e` (gold bench + zero-perf kernel hardening;
decode kernels byte-identical to the 49174a3a6 lineage). `results/b300` is the **unlocked/boost**
headline; `results/b300-locked` is the clock-pinned sibling for the extended version. DE rows in
`b300/onpair_nvcomp_hw.json` are from the same rev with the chunk-size sweep (best per column):
each column entry retains its full per-chunk sweep (32\,KiB–512\,KiB) in a `chunk_sweep` field, and
`best_decode_gib_s` is the max over it (the field `de_map()` reads).

## Hardware Decompression Engine (Blackwell-only)

| Result | Box | Rev | Config | Consumed by |
|---|---|---|---|---|
| `b300/onpair_nvcomp_hw.json` (16 cols) | B300, Nebius uk-south1, 2026-06-27 | 62336963e (gold) | `nvcomp_hw_bench.cu`, backend=HARDWARE, Deflate algo 5/0 + LZ4, **chunk-size sweep (best per column)**, fed the **identical** uncompressed bytes OnPair decodes | `fig:payoff`, `fig:teaser`, DE multiple (**2.4–4.6×**) |

Source: [`bench/gpu/nvcomp_hw_bench.cu`](bench/gpu/nvcomp_hw_bench.cu). DE is fixed-function
silicon, byte-identical B200/B300, so `de_map()` (in `figures/common.py`) sources it from B300.

## NCU cost surface (the bottleneck characterization)

**PROVENANCE SPLIT (2026-07-05/06).** The original captures below profiled the BASE reference
kernel (`onpair_u64`: shared mem 0, block 64), not the shipped family — the job set
`ONPAIR_FAST=1` only for materialization, so `ncu -c 16` with no `-k` filter grabbed the first
launches (`GPU_KERNELS[0]` = Ref). They are retained as a valid profile *of the base kernel*;
do not cite them as shipped-kernel facts. The `*-ncu-v2/` recapture (rev `ba16fad7f`, locked
clocks, exact per-cell `-k`, CAPTURE-VERIFIED 56/56: only `onpair_shmem_4tpt{,_split8read}`
present, block 512, static shared mem 33.28 KB/block) is the shipped-kernel source for all
paper bottleneck claims.

| Result | Box(es) | Config | Consumed by |
|---|---|---|---|
| `ncu-costsurface-v2.csv` | L40S + H100 + B300 + A100, 2026-07-05 locked recapture (run dirs `~/agents/harness/runs/pristine-*-locked-20260705-*`) | NSight Compute `--set full`, **shipped** decode kernels, per-pipe Speed-of-Light %-of-peak | `fig:costsurface`, `tab:bottleneck`, the "cache-request bound" claim (post-recapture revision) |
| `ncu-stalls-v2.csv` | same recapture | warp-stall shares, % of warp cycles per issued instruction | §5.2 stall evidence + `tab:stallmix` shipped column (reference column: the base-kernel `*-ncu/` raw via the same script with suffix `-ncu`) |
| `figures/out/fig_roofline.pdf` | derived (no new capture) | request-rate roofline: per-cell prediction from `*-ncu-v2` (`figures/fig_roofline_v2.py` model) vs `best_shipped`, one fitted per-arch clock constant | `fig:roofline`, the §5.2 prediction claim (B300/H100/A100 median rel err 1.7/3.8/8.0%; L40S non-predictive) |
| `{l40s,h100,b300,a100}-ncu-v2/ncu_costsurface_*_{details,raw}.csv` | per-arch raw | `--set full`, 16 launches/cell, mean | source for both v2 CSVs (via `figures/extract_costsurface.py` / `figures/extract_stalls.py`) |
| `ncu-costsurface.csv` | B300 + H100 + L40S + A100 (GCP profiling box) | `--set full`, **base reference kernel** (see provenance split above) | base-kernel (`onpair_u64`) profile only; the before/after stall contrast |
| `{b300,h100,l40s,b200}-ncu/ncu_costsurface_*_details.csv` | per-arch raw, base kernel | `--set full`, 16 launches/cell, mean | source for `ncu-costsurface.csv` |

A100/GH200 NCU was `RmProfilingAdminOnly`-blocked on Lambda; the base-kernel A100 row in
`ncu-costsurface.csv` was captured later on a GCP profiling box, its raw archived off-repo (no
`a100-ncu/` dir). The v2 recapture has committed raw for all four arches, A100 included (GCP
`us-west4-b`). Columns: `arch,col,card,bits,l1tex,l2,dram,sm,l1hit,ld,st` (pipe columns are
%-of-peak). `validate.py` still asserts the base-kernel CSV's invariants (B300 L1/TEX 92%,
H100 L2 88%); a v2 invariant check should replace it when the paper's revised §5.2 numbers are
final — on v2 data the shipped kernel binds on L1/TEX (87–96%) on every HBM chip, and on the
L40S no pipe saturates (see the paper repo's `docs/notes/2026-07-06-ncu-v2-rederivation.md`).

## Drain ablation + targeted NCU captures (B300) — `results/b300-drain-e2e/`

One locked-clock B300 session (SM pinned to 2032 MHz, Nebius, 2026-07-06; rev `ba16fad7f`;
run dir `~/agents/harness/runs/b300-drain-e2e-20260706-210827`). `RESULTS.md` in the dir is
the session digest; NCU captures are `--set full`, 16 launches/cell, exact `-k`,
CAPTURE-VERIFIED.

| Result | Config | Consumed by |
|---|---|---|
| `onpair_summary_{clickbench,lship,pscmt,synthetic}.json` (+ `ncu_*_ablate_nodrain_*` captures) | drain ablation: `onpair_shmem` / `_4tpt` / `_4tpt_ablate` / `_4tpt_ablate_nodrain` per cell, min-of-100, kernel-only. The `_ablate*` builds are **diagnostic, not shipped**; `_nodrain` is **not byte-exact** (validation fails by construction) | §5.3 drain sentence + §4.2 — drain = **10–13% of ablate-baseline runtime** across the 5 cells (17.5–20.5% vs plain 4tpt) |
| `ncu_clickbench_URL_b12_onpair_shmem_{details,raw}.csv` + `..._onpair_shmem_4tpt_{details,raw}.csv` | occupancy pair on ClickBench URL b12 | §4.3/§6.4 — 1tpt **89.3%** achieved occupancy @ 32 reg/thread vs 4tpt **45.4%** @ 56 reg (50% theoretical) |
| `ncu_dbtext_ps_comment_b12_onpair_shmem_4tpt_b128o12_*` (+ plain `_4tpt` sibling) | launch-bound capture: dbtext ps_comment b12 (dict-only column) | §6.4 — b128o12 launches **492 blocks**, **19.4%** achieved occupancy: the grid can't fill the chip |
| `toolkit_*` (PTX/SASS + diffs, `toolkit_versions.txt`) + `e2e_tk_*.json` | nvcc 12.8 vs 13.0: PTX + SASS (per-toolkit AOT and fixed-ptxas13.0 JIT analogue) + e2e timing on ClickBench URL b12 | §6.1 disclosure — SASS **differs** 12.8 vs 13.0; 13.0 is **+1.4%** decode (761.2 → 771.5 GB/s) |

## CPU decode sweep (the cross-stack story)

| Result | Boxes | Source | Config | Consumed by |
|---|---|---|---|---|
| `cpu-sweep-4phys/cpu-sweep.json` (**gold**; `cpu-sweep/`, `-8phys/` are the older runs) | 10 AWS gens (AMD/Intel/Arm, DDR4/DDR5), bare-ish | [`bench/cpu/`](bench/cpu) @ 175f504 (`target-cpu=native`) | fixed-stride (`fat`) vs variable-stride (`entries`) decode, 256 MB working set, 1/4/8 phys cores, per-pass raw → min-derived | `fig:crossstack` (1 core, extended), CPU fat/entries **1.15× median / 1.63× max** (validate) |
| `cpu-bitsweep/cpu-bitsweep.json` | same fleet | same | dict bit-width 9→16 | `fig:bitsweep` |
| `cpu-sota/*.json` | same fleet | same | compression ratios (codec-independent) | `fig:compressibility`, `fig:cpufield` |
| `cpu-tma/*_raw.tar.gz` | bare-metal Intel Sapphire / AMD Genoa / Arm Graviton4 | [`bench/cpu/`](bench/cpu) under `perf stat --topdown` | `perf stat --topdown` + L2, fat vs entries, 1/4/8 threads | `fig:cputma` |

## IAA accelerator (the CPU analog of the GPU DE) — #29

| Result | Box | Source | Config | Consumed by |
|---|---|---|---|---|
| `iaa/iaa_aggregate_sapphire.txt` | GCP c3-standard-192-metal (Sapphire, 8 IAA engines), 2026-06-27 | [`bench/iaa/iaa_bench_mt.cpp`](bench/iaa/iaa_bench_mt.cpp) | all 8 engines, shared WQ 8×128, block_on_fault=1, **run as root**, mlock'd; 9 cols × threads {1..96}; min over ≥3 passes | IAA aggregate 28.9 GB/s geomean; `ANALYSIS.md` |
| `iaa/onpair_cpu_sapphire.json` | same box | [`bench/cpu/`](bench/cpu) | FastPair-CPU fat/entries, same columns | IAA comparison (FastPair 1-core 2.35× one engine; 8-core matches the block) |

Setup is reboot-requiring (intel_iommu scalable mode + idxd from `linux-modules-extra`); driven
by [`bench/iaa/iaa_drive.sh`](bench/iaa/iaa_drive.sh) + [`iaa_mt_setup_run.sh`](bench/iaa/iaa_mt_setup_run.sh).

## End-to-end decode→scan (the operator hand-off) — #28

| Result | Box | Rev | Source | Consumed by |
|---|---|---|---|---|
| `e2e/e2e_{clickbench,synthetic}_url.json` | B300, Nebius uk-south1, 2026-06-27 | 6ee03c1d8 (49174a3a6 decode lineage + e2e bench) | [`bench/gpu/e2e_scan.cu`](bench/gpu/e2e_scan.cu) | §6.8 operator hand-off. ClickBench URL: decode 1007 GB/s, scan 4714 GB/s, e2e 827 GB/s (+22%), PCIe-decompressed/decode+scan **14.9×**, full pipeline vs CPU-decode baseline **70×**; needle unique (byte-exact). `ANALYSIS.md` |
| `e2e/sweep/sweep_*.json` (10 needles + `sweep_rare.json` anchor) | B300, Nebius uk-south1, 2026-06-27 | 6ee03c1d8 | [`bench/gpu/e2e_scan.cu`](bench/gpu/e2e_scan.cu), the same decoded ClickBench URL dump swept over needles rare→ubiquitous, min-of-200 | archived predicate-selectivity sweep (rare→ubiquitous needle), superseded in the paper by `fig:offtrade`; 3 `validate.py` cross-over checks |
| `b300-drain-e2e/ncu_e2e_scan_needle_{details,raw}.csv` (+ same-session `e2e_b300_clickbench_url_b12.json`) | B300, locked 2032 MHz, 2026-07-06 | ba16fad7f | NCU `--set full` on the `scan_needle` kernel (ClickBench URL b12 dump, repro-repo `e2e_scan.cu`) | §6.7 scan characterization — DRAM **42.8%** of peak, long_scoreboard **48.5%** of warp cycles, L1/TEX 21.0% |

`e2e_scan.cu` reuses the shipped split-read decode kernel + a rare-string scan; validated against
a CPU reference decode + match count. Inputs dumped from the encoder via `ONPAIR_DUMP_E2E` on the
decode path (the frozen harness fork; see its `benchmarks/onpair-bench/README.md` §3, end-to-end);
the dumps are stashed locally so a scan-kernel tweak re-runs in ~3 min (stage dump + nvcc + run).

## Offsets / materialization trade-off — `results/b300-offtrade/` (`fig:offtrade`, §6.8)

| Result | Box | Rev | Source | Consumed by |
|---|---|---|---|---|
| `b300-offtrade/run{1..4}_url.json` | B300 SXM6, Nebius uk-south1 (preemptible), 2026-07-21 | `9b4714c2a` (flattened; run revs `b0bc051d4` / `9afe81125` / `9b1ee137c` / `8305d35be`) | [`offsets_tradeoff.cu`](https://github.com/mprammer/vortex/blob/mp/fastpair/benchmarks/onpair-bench/offsets_tradeoff.cu) | **`fig:offtrade` (§6.8)** + 5 `validate.py` checks. ClickBench URL (12.25M rows) at FastPair-16, Q20 substring count under an incoming filter of selectivity `m`; four decode strategies (dense over stored offsets, regenerate-on-GPU OP2, late-materialization, early-materialization) relative to dense. Runs 1–3 supply the plotted m-grid (1.0→0.03); run4 adds the sub-0.03 reference tail. Every cell byte-exact + count==oracle; min-of-200. |

The offset-strategy trade-off measures what a pushed-down filter buys against the filter-agnostic
dense decode: dense stays cheapest to ~20% selectivity, early materialization wins below, and the
late-materialization prototype never wins. Driver: `offsets_tradeoff.cu` in the frozen harness
(`mp/fastpair`); the `m`-set is the `mlist` literal in the driver.

## FSST recipe port (the generality check) — `results/a100-fsst/`

| Result | Box | Rev | Config | Consumed by |
|---|---|---|---|---|
| `fsst_scan_tpch_{l_comment,l_shipinstruct}.json` | A100-SXM4-40GB, locked 1410 MHz, 2026-07-06 | branch `mp/fsst-recipe` @ `24719f925` (pushed to the fork) | naive `fsst.cu` vs recipe `fsst_4tpt.cu`, 100 iters, raw per-iteration ns retained, **byte-exact both** | §6.3 generality sentence + §5.2/§8 scope — recipe **327.7 GB/s** on TPC-H l_comment = **1.72×** GSST's published 191 (naive `fsst.cu` 138.6); l_shipinstruct **570.1** |
| `fastpair_summary_{tpch_lcomment,dbtext}.json` | same box, same run | same | shipped FastPair family on the same cells (incl. the bonus dbtext summary), GiB/s | same-chip FastPair reference for the FSST comparison |

**DISCLOSE:** the recipe port pre-stages a `group_in_off` side table (~539 MB on l_comment)
untimed, like the chunk offsets. `fsst_scan` reports decimal GB/s (decoded bytes / kernel s /
1e9), directly comparable to GSST's 191. Blob provenance: `fsstbin_manifest.txt`;
clocks/driver: `run-env.txt`.

## OP-cluster + fresh baselines (B300) — `results/b300-campaign-0717/`

One-session B300 campaign (Nebius uk-south1 preemptible, boost clocks) at rev `5e10231c5`
(`mp/fastpair`: registry `dump_columns.py` + `op_gpu_regen.cu` OP2 + `ONPAIR_OFFSET_COST`
hook). Value-ordered; the trailing chunk-size steelman was cut by the 3 h timeout (absent by design).
See the dir `README.md` for the full file table.

| Result | Experiment | Reduction | Headline / consumed by |
|---|---|---|---|
| `offset_cost.jsonl` | OP4 store: offset sidecar size + host gen time, per chunk (`ONPAIR_OFFSET_COST`) | per-chunk raw | stored **0.37–1.08%** of compressed (median ~0.6%); raw-u64 2.5–7.3% → the disclosed footprint-with-sidecar config |
| `op_gpu_regen.jsonl` | OP2 regen chunk_offsets on GPU (scan+CUB), byte-exact (`op_gpu_regen.cu`) | min-of-200 | **+15–19%** decode time on throughput-bound cols (dbtext launch-bound 94–151%, excluded like other throughput claims) |
| `op1_row_decode.jsonl` †sep-run | OP1 row-partition decode: reuse free per-row code offsets + on-device output-offset scan, thread-per-row (`op1_row_decode.cu`, `ONPAIR_DUMP_OP1`) | min-of-200 | **13/13 byte-exact**; decode 24–321 GB/s (med 98) — wins small/uniform rows, craters on long text (fineweb/wiki ~25 @ 3–4.5 KB/row): the thread-per-row load-imbalance signature. †from run `b300-op1chunk` 2026-07-18 rev `7a408d961` |
| `e2e_v2.jsonl` | decode→in-HBM scan (rare needle) | min-of-200 | e2e ≈ decode + ~22% |
| `gans_bitcomp.jsonl` | nvCOMP SM codecs gANS/Bitcomp, same bytes (`nvcomp_sw_bench.cu`) | best-over-chunk-sweep | behind at equal-or-better ratio (§7 SM baseline) |
| `onpair_nvcomp_hw.json` | hardware DE, chunk-swept | best per column | 14–658 GB/s, median 215; ClickBench URL 418 — **reconfirms canonical `b300`** |
| `onpair_summary_*.json` (7) | base OnPair sweep, bits 12+16, FAST=0 | best shipped kernel | reconfirmation of canonical `b300` rates |
| `onpair_chunk_sweep.json` (130) †sep-run | OnPair decode throughput vs chunk size (5 sizes × 2 bits × 13 cols, FAST=1, 30 iters) | best kernel per cell | steelman: near-headline at 1000/100 MB, cliff <10 MB (launch-bound) — ClickBench URL b16 1087→1039→588→103→10 GB/s. †from run `b300-chunksweep` 2026-07-18 rev `7a408d961` |

OP-cluster verdict: **store (OP4) wins — ~0.5–1% space ≪ ~15–19% (OP2) regen time.** OP1 (row-partition,
now measured) is the zero-stored-metadata option but thread-per-row craters on long rows (fineweb/wiki
~25 GB/s), competitive only on small/uniform rows — a load-balanced kernel is future work. OP3 (CPU+stream)
ruled out (~50 ms/GB gen ≫ ~1 ms decode). Raw drop, not folded into figures. FLAG: fresh DE shows Snappy
edging LZ4 on 5 cols → soften §6 "Snappy never leads".

## Review-response E1 (batching) + E3 (drain counterfactual) — `results/b300-e1e3/`

One B300 session (Nebius uk-south1 preemptible, boost) at rev `f38924aea`
(`mp/onpair-drain-baseline` = campaign branch's fixed Unit-B batch bench + the E3
`onpair_shmem_4tpt_directstore` kernel). Byte-exact both. Answers content-review M2 + M3;
changes NO headline number (reported decode always uses the shipped staged coalesced drain;
`directstore` is a diagnostic, excluded from best-shipped selection). See the dir `README.md`.

| Result | Experiment | Reduction | Headline / consumed by |
|---|---|---|---|
| `onpair_summary_directstore_{clickbench,tpch-sf10}.json` | E3: byte-exact direct-store drain counterfactual (same gather+scan; per-byte scattered global stores vs the staged coalesced drain), both `verified:true` | best shipped = min(decode_ns_iters); `X = directstore/4tpt` | §5.2/§4.2 `tab:drain` — the staged drain is **1.8–3.3×** faster than the naive byte-exact alternative (write amplification, the write-side mirror of the gather's read amplification) |
| `batch_multidict.jsonl` | E1: batched many-small-row-group decode (239 ~4 MB independently-dicted RGs), 4 launch strategies, all byte-exact | min-of-100, aggregate GB/s | §6.4 launch-bound — streams/multidict recover **~2×** over naive sequential (tpch 413→901/890, ClickBench 453→916/876). Pilot scope (hardcoded 512-thread kernel, synthetic sliced corpus, whole-sequence makespan) |

## Not in git (too large; on the orchestrating laptop / regenerable)
- Raw `.ncu-rep` archives → `~/data/onpair-ncu-archive/`, `~/agents/harness/runs/`.
- Full CPU `perf` text → inside the `cpu-tma/*_raw.tar.gz`.
- E2E input dumps (~400 MB) → `~/data/onpair-e2e-dumps/` (regenerable from the frozen harness fork; see its `benchmarks/onpair-bench/README.md` §3).
- Datasets → see [`data/fetch.md`](data/fetch.md).
