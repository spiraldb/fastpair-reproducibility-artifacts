# Datasets — how each is obtained or generated

The benches sample 1 GB of a column's UTF-8 bytes. Sources, in the order the sweep uses them.
The download links were live as of **2026-06** (the paper's measurement window); each source's
landing page is recorded next to its URL in the harness `columns.py`
(`github.com/mprammer/vortex` @ branch `mp/fastpair`), so a reproducer can find a moved source from there.
This is a reproducibility harness, not a data archive — best-effort provenance, not a frozen copy
of the corpora.

| Dataset / column | How | Notes |
|---|---|---|
| **synthetic** `url` | generated on-box: `onpair-chunk-bench gen-synth-urls` (10M rows, **seed 123**) | deterministic ClickBench-style URL corpus; no download. The reproducible URL stand-in. |
| **tpch-sf10** `l_comment`, `ps_comment`, `s_comment`, `l_shipinstruct` | generated on-box: `onpair-chunk-bench gen-tpch --sf 10` | deterministic; no download. `l_shipinstruct` is the low-cardinality (fast) column. |
| **clickbench** `URL` | `curl https://datasets.clickhouse.com/hits_compatible/hits.parquet` (~13.7 GB) | the real ClickBench URL column; downloaded by `run.py` on first use. |
| **fineweb** `text` | HuggingFace `HuggingFaceFW/fineweb` (v1.4.0 sample/10BT/000_00000.parquet) | needs an HF token to avoid throttling (pushed as a job secret). |
| **wikipedia** `text` | HuggingFace `wikimedia/wikipedia` (20231101.en/train-00000-of-00041.parquet) | needs an HF token. |
| **book-reviews** `text` | HuggingFace `McAuley-Lab/Amazon-Reviews-2023`, category **Books**, `text` field, ~1.2 GB cap | **reproduced** public corpus, *not* OnPair's original non-public book-reviews. Non-redistributable; fine for personal use. |
| **amazon-movies** `text` | same, category **Movies_and_TV** | long narrative prose (contrasting token profile). |
| **amazon-electronics** `text` | same, category **Electronics** | short product text. |
| **dbtext** `email,hex,l_comment,ps_comment,yago` | small native-size files staged with the bench | launch-bound (1–6 MB); reported for completeness, not as throughput. |

The CPU/IAA benches read pre-sampled column dumps (`~/data/onpair-cpu-cols/*.bin`, format:
`u64 nrows; (nrows+1) u32 offsets LE; payload bytes`) so they need no parquet at bench time;
those are derived from the same sources above.

The **end-to-end** experiment (#28) dumps the exact encoder output for clickbench URL +
synthetic URL via `ONPAIR_DUMP_E2E`; the dumps (~400 MB) are stashed at
`~/data/onpair-e2e-dumps/` (not committed; regenerable from the frozen harness fork — see its `benchmarks/onpair-bench/README.md` §3).

HF token lives at `~/.cache/huggingface/token` and is pushed to the box as a 0600 job secret
(never on a command line, torn down with the box).
