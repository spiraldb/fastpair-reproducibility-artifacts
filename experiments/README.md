# FastPair experiments and reproduction

This directory is the reproduction entry point: the scripts that rebuild the paper's figures and
re-derive its numbers, the provenance map, the measurement conventions, and the benchmark sources.
The chain is self-contained. It reads only the committed results under [`../results/`](../results)
and the figure generators under [`../figures/`](../figures), with no external datasets, no cloud
state, and no private tooling required.

## Reproduce in one command

```sh
bash experiments/verify.sh        # or:  make verify
```

This rebuilds every data-driven figure from the committed `results/` (no GPU, no cloud) and then
re-derives every headline number and asserts it against the value the paper states. It prints a
PASS/FAIL table and exits nonzero on any mismatch. The only prerequisite is
[`uv`](https://docs.astral.sh/uv/), since each figure script carries its own dependencies (PEP 723).

To re-check the numbers without rebuilding the figures, run `uv run experiments/validate.py`.

## What is here

| Path | What it is |
|---|---|
| [`verify.sh`](verify.sh) | the one-command reproduce: rebuild the figures, then re-derive the numbers |
| [`validate.py`](validate.py) | re-derives every headline number from `results/` through `figures/common.py`, the figures' own reduction code, so there is no second implementation to drift |
| [`MANIFEST.md`](MANIFEST.md) | every result mapped to its box, revision, config, reduction, and the figure or number it backs |
| [`METHODOLOGY.md`](METHODOLOGY.md) | the measurement conventions: reduction to the min, GB/s, best-shipped-kernel, byte-exact validation, sampling, and the baselines |
| [`bench/gpu/`](bench/gpu) | the standalone GPU benches: `e2e_scan.cu` (decode then scan) and `nvcomp_hw_bench.cu` (the Decompression Engine baseline); `e2e_scan` reuses the hero decode kernel |
| [`bench/cpu/`](bench/cpu) | the fixed-stride versus variable-stride CPU decode bench (a Rust crate) |
| [`bench/iaa/`](bench/iaa) | the Intel IAA aggregate bench, with its reboot-aware setup and driver |
| [`data/fetch.md`](data/fetch.md) | how each dataset is obtained or generated |

## Rebuild the figures, or re-run the benchmarks

There are two depths of work here, depending on whether you have GPU hardware.

Rebuilding from committed data needs no hardware. `verify.sh` regenerates every figure and re-derives
every headline number from the archived `results/`, asserting each number against the value the paper
states. This is a convenience for rebuilding a figure, checking a number, or building a new plot on
the committed data. It confirms the figures and numbers follow from the measurements; it does not
re-measure anything.

Re-running a benchmark reproduces the measurements themselves, and needs your own capable machine.
The orchestration we used to drive the cloud runs is intentionally not shipped here, so reproduction
is build-and-run: you provision and
configure your own box. The frozen harness is `github.com/mprammer/vortex` on branch `mp/fastpair` (a single flattened commit, `9b4714c2a`). Clone it, build on a GPU box with `--features cuda`, and run:

```sh
python benchmarks/onpair-bench/run.py --gpu-decode --gpu-validate --gpu-iters 100 --chunk-mb 1000
```

with your own `HF_TOKEN` set. Its `benchmarks/onpair-bench/README.md` covers the prerequisites and
the Decompression Engine and end-to-end benches. The exact protocol, namely the reduction, iteration
count, clock settings, and baselines, is in [`METHODOLOGY.md`](METHODOLOGY.md); the per-result box,
revision, and config are in [`MANIFEST.md`](MANIFEST.md). The standalone benches here (`e2e_scan.cu`,
`nvcomp_hw_bench.cu`) are read-only copies of files in that tree, and they build inside it, since
their `#include`s are relative to `benchmarks/onpair-bench/`.

## Code revisions

The GPU and CPU bench code is pinned. The public frozen harness is `github.com/mprammer/vortex` at
branch `mp/fastpair` (a single flattened commit, `9b4714c2a`). The decode kernels are byte-identical across the
lineage `fe4a84d65 → 550c3c3ca → 49174a3a6` that produced the committed results, where only the bench
harness, the datasets, and the end-to-end bench changed. The end-to-end results are from `6ee03c1d8`,
and `mp/fastpair` carries the same kernels, so a run there reproduces every GPU number regardless of
which revision a `run-env.txt` records.
