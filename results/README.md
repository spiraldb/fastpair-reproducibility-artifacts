# FastPair raw evaluation results

> Authoritative provenance and reproduction live in [`../experiments/`](../experiments):
> [`MANIFEST.md`](../experiments/MANIFEST.md) maps each result to its box, revision, config,
> reduction, and figure; [`METHODOLOGY.md`](../experiments/METHODOLOGY.md) states the conventions;
> and `verify.sh` (or `make verify`) rebuilds the figures and re-derives the headline numbers in one
> command. This file is the guide to the `results/` directory itself: the fleet, what is measured,
> the corpus caveats, and the JSON/CSV schema. Where this file and `MANIFEST.md` ever differ, trust
> `MANIFEST.md`.

These are the first-party measurement artifacts behind the evaluation, recorded so collaborators can
regenerate and extend the figures directly from source data. Every number in the paper traces to
these files, and the JSON carries the full per-kernel breakdown, not just the headline cell, so new
plots can be built without re-running a GPU job.

## The evaluation fleet

The paper evaluates four GPU architectures, one representative card each, with the B300 as the
canonical card, since the complete locked-clock sweep, the full NCU cost surface, and the hardware
Decompression Engine head-to-head all run there. Two memory technologies are covered: HBM
(A100/H100/B300) and GDDR6 (L40S).

| Dir | GPU | Arch | Mem peak | Cloud / region | Driver / CUDA | Date |
|-----|-----|------|---------:|----------------|---------------|------|
| `a100/` | A100-SXM4-40GB | Ampere, sm_80 | 1.56 TB/s HBM2 | Lambda, us-east-1 | 570.148 / 12.8 | 2026-06-05 |
| `l40s/`, `l40s-ncu/` | L40S | Ada Lovelace, sm_89 | 0.86 TB/s GDDR6 | Lambda | 12.8–13.0 / 570–580\* | 2026-06-26 |
| `h100/`, `h100-ncu/` | H100-SXM5 80 GB | Hopper, sm_90 | 3.35 TB/s HBM3 | Nebius, eu-north1 | 580.126 / 13.0 | 2026-06-08 |
| `b300/`, `b300-ncu/` | B300 SXM6 | Blackwell, sm_103 | 8.0 TB/s HBM3e | Nebius | 580.159 / 13.0 | 2026-06-25 |

\* The L40S driver and CUDA version were not archived for that leg (see `l40s/run-env.txt`); they
fall within the campaign's CUDA 12.8–13.0 / 570–580 range.

Retained as raw only (superseded, in no figure): `gh200/`, a redundant second Hopper within noise of
the H100, and `b200/` with `b200-ncu/`, the earlier Blackwell superseded by the B300's complete
locked sweep and four-arch NCU. `common.py`'s `GPUS` list is `a100, l40s, h100, b300`; nothing live
reads `gh200/` or `b200*/`.

## What is measured

GPU decode is kernel-only (codes, dictionary, and offsets pre-staged in HBM), byte-exact validated
against the CPU decoder (`--gpu-validate`), at bits 12 and 16, over 1000 MB whole-column chunks, 100
timed iterations, reduced to the min (see `METHODOLOGY.md`). The `FAST=0` legs add the nvCOMP
software Zstd path and the naive thread-per-row reference. The binary is `onpair-chunk-bench
--features cuda` from the Vortex tree; the early A100 and GH200 legs are branch `ji/onpair-gpu` at
`fe4a84d65`, later legs `mp/fastpair`, and the decode kernels are byte-identical across
the lineage (see `MANIFEST.md`).

### Corpus-provenance caveats

Two evaluation columns are reproduced public stand-ins, not the OnPair paper's original corpora, so
their numbers supersede and differ from older carried values:
- `synthetic` `url` is a deterministic ClickBench-style URL corpus (10M rows, seed 123) generated
  in-pipeline by `onpair-chunk-bench gen-synth-urls`. It compresses about 9.8x and is the fastest
  high-cardinality cell. It is not the old `onpair_cuda` micro-bench corpus.
- `book-reviews` `text` is the public Amazon-Reviews-2023 *Books* review bodies (McAuley Lab, UCSD),
  a roughly 1.2 GB sample, not OnPair's original non-public book-reviews. `amazon-movies` and
  `amazon-electronics` are the *Movies_and_TV* and *Electronics* categories of the same corpus. See
  [`../experiments/data/fetch.md`](../experiments/data/fetch.md).

## The other measurement families

| Path | What it is | Backs |
|---|---|---|
| `b300/onpair_nvcomp_hw.json` | the hardware Decompression Engine (Blackwell-only): Deflate-hi/-fast and LZ4, 256 KiB chunks, fed the identical bytes OnPair decodes, 16 columns | `fig:teaser`, `fig:payoff`, the DE multiple (2.4–4.6x) |
| `ncu-costsurface.csv` | the NSight Compute cost surface across four architectures (a100/l40s/h100/b300), per-pipe Speed-of-Light percentage of peak | `fig:costsurface`, `tab:bottleneck`, the cache-request-bound claim |
| `{b300,h100,l40s,b200}-ncu/` | the per-arch raw NCU `*_details.csv` that `extract_costsurface.py` reduces into `ncu-costsurface.csv`; `b200-ncu/` is retained raw | source for `ncu-costsurface.csv` |
| `e2e/` | end-to-end decode then scan on the B300, the operator hand-off | the figure-less §6 result and `fig:e2e_sweep`; `ANALYSIS.md` |
| `iaa/` | the Intel IAA accelerator aggregate versus FastPair-CPU on Sapphire Rapids | the §6 accelerator comparison; `ANALYSIS.md` |
| `cpu-sweep*/`, `cpu-bitsweep/`, `cpu-sota/`, `cpu-tma/` | the ten-generation CPU decode sweep (fixed-stride versus variable-stride) | `fig:cpufield`, `fig:compressibility`, and the extended-version CPU figures |

The cost surface is cache-request bound, not bandwidth- or compute-bound. On every GPU-filling cell a
cache pipe saturates while DRAM (at most 22% of peak) and SM compute (at most 38%) trail far behind.
Which cache pipe binds is architecture-dependent: the per-SM L1/TEX on Blackwell (92%), the
device-wide L2 on Hopper (88%). `validate.py` asserts that the cache pipe leads DRAM and SM by 45 or
more points on all four arches. (A100 and GH200 NCU was `RmProfilingAdminOnly`-blocked on Lambda; the
A100 row was captured later on a GCP profiling box, see `MACHINES.md`.)

## Cross-box reproducibility (spot-checks)

- The H100 (Nebius eu-north1, 2026-06-08, rev `550c3c3ca`, driver 580 / CUDA 13.0) reproduces the
  earlier Lambda H100 batch (rev `fe4a84d65`, driver 570 / 12.8) to about 1% on every shared cell,
  since decode is kernel-only and the toolchain bump does not move throughput.
- The B300 DE re-measure reproduced the committed DE to within 0.4% on the 6 overlap columns once the
  two missing Amazon DE rows were added (2026-06-27, rev `49174a3a6`).
- The superseded B200 rerun reproduced its own piecemeal predecessor to about 2%; both remain in git
  history.

## Schema

`onpair_summary_<dataset>.json` is an array of cells, one per (column, bits). Each cell carries
`dataset_id, column, bits, rows, sample_bytes, in_memory_bytes, on_disk_bytes, mem_ratio,
disk_ratio, decode_gib_s` (CPU), and a `gpu` object:

- `best_kernel` / `best_decode_gib_s` is the best over the whole kernel family per cell. On a few
  high-throughput cells `best_kernel` can be a byte-exact `*_ablate*` instrumentation build that
  edges the shipped kernel by under 0.2%. The figures and `validate.py` use `common.best_shipped()`,
  which excludes any `*ablate*` name and any kernel that failed byte-validation, so paper numbers
  take the best shipped kernel.
- `auto_kernel` / `auto_decode_gib_s` is what the shipped `pick_auto_kernel` selector actually picks.
- `kernels[]` is every kernel timed, with `decode_gib_s`, `decode_ns_iters` (the raw per-iteration
  timings; the figures reduce to `decoded_bytes / min(ns)`), `applicable`, and `verified`
  (byte-exact). It includes the `_ablate_*` proxies, which are non-byte-exact by design and back only
  the stage-cost figure.
- `nvcomp_zstd[]` is nvCOMP software Zstd (several configs, with `raw_bytes` and `decode_ms_iters`).
  `nvcomp_zstd_hw` self-reports `supported:false` on Blackwell, since the engine does Deflate and
  LZ4, not Zstd; the hardware DE lives in `onpair_nvcomp_hw.json`.
- `h2d_gib_s`, `whole_decompress_gib_s` are the PCIe transfer and transfer-bound end-to-end rates.
  `frac_le8`, `dict_mean_len`, `small_dict`, `distinct_codes` are the dictionary profile the selector
  dispatches on.

`onpair_nvcomp_hw.json` is an array, one entry per column: `dataset_id, column, raw_bytes,
chunk_bytes, codecs{DEFLATE-hi, DEFLATE-fast, LZ4}`, each `{ratio, compress_gib_s, decode_gib_s}`,
plus `best_codec / best_decode_gib_s / best_ratio`. It comes from `bench/gpu/nvcomp_hw_bench.cu` with
`backend=HARDWARE`, fed the exact uncompressed bytes OnPair decodes.

Each directory's `run-env.txt` records the GPU, memory, compute capability, driver, CPU, and
timestamp for that run (ephemeral host identifiers are redacted). The CPU families carry
`cpu-env.txt` / `machine.meta` per generation; see [`MANIFEST.md`](../experiments/MANIFEST.md) for
the full map.
