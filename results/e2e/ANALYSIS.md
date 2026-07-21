# End-to-end: does the decode win survive a real consuming operator? (#28)

The paper times decode in isolation. This experiment answers the fair reviewer question --
*does query-part overhead eat the speedup once an operator consumes the decoded bytes?* -- with a
**substring scan over the entire decoded column**. We anchor on a rare, near-unique needle: it
makes the operator touch every decoded byte (a full pass, no pruning), and being unique it gives a
byte-exact match count that validates the decode. On the throughput axis the rare needle is the
*lightest* hand-off, not the worst -- the full selectivity sweep
([`PREDICATE_SWEEP.md`](PREDICATE_SWEEP.md)) traces e2e overhead from +22% here up to 845% on a
ubiquitous predicate, all of it scan-side predicate-evaluation work the query would pay under any
decoder (decode stays constant). "Heaviest hand-off" holds only in the bytes-touched sense: every
substring scan reads the whole column regardless of selectivity.

Bench: `experiments/bench/gpu/e2e_scan.cu` (reuses the shipped split-read decode kernel + a
vectorized uint4 SWAR scan), B300, rev `6ee03c1d8` (49174a3a6 decode lineage + the e2e bench),
1 GB sample, min-of-200 CUDA-event timing. Validated against a CPU reference decode + match count.
Raw: `e2e_clickbench_url.json`, `e2e_synthetic_url.json`.

## ClickBench URL (the real headline column), B300

| stage | time | rate |
|---|---|---|
| OnPair decode (alone) | 0.99 ms | **1009 GB/s** (reproduces the eval) |
| substring scan (alone, whole column) | 0.21 ms | **4720 GB/s** (HBM-bandwidth-bound) |
| **decode → scan end-to-end** | **1.21 ms** | **830 GB/s** (**+22%** over decode alone) |
| PCIe H2D of the *decompressed* column (1 GB) | 17.98 ms | 55.6 GB/s |
| PCIe H2D of the *compressed* column (234 MB) | 4.21 ms | (4.3× less data) |
| CPU decode (1 core) | 362 ms | 2.76 GB/s |

The needle is **unique** (`cpu_matches == gpu_matches == 1`) -- a genuinely selective filter,
byte-exact against the CPU reference.

## What it shows

1. **The operator is nearly free at this anchor.** Adding a full-column substring scan for the rare
   needle costs only **+22%** over decode alone, because the decoded bytes are already in HBM -- the
   scan runs at 4.7 TB/s and never leaves the chip. Overhead grows with selectivity (the sweep), but
   the decode rate is fixed -- the growth is predicate-evaluation work, not a hand-off tax.

2. **On-device decode beats moving the data.** Merely transferring the *decompressed* column over
   PCIe (18.0 ms) is **14.9×** the time to decode it from scratch on the GPU and scan it (1.21 ms).
   Decompressing on the GPU avoids the round-trip that a CPU-decode path cannot.

3. **End to end vs a CPU-decode baseline.** To scan on the GPU you either ship the compressed
   column and decode on-device (4.2 + 1.0 ms staging) or decode on the CPU and ship the decompressed
   column (362 + 18 ms). The full GPU-native pipeline is **70×** faster (5.4 ms vs 380 ms); the same
   scan follows both, so the gap is the decode + transfer, not the operator.

## Synthetic URL (no-download cross-check)

decode 1548 GB/s, scan 1181 GB/s, e2e 671 GB/s, PCIe-decompressed/decode+scan **12.0×**,
byte-exact (999,256 matches). Corroborates the story. Its larger e2e overhead (+131%) is because
the synthetic decode is *so* fast (1548 GB/s, a 879-entry dictionary) that a fixed HBM scan pass is
a bigger relative fraction -- the scan rate itself (1.2 TB/s) is healthy.

## Method note

The scan kernel went through three fixes worth recording (they are the paper's own lessons in
miniature): a byte-wise scan is **L1-request-bound** (~24-44 GB/s -- exactly the bottleneck FastPair
is about), so it loads 16 bytes per uint4 request and SWAR-tests them in registers; and an
unconditional per-thread `atomicAdd` serialized ~62 M threads on one counter (scan time scaled with
thread count, not bytes), so only the rare matching threads touch it. With both, the scan is a clean
HBM-bandwidth pass.
