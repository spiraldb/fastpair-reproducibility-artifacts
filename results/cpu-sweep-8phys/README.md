# OnPair CPU decode sweep — 8 physical cores (full)

Cross-generational CPU measurement of the OnPair string decode, isolating the GPU-motivated
"fat dictionary" layout. Three byte-identical decode paths over identical compressed columns:

- **fat** — `data + code*16`: independent fixed-stride load + 16-byte over-copy (this work; FSST's fixed-stride decode at OnPair's dictionary scale).
- **entries** — variable-stride addressing (`offset -> bytes`, dependent load) + the same over-copy. **This is the published OnPair decode** (Gargiulo & Venturini, arXiv:2508.02280): a compact Arrow-style offsets dict that over-copies.
- **naive** — variable-stride + an inlined *exact* per-token copy. A non-over-copying baseline to ground the others; not a real codec (every real one over-copies).

`fat/entries` is the honest improvement over published OnPair; `fat/naive` shows what not over-copying
at all costs. Metric: GiB/s of decoded output, at **1/4/8 threads**, **256 MiB/column**.

## Columns (7)

Real eval columns (same data as the GPU eval, replicated to the working set) plus the synthetic
stand-ins, spanning the dictionary-cardinality range the request-bound thesis turns on:

| column | source | kind |
|--|--|--|
| clickbench_url | real ClickBench URL column | high-cardinality URLs |
| l_comment | real TPC-H SF10 `lineitem.l_comment` | mid-cardinality text |
| l_shipinstruct | real TPC-H SF10 `lineitem.l_shipinstruct` | very low cardinality (≈296 dict tokens) |
| book_reviews | real Amazon-Reviews-2023 Books `text` | high-cardinality natural text (≈65k at b16) |
| synthetic_url / tpch_comment / fineweb_text | deterministic LCG stand-ins | cross-check vs the real columns |

## Dictionary widths

Both **b12** and **b16** (matching the GPU eval). b16 widens the dict (table grows 64 KB → ~1 MB),
where the fat layout's load-unit advantage is most visible.

## This run

Every box `*.4xlarge`, pinned to **8 physical cores** (one logical CPU per core via `lscpu -e`).
`.4xlarge` is the size at which the SMT families (Rome/Milan, all Intel) have a full 8 physical cores;
the no-SMT families (Genoa/Turin, all ARM) have 16 and we pin to 8. Uniform `.4xlarge` slice with 8
active cores each → apples-to-apples. 10 machines: AMD Rome/Milan/Genoa/Turin, Intel
Ice/Sapphire/Granite, ARM Graviton2/3/4 (DDR4 + DDR5 pairs); see `../cpu-sweep/README.md` for the
full machine table.

`cpu-sweep.json` is the combined artifact (per-row `bits` field). Regenerate:
`python3 results/cpu-sweep/combine.py results/cpu-sweep-8phys`. Real columns are produced locally by
`onpair-cpu-bench/extract_cols.py` and shipped via the harness.
