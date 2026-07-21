# METHODOLOGY — how every number is measured and reduced

Frozen so the paper's numbers are reproducible and comparable. [`MANIFEST.md`](MANIFEST.md)
maps each result to its box/rev/config; this file is the *conventions* those runs share.
[`validate.py`](validate.py) enforces the reductions below by importing `figures/common.py`
(one implementation, no drift).

## Throughput and reduction
- **Unit: GB/s, decimal (10⁹ B/s).** `decoded_bytes / time_seconds`. Where a run stored only a
  GiB/s scalar (the DE, older cells), convert ×`2³⁰/10⁹` = 1.073741824 (`common.GIB_TO_GB`).
- **Reduction: minimum over iterations** (best-of-N). The raw per-iteration timings are logged
  and the figure-gen takes `decoded_bytes / min(decode_ns_iters)` (bytes/ns ≡ GB/s). Min is the
  microbenchmark convention: it reports the achievable rate with scheduling/boost noise removed.
  GPU decode uses 100 iters; the e2e bench uses min-of-200 (CUDA events).
- **Best shipped kernel.** Each cell runs the whole tokens-per-thread kernel family; the reported
  rate is the best kernel that (a) is byte-exact verified and (b) is **not** an `*ablate*`
  instrumentation build. (Ablate builds skip a decode stage and are not byte-exact; they back the
  stage-cost figure only.) `common.best_shipped()` is the single source of this rule.

## What is timed
- **GPU decode is kernel-only:** inputs (codes, dictionary, offsets) pre-staged in HBM; the timed
  region is the decode kernel(s). This isolates decode from staging/PCIe — and is the scope the §6
  *Limitations* note names. The end-to-end experiment (#28, `e2e_scan.cu`) is the companion that
  times decode→operator with the decoded bytes consumed in HBM, plus the PCIe baseline.
- **Byte-exact validation:** every GPU/IAA decode is checked against a CPU reference decode of the
  same input (`--gpu-validate`; the IAA and e2e benches verify in-process). A cell that fails
  validation is excluded from `best_shipped`.

## Sampling and configuration
- **Sample:** 1 GB of the column's UTF-8 bytes (`--sample-bytes 1e9`), concatenated with no
  separators (matches the encoder); whole-column 1000 MB chunks.
- **Dictionary width:** bits 12 (4096 entries) and bits 16 (65536); the paper reports BOTH presets as
  configurations of one codec (tab:datasets carries both ratios; its §6.2 gives per-preset DE
  multiples). `fig_teaser` plots each column's better preset and its caption says so;
  `fig_sota` plots both presets separately.
- **GPU clocks:** the canonical `results/b300` sweep runs **default boost** clocks — the headline,
  as the paper discloses; `results/b300-locked` is the clock-pinned sibling (`CLOCK_LOCK=1`),
  under ~7.6% lower on the deterministic columns. NCU controls
  its own clocks; the %-of-peak metrics are clock-independent regardless.

## Baselines
- **Hardware DE (Blackwell):** nvCOMP `backend=HARDWARE`, Deflate algo 5 (max ratio) + algo 0
  (fast) + LZ4, 256 KiB chunks, fed the **identical** uncompressed bytes OnPair decodes (same
  column, same ~1 GB cap). Reported = best DE codec per column.
- **Software Zstd:** nvCOMP software path, several levels; reported = best level per cell. The
  "6–372×" range is best-FastPair / best-Zstd per column on B300 (max over bits, independently).
- **CPU:** `target-cpu=native`, pinned to physical cores (one logical CPU each), 256 MB working
  set. CPU rate is an amortized mean over ~0.7 s of decoding (vs the GPU min-of-100) — a
  conservative reduction for the CPU side. Competitors (FSST, Zstd, LZ4, zlib) are stock library
  decoders, single core.
- **IAA:** Intel QPL hardware path, software-compressed blocks (256 KB, dynamic Huffman) decoded on
  the IAA engines; min over ≥3 passes; run as root with a shared WQ per device (8×128),
  block_on_fault=1, mlock'd buffers; byte-exact per cell. T-thread sweep to find the saturation
  point; T=1 reproduces the per-engine number.
- **NCU cost surface:** NSight Compute `--set full`, per-pipe Speed-of-Light %-of-peak (the valid,
  clock-independent signal — NCU "Duration" is instrumented-replay time, not throughput), mean over
  up to 16 kernel launches; classified GPU-filling vs underfilled.

## Provenance integrity
- The decode kernels are byte-identical across `fe4a84d65 → 550c3c3ca → 49174a3a6` (the revs that
  produced the committed results; e2e from `6ee03c1d8`) and in the frozen harness
  `github.com/mprammer/vortex` @ `ba16fad7f`; only the bench harness/datasets/e2e bench changed. So
  throughput is comparable across all GPU runs even where a `run-env.txt` records a different lineage
  rev (see the B300 note in MANIFEST).
- Cross-box reproducibility is spot-checked: the H100 Nebius rerun reproduced the Lambda H100 to
  ~1%; the B300 DE re-measure reproduced the committed DE to ≤0.4% on the 6 overlap columns.
