# Figure generation

These scripts reproduce the paper's data-driven figures directly from the committed measurement
artifacts in [`../results/`](../results). No GPU and no benchmark re-run: every figure is built from
the archived JSON and CSV. For the full reproduce (figures plus headline-number re-derivation) run
[`../experiments/verify.sh`](../experiments/verify.sh), or `make verify`.

## Reproduce

Each script is self-contained, with inline dependencies ([PEP 723](https://peps.python.org/pep-0723/)),
so with [`uv`](https://docs.astral.sh/uv/) a single figure is `uv run figures/fig_sota.py`. Output
PDFs (and PNGs) land in `figures/out/`. Shared loading and the unified theme live in `common.py`,
which also holds the best-shipped-kernel rule (it excludes the non-byte-exact `*ablate*` builds), the
HBM peaks, the GiB-to-GB factor, and the hardware-DE map. `validate.py` reuses `common.py` too, so
the figures and the number-checker share one reduction.

Type sizes and mark sizes come from `common.FS` / `common.MS`, and they are **printed points**: a
figure the paper prints passes its float shape to `common.save` (`width="column"` or `width="text"`),
which scales the canvas so the saved PDF is exactly the width LaTeX shows it at. Fonts are absolute,
so the axes absorb the change and a declared 8pt label lands on the page as 8pt. Generators the
paper does not print omit `width` and keep whatever size they chose.

`verify.sh` rebuilds 15 figures: the 11 that the paper `\includegraphics`, plus 4 extended-version
figures that the main paper does not reference. `fig_hierarchy` is a code-drawn schematic with no
results dependency; the other 14 are data-driven.

## The 11 figures in the paper

| Script | Label | What it plots | Source under `results/` |
|---|---|---|---|
| `fig_teaser` | `fig:teaser` | FastPair versus the DE versus Zstd, 3 columns | `b300/onpair_summary_*` + `b300/onpair_nvcomp_hw.json` |
| `fig_sota` | `fig:payoff` | throughput against ratio, every codec and GPU | `{a100,l40s,h100,b300}/onpair_summary_*` + `b300/onpair_nvcomp_hw.json` |
| `fig_sota_cpu` | `fig:cpufield` | the CPU codec field | `cpu-sota/*.json` + the GPU summaries |
| `fig_scaling` | `fig:scaling` | decode and percentage of HBM peak across GPUs | `{a100,h100,b300}/onpair_summary_tpch-sf10.json` |
| `fig_stagecost` | `fig:stagecost` | the per-stage deltas from the skip-one-stage ablation | `b300/onpair_summary_{lship,synthetic,clickbench}.json` (the `*_ablate*` builds) |
| `fig_costsurface` | `fig:costsurface` | NSight Compute percentage of peak per pipe, 4 arches | `ncu-costsurface.csv` |
| `fig_gatherwidth` | `fig:gatherwidth` | the split8read gather-width lever versus short-token fraction | `b300/onpair_summary_*` |
| `fig_ablation` | `fig:ablation` | each read-side lever's decode speedup (fixed-stride, coarsening), 4 GPUs | `{a100,l40s,h100,b300}/onpair_summary_*` |
| `fig_compressibility` | `fig:compressibility` | compression ratio by technique over real and synthetic columns | `cpu-sota/*.json` |
| `fig_offtrade` | `fig:offtrade` | offset-strategy × materialization trade-off vs incoming-filter selectivity (e2e relative to dense), B300 | `b300-offtrade/{run1..4}_url.json` |
| `fig_hierarchy` | `fig:hierarchy` | a code-drawn schematic of the GPU memory path (theme only, no results data) | none |

## The 4 extended-version figures

These rebuild for completeness (the CPU deep-dive and a per-dataset breakdown) but are not referenced
in the main paper.

| Script | What it plots | Source under `results/` |
|---|---|---|
| `fig_crossstack` | fixed-stride versus variable-stride, 10 AWS generations (writes `fig_crossstack_strip.pdf`) | `cpu-sweep-4phys/cpu-sweep.json` |
| `fig_bitsweep` | dictionary bit-width 9 to 16 | `cpu-bitsweep/cpu-bitsweep.json` |
| `fig_cputma` | the Top-Down slots | `cpu-tma/{intel-sapphire,arm-graviton4}_raw.tar.gz` |
| `fig_b300_datasets` | the per-dataset decode breakdown on the B300 | `b300/onpair_summary_*.json` |

## Superseded scripts (`_archive/`)

`fig_payoff`, `fig_field`, `fig_breadth`, `fig_pareto`, `fig_payoff_frontier`, `fig_ldst`, and
`fig_tokenlen` are earlier figures no longer produced. For example, `fig_payoff` and `fig_field` were
merged into `fig_sota`, and the breadth and Pareto panels folded in too. They read the superseded
`b200` data and are kept under `_archive/` for history only, not built by `verify.sh`.
