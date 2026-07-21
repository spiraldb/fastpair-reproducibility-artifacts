# CPU multi-thread Top-Down — the dependency/ILP split on the silicon (1/4/8 threads)

First-party Linux-`perf` Top-Down of the OnPair decode hot loop, **fat** (fixed-stride, one
independent indexed load) vs **entries** (variable-stride, the published OnPair: a dependent
offset→bytes chain), swept across 1/4/8 threads on bare-metal boxes of three ISAs. Captured
2026-06-12. Each run is pinned via `taskset` to N physical cores on a single NUMA node, one logical
CPU per physical core (no SMT siblings), so the measurement is topology-clean. Bare-metal is
required: virtualized Nitro PMUs do not expose the Top-Down slots. Bench perf-mode spawns N worker
threads (`onpair-cpu-bench`, `ONPAIR_BENCH_PERF=layout:col:bits:threads`). Raw per-config output in
`{intel-sapphire,amd-genoa,arm-graviton4}_raw.tar.gz`.

## Reading

The split the single-thread runs found holds at 4 and 8 threads, on both ISAs that expose a native
Top-Down: the **fixed-stride layout retires more and stalls the backend less**, while the
**dependent gather is more backend-bound** (its offset→bytes chain serializes at load latency,
starving instruction-level parallelism). The throughput edge tracks it (≈1.2× on Intel, ≈1.3× on
Arm), and on Arm the backend-bound gap *widens* with thread count as the shared cache fills. AMD
exposes no native Top-Down through `perf --topdown` (it needs `-M TopdownL1`), but its IPC tells the
same story (fat ≈1.2× the entries IPC). The effect is clearest on the gather-dominated column
(`fineweb_text`, shown below); it is weaker on `synthetic_url`, where the gather is a smaller share
of the loop, the CPU analog of the GPU stage-cost migrating with the column.

## Intel Sapphire (c7i.metal-24xl) — full Top-Down, fineweb_text b12

| threads | fat retiring% | fat backend% | fat GiB/s | entries retiring% | entries backend% | entries GiB/s |
|--|--|--|--|--|--|--|
| 1 | 55.3 | 29.8 | 5.1 | 46.4 | 38.7 | 4.3 |
| 4 | 63.5 | 30.2 | 21.3 | 50.7 | 42.6 | 17.6 |
| 8 | 61.7 | 33.8 | 40.2 | 51.1 | 44.2 | 34.6 |

## ARM Graviton4 (c8g.metal-24xl) — slots Top-Down, fineweb_text b12

| threads | fat retiring% | fat backend% | fat GiB/s | entries retiring% | entries backend% | entries GiB/s |
|--|--|--|--|--|--|--|
| 1 | 40.9 | 43.4 | 3.6 | 38.0 | 49.8 | 2.8 |
| 4 | 43.0 | 48.5 | 14.1 | 37.7 | 55.0 | 10.8 |
| 8 | 43.1 | 48.3 | 28.0 | 37.5 | 56.5 | 21.4 |

## AMD Genoa (c7a.metal-48xl) — IPC only (no native Top-Down), fineweb_text b12

| threads | fat IPC | entries IPC |
|--|--|--|
| 1 | 2.69 | 2.28 |
| 4 | 2.82 | 2.34 |
| 8 | 2.40 | 2.22 |

## Caveats / follow-ups

- **AMD Top-Down**: this run used `perf stat --topdown`, which Zen does not populate; a re-run with
  `perf stat -M TopdownL1` would recover AMD's retiring/backend breakdown. IPC corroborates for now.
- **Column dependence**: `fineweb_text` (long tokens, gather-dominated) shows the split most
  clearly; on `synthetic_url` the retiring gap is ~1.5pp and core-bound stays low. Both bit-widths
  (b12, b16) are in the raw tarballs.
- The backend-bound figure is the clean cross-ISA metric here; the finer memory-bound vs core-bound
  L2 split is in the raw `-- topdown L2 --` blocks.
