# FastPair reproducibility artifacts

FastPair is a CUDA decoder for OnPair, a pair-merging dictionary string codec in the FSST family.
It decodes the unmodified, byte-packed OnPair format on the GPU at HBM-class rates, up to roughly
1.4 TB/s on a B300 for the TPC-H comment columns. That is 2.4 to 4.6x faster than the GPU's
fixed-function Decompression Engine across the columns we measure, and 3.3x faster than GSST, the
prior GPU decoder for this codec family, on the A100 column GSST reports. This repository is the
reproduction package for the paper "FastPair: GPU-Optimized String Decompression": the committed raw
results, the figure generators, and the benchmark sources that produced them.

The figures and headline numbers regenerate from committed data, with no GPU, no cloud account, and
no access to the manuscript required. Everything they derive from is committed here under `results/`.

## Reproduce in one command

```sh
make verify          # or: bash experiments/verify.sh
```

This rebuilds every data-driven figure from `results/` and re-derives every headline number,
asserting each against the value the paper states. It prints a PASS/FAIL table and exits nonzero on
any mismatch. The only prerequisite is [`uv`](https://docs.astral.sh/uv/), since each figure script
carries its own dependencies (PEP 723). To re-check the numbers without rebuilding the figures, run
`uv run experiments/validate.py`.

Current status: 15 figures rebuilt (the 11 in the paper plus 4 extended-version figures), 43 headline
numbers re-derived, all green.

## What you are looking at

The repository has three parts, each with its own guide. Start with whichever matches your question.

| Directory | What it holds | Read first |
|---|---|---|
| `results/` | every committed measurement, namely the four-GPU decode matrix, the hardware-DE head-to-head, the NSight Compute cost surface, the ten-generation CPU sweep, IAA, and end-to-end. | [`results/README.md`](results/README.md) for the fleet, the corpus caveats, and the JSON/CSV schema; [`results/RESULTS_SUMMARY.md`](results/RESULTS_SUMMARY.md) for a one-page index of every campaign and its headline. |
| `figures/` | the figure generators (`fig_*.py`, each self-contained) and `common.py`, the shared reduction code that the figures and the number-checker both use. | [`figures/README.md`](figures/README.md), which maps each script to its paper label and its source data. |
| `experiments/` | the reproduction entry points (`verify.sh`, `validate.py`), the provenance map, the conventions, and the benchmark sources. | [`experiments/README.md`](experiments/README.md), then [`MANIFEST.md`](experiments/MANIFEST.md) (each result to its box, revision, config, and figure) and [`METHODOLOGY.md`](experiments/METHODOLOGY.md) (how every number is measured and reduced). |

Where any two documents disagree on provenance, `experiments/MANIFEST.md` is authoritative.

## Rebuild the figures, or re-run the benchmarks

There are two depths of work here, depending on whether you have GPU hardware.

Rebuilding from committed data needs no hardware. `make verify` regenerates every figure and
re-derives every headline number from the archived `results/`, asserting each number against the
value the paper states. This is a convenience for rebuilding a figure, checking a number, or building
a new plot on the committed data. It confirms the figures and numbers follow from the measurements;
it does not re-measure anything.

Re-running a benchmark reproduces the measurements themselves, and needs your own capable machine.
The orchestration we used to drive the cloud runs is intentionally not part of this artifact, so
reproduction is build-and-run: you
provision and configure your own box. The frozen harness is `github.com/mprammer/vortex` at
branch `mp/fastpair` (a single flattened commit, `9b4714c2a`). Clone it, build on a GPU box with `--features cuda`,
and run:

```sh
python benchmarks/onpair-bench/run.py --gpu-decode --gpu-validate --gpu-iters 100 --chunk-mb 1000
```

with your own `HF_TOKEN` set. Its `benchmarks/onpair-bench/README.md` covers the prerequisites and
the Decompression Engine and end-to-end benches. The exact protocol every run follows, namely the
reduction, iteration count, clock settings, and baselines, is in
[`experiments/METHODOLOGY.md`](experiments/METHODOLOGY.md). The standalone benches under
`experiments/bench/` (`e2e_scan.cu`, `nvcomp_hw_bench.cu`, and the IAA bench) are read-only copies of
files in that tree.

## Relation to the paper

The manuscript is a separate repository that `\includegraphics` the figure PDFs this artifact
produces. To update a figure for the paper, run `make verify` here, then copy the regenerated
`figures/out/<fig>.pdf` into the manuscript. The decode kernels are byte-identical across the
revision lineage `fe4a84d65 → 550c3c3ca → 49174a3a6` that produced the committed results (the
end-to-end results are from `6ee03c1d8`), and the frozen harness on `mp/fastpair` carries those same
kernels, so throughput is comparable across every GPU run. See
[`experiments/METHODOLOGY.md`](experiments/METHODOLOGY.md) for the details.
