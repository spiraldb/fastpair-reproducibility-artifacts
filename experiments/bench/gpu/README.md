# GPU bench sources (snapshots)

Read-only copies of files in the frozen harness **`github.com/mprammer/vortex` @ `mp/fastpair`** (a single flattened commit, `9b4714c2a`). The canonical build clones that tree and builds it; these files'
`#include` paths are relative to its `benchmarks/onpair-bench/`, so they do **not** compile standalone.

- `e2e_scan.cu` — the end-to-end **decode→scan** bench (#28). Reuses the shipped split-read
  decode kernel + a vectorized (uint4 SWAR) rare-string scan; times decode, scan, decode→scan
  end-to-end, and the PCIe H2D of the decompressed vs compressed column; validates against a CPU
  reference decode + match count. Build (inside the Vortex tree): `nvcc -O3 -arch=native
  -std=c++17 e2e_scan.cu -o e2e_scan`. Run: `./e2e_scan <dump.e2ebin> [needle] [iters]`. The
  input dump is produced by `ONPAIR_DUMP_E2E=<path>` on the decode path (see the fork's `benchmarks/onpair-bench/README.md` §3).
  A predicate-selectivity sweep over this same bench (one decoded column, many `LIKE` needles, rare→common)
  is defined in [`../../../results/e2e/PREDICATE_SWEEP.md`](../../../results/e2e/PREDICATE_SWEEP.md) — pending execution.
- `nvcomp_hw_bench.cu` — the hardware Decompression Engine baseline (Blackwell). nvCOMP
  Deflate algo 5/0 + LZ4, `backend=HARDWARE`, fed the identical uncompressed bytes OnPair decodes.
- `onpair_shmem_4tpt_split8read.cu` — the shipped decode kernel `e2e_scan` reuses (the
  request-reducing split-read variant). The full OnPair kernel family lives in the Vortex tree at
  `vortex-cuda/kernels/src/`; the canonical build compiles all of it via `cargo build --features cuda`.
