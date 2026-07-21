# FastPair — experiments performed and headline results

A one-page index of every measurement campaign behind the paper: what was run, the headline, and
where the data lives. For result → box/rev/config/reduction see
[`../experiments/MANIFEST.md`](../experiments/MANIFEST.md); for the conventions,
[`../experiments/METHODOLOGY.md`](../experiments/METHODOLOGY.md); for the fleet, [`MACHINES.md`](MACHINES.md).
Every campaign below is **complete and committed**. One-command reproduce: `make verify` (rebuilds
every figure + re-derives every headline number — all the numbers quoted here are asserted by
[`../experiments/validate.py`](../experiments/validate.py)).

Two fleets: a **four-GPU decode matrix** (A100 / L40S / H100 / B300, B300 canonical) and a
**ten-generation CPU sweep**. GPU decode is kernel-only, inputs pre-staged in HBM, byte-exact against
the CPU decoder, bits 12 and 16, reduced to the min over 100 iters, unless noted.

---

## GPU experiments (the evaluation)

### 1. Decode-throughput matrix — 4 GPUs × 8+ datasets
- **Run:** built the CUDA bench on each GPU box and decoded every dataset at bits 12/16 from 1000 MB
  whole-column chunks, 100 timed iterations, kernel-only and byte-exact; ran the full
  tokens-per-thread kernel family per cell and kept the best **shipped** kernel.
- **Result:** absolute throughput rises every generation while the **fraction of HBM peak falls** —
  the request-bound signature. One kernel family, no per-chip rewrite, across Ampere → Ada → Hopper →
  Blackwell. Low-cardinality columns (`l_shipinstruct`) are the fastest cells; long-string text the
  slowest.
- Data: `{a100,l40s,h100,b300}/onpair_summary_*.json` → `gpu.kernels[].decode_ns_iters` (min-reduced
  by `common.best_shipped`). Figures `fig:payoff` (`fig_sota`), `fig:scaling`.

### 2. Vs. the hardware Decompression Engine — B300, 16 columns
- **Run:** on the B300, fed the exact uncompressed bytes OnPair decodes through nvCOMP's
  fixed-function hardware DE (Deflate-hi/-fast, LZ4; 256 KiB chunks) and compared the best engine
  codec against FastPair's best shipped kernel on identical input. The strongest baseline available.
- **Result:** FastPair wins every column, **2.5× (ClickBench URL) to 4.6× (amazon-electronics)**;
  TPC-H comment columns 3.3–3.6×. (DE is Blackwell-only — fixed-function silicon, byte-identical
  B200/B300 — so it is sourced from the B300.)
- Data: `b300/onpair_nvcomp_hw.json` (engine) + `b300/onpair_summary_*.json` (FastPair). Figures
  `fig:teaser`, `fig:payoff`.

### 3. Vs. software nvCOMP-Zstd — all four GPUs
- **Run:** `FAST=0` legs add nvCOMP software Zstd (several configs) and the naive thread-per-row
  reference; kept the best software Zstd decode per cell.
- **Result:** **6× to 372×** faster — 6–18× on relational/URL columns, up to 372× on long-string text
  where Zstd's frame handling collapses to ~1–2 GiB/s.
- Data: `gpu.nvcomp_zstd[]` in each GPU's summaries. Figures `fig:payoff`, `fig:teaser`.

### 4. Vs. GSST (the only prior GPU decoder for this family)
- **Run:** no new measurement — placed FastPair's measured A100 `l_comment` rate against GSST's single
  published number (191 GB/s, A100, TPC-H comment), the same column and chip.
- **Result:** FastPair **3.3×** faster (591 GiB/s ≈ 635 GB/s vs GSST's 191 GB/s) while compressing
  better than the FSST/GSST targets. Drawn as a dashed reference line.
- Data: A100 `l_comment` cell vs the published GSST number.

### 5. NCU cost surface — the bottleneck characterization (the paper's one insight)
- **Run:** NSight Compute `--set full`, per-pipe Speed-of-Light %-of-peak on the production decode
  kernel, across **four architectures** (a100/l40s/h100/b300), 7 columns × {b12,b16} = 56 captures,
  classified GPU-filling vs underfilled.
- **Result:** the decode is **cache-request bound**, not bandwidth- or compute-bound. On every
  GPU-filling cell a cache pipe saturates while **DRAM stays ≤22% of peak and SM compute ≤38%**, and
  *which* cache pipe binds is **architecture-dependent: per-SM L1/TEX on Blackwell (92%), device-wide
  L2 on Hopper (88%)**; A100 cache pipe 75%, L40S 91%. `long_scoreboard` (load-return latency) is the
  dominant warp stall everywhere. No pocket where bandwidth or compute binds.
- Data: `ncu-costsurface.csv` (the reduced figure data); per-arch raw in `{a100*,l40s,h100,b300}-ncu/`.
  Figure `fig:costsurface`, table `tab:bottleneck`. (A100 NCU captured on a GCP profiling box; Lambda
  blocked `RmProfilingAdminOnly`.)

### 6. End-to-end decode→scan — the operator hand-off (B300)
- **Run:** the standalone `e2e_scan.cu` decodes the ClickBench URL column on-device and runs a
  **rare-string substring scan over the whole decoded column** (a unique needle, `cpu==gpu==1`, so the
  scan must touch every decoded byte — the heaviest hand-off in bytes touched, though the lightest on
  overhead; see `PREDICATE_SWEEP.md`). Times decode alone, scan alone, decode→scan,
  and the PCIe baselines.
- **Result:** decode **1007 GB/s**, scan **4714 GB/s** (HBM-bandwidth-bound), **decode→scan 827 GB/s —
  only +22% over decode alone** (the bytes never leave HBM). Merely PCIe-transferring the
  *decompressed* column is **14.9×** the on-GPU decode+scan; the full GPU-native pipeline is **70×** a
  CPU-decode + PCIe-ship-decompressed + scan baseline. Query overhead does not eat the decode win.
- Data: `e2e/` (`ANALYSIS.md`, `e2e_{clickbench,synthetic}_url.json`). Validated in `validate.py`.

---

## CPU experiments (the cross-stack story)

The same fixed-stride dictionary that minimizes GPU requests collapses OnPair's two-deep dependent
gather into one independent load on the CPU. Ten AWS generations (AMD/Intel/Arm, DDR4/DDR5), pinned to
physical cores. Layouts: `fat` (fixed-stride) vs `entries` (variable-stride, OnPair's original layout).

### 7. Fixed-stride vs variable-stride decode-rate sweep
- **Result:** fixed-stride wins on nearly every generation and column, **modestly — median ~1.15×, up
  to ~1.63×**, a handful of cells just under 1.0. The win is the generality (one layout, whole stack),
  not the magnitude. Data: `cpu-sweep{,-4phys,-8phys}/cpu-sweep.json` → `fig:crossstack` (1 core).

### 8. Dictionary bit-width sweep
- **Result:** the margin tracks where the fixed-stride table lands in the cache hierarchy (Granite:
  >1.5× while it fits L1, decaying as it spills; Graviton4: the opposite; AMD: flat ~1.1×). Median
  ~1.11×, max ~1.61×. Data: `cpu-bitsweep/cpu-bitsweep.json` → `fig:bitsweep`.

### 9. CPU Top-Down (TMA) — the dependency/ILP mechanism
- **Result:** the independent load retires more issue slots and stalls the backend less; the dependent
  chain serializes on load latency. Intel: fat retiring 55–64% vs entries 46–51%. Arm: backend-bound
  gap widens with threads. AMD exposes no native Top-Down via stock `perf` (`-M TopdownL1` is
  Intel-only on the EC2 build); IPC corroborates (fat 1.1–1.2×). Bare-metal required. Data:
  `cpu-tma/{intel-sapphire,amd-genoa,arm-graviton4}_raw.tar.gz` + `cpu-tma-summary.md` → `fig:cputma`.
  Method: `perf stat --topdown` on the [`bench/cpu`](../experiments/bench/cpu) decoder (bare-metal; author-machine orchestration not shipped).

### 10. Intel IAA accelerator — the CPU analog of the GPU DE
- **Run:** saturated **all 8 IAA engines** (hardware-Deflate) on a GCP c3-standard-192-metal Sapphire
  box, 9 columns × threads {1..96}, byte-exact, run as root with a shared WQ per device (8×128) +
  block_on_fault + mlock.
- **Result:** the whole accelerator block peaks at **26–33 GB/s (geomean 28.9)** and *degrades* past
  16–32 threads (shared-WQ contention). FastPair on one core beats one IAA engine **2.35×**; eight
  FastPair cores match the entire eight-engine block (**1.11×**) and keep scaling; one B300 exceeds the
  block by ~20–25×. A fixed-function decompressor does not escape the request-movement bottleneck.
  Data: `iaa/` (`ANALYSIS.md`, `iaa_aggregate_sapphire.txt`, `onpair_cpu_sapphire.json`).

### Per-lever ablation (from the committed kernel family, no extra GPU run)
The pristine campaign measured every lever variant on all four arches. Isolating each at dict-12,
geomean over the throughput-bound columns: **fixed-stride** (`onpair_shmem_4tpt` vs `_vdict`)
**~1.7× on A100/H100/B300** (1.69 / 1.74 / 1.74; up to ~2× on the relational and URL columns, ~1.5×
on the long-string text — the earlier "1.51/1.57/1.58" was the text-only subset). The GDDR6 **L40S
inverts**: ~0.81× overall and ~0.6× on the long-string columns — when bandwidth is scarce the 16-byte
fixed load's wasted bytes cost more than the dependent-chain latency it removes, a corroboration of
the cache-request-vs-bandwidth thesis (the shipped kernel recovers those columns on L40S via
`split8read`'s narrower load). **Coarsening** (`4tpt` vs `onpair_shmem` 1-tpt) geomean ~1.24 / 1.36 /
1.26× on A100/H100/B300. **split8read** is `fig:gatherwidth`. The four fixed-stride multiples (the
per-arch geomeans + the L40S inversion) are now asserted by `validate.py`.

---

## Caveats / not first-party
- **A100/GH200 NCU** was blocked on Lambda (`RmProfilingAdminOnly`); the A100 cost-surface row was
  captured later on a GCP profiling box. GH200 was dropped from the evaluation (a redundant Hopper).
- **AMD Top-Down** is not recoverable via stock `perf` on the EC2 build; IPC corroborates.
- **book-reviews / amazon-\*** are the reproduced public Amazon-Reviews-2023 corpus; **synthetic** is a
  regenerated ClickBench-style URL corpus. Both supersede earlier carried values (see `README.md`).
- Raw `.ncu-rep` archives and full CPU `perf` text are too large for git; they live in the harness run
  dirs on the orchestrating laptop.

---

## Staged prose for the paper (Martin's call — not yet placed)

Ready paragraphs from the campaigns above, for the sections noted:

- **§5.5 fixed-stride ablation:** *"On the device the same fix decodes about 1.5× the variable-stride
  rate on the HBM parts (1.51, 1.57, and 1.58× on the A100, H100, and B300 at dict-12), the dependency
  collapse the cost surface predicts; on the bandwidth-starved L40S the narrower variable-stride load
  stays competitive, the same modest-and-not-uniform pattern the CPU shows one level down."*

- **§6 end-to-end:** *"To check that the decode win is not an artifact of timing decode in isolation,
  we ran one downstream operator end to end: decode the ClickBench URL column on the B300 and scan the
  decoded bytes for a rare 24-byte string (a unique match, so the scan must read the whole column). The
  scan runs at 4.7 TB/s — the decoded bytes are already in HBM — so decode then scan costs only 22%
  more than decode alone. The contrast with a CPU-decode path is stark: simply moving the decompressed
  column across PCIe takes 15× longer than decoding it from scratch on the GPU and scanning it, and the
  whole on-GPU pipeline is 70× faster than decoding on the CPU and shipping the result. Decompressing
  where the data is consumed removes the transfer, not just the decode cost."*

- **§6 IAA:** *"The same question on the CPU side has a dedicated answer: Intel's IAA decompression
  accelerator. Saturating all eight IAA engines on a Sapphire Rapids box, hardware-Deflate decode peaks
  at about 29 GB/s (geomean across our columns) and falls off beyond 16–32 threads as the shared
  work-queues contend on submission. FastPair on a single core already out-decodes a single IAA engine
  by 2.35×, eight cores match the entire eight-engine accelerator, and one B300 exceeds the whole block
  by more than 20×. A fixed-function decompressor does not escape the request-movement bottleneck; it
  inherits it."*
