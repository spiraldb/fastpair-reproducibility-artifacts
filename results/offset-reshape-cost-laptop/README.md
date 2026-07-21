# Offset-sidecar decompress + dictionary-repack cost (host CPU, laptop)

The two one-time, host-side costs that sit *outside* the paper's timed decode
boundary (`sections/6_evaluation.tex:51` excludes "the one-time fixed-stride
repack ... and setup"). Measured here to bound "how small" they are. Both are
CPU-only; no GPU is involved, so this runs on a laptop.

## What is measured

Extends the existing `ONPAIR_OFFSET_COST` path in
`vortex-bench/src/onpair_bench.rs` (fork branch `mp/fastpair`) with
two new min-of-7 timings per (column, preset), alongside the existing sidecar
sizes:

- **`repack_ns`** — the in-memory fixed-stride dictionary repack (Q3): scatter
  the packed dictionary bytes into `MAX_TOKEN_SIZE` (16-byte) slots, the exact
  host build the CUDA decode consumes as `dict_padded`
  (`vortex-cuda/benches/onpair_real_data.rs:259`). Scales with dictionary size,
  not column length.
- **`decompress_ns`** — decompressing the stored compressed offset sidecar back
  to the plain integer offsets the GPU consumes (Q2): canonicalizes the
  `BtrBlocks`/`Delta`-compressed offset array (`compress_offsets`) to a
  `PrimitiveArray`, fresh clone per rep. Scales with the offset count
  (`n_batches`), ~0.8 ns/offset on this machine.

Existing fields (`offset_raw_u32`, `offset_compressed_bytes`, `gen_ns`, ...) are
unchanged; `gen_ns` is the serial-CPU *write-time* generation of the sidecar,
not a decode-path cost.

## Machine

Apple M5 Max (Mac17,6), 18 cores, macOS 26.5 (25F71). **Single-threaded**;
release build (`cargo build --release --bin onpair-chunk-bench`, no `cuda`
feature). Datasets: local synthetic-URL corpus (low cardinality) and TPC-H SF1
`l_comment` / `ps_comment` (high cardinality, fill the dictionary). 1000 MB
single chunk, threshold 0.20, min-of-7 reps.

## Result (min-reduced)

| column | bits | dict entries | dict_padded | **repack** | sidecar u32 | sidecar zip | **decompress** | n_batches |
|---|--:|--:|--:|--:|--:|--:|--:|--:|
| synthetic/url | 12 | 879 | 14 KB | 0.002 ms | 2.46 MB | 656 KB | 0.501 ms | 615,936 |
| synthetic/url | 16 | 886 | 14 KB | 0.002 ms | 2.48 MB | 660 KB | 0.504 ms | 620,253 |
| tpch/l_comment | 12 | 4,096 | 64 KB | 0.012 ms | 0.64 MB | 193 KB | 0.141 ms | 160,534 |
| tpch/l_comment | 16 | **65,507** | **1.05 MB** | **0.311 ms** | 0.48 MB | 143 KB | 0.101 ms | 119,782 |
| tpch/ps_comment | 12 | 4,096 | 64 KB | 0.012 ms | 0.30 MB | 95 KB | 0.064 ms | 75,970 |
| tpch/ps_comment | 16 | 34,795 | 0.56 MB | 0.163 ms | 0.25 MB | 76 KB | 0.052 ms | 63,461 |

## Reading

- **Repack (Q3):** the worst case, a full dict-16 dictionary (65,507 entries,
  1.05 MB padded), is **0.31 ms**, one-time and independent of column length;
  dict-12 (4,096 entries) is **0.012 ms**. Against a ~1 ms B300 decode of a 1 GB
  column, and amortized over every scan of the column, it is negligible.
- **Decompress (Q2):** **~0.8 ns per offset**; 0.05–0.14 ms for the SF1 columns
  (60–160 K offsets) and 0.50 ms for the 616 K-offset / 2.5 MB synthetic sidecar.
  This is a one-time per-load cost: once decompressed, the offsets are resident
  and serve every subsequent decode. The alternative to storing the sidecar is
  regenerating the offsets on the GPU, measured at +15–19% of decode on the
  device-filling columns (`../b300-campaign-0717/op_gpu_regen.jsonl`).

Both are sub-millisecond, one-time, and CPU-side, and neither is on the per-decode
critical path the headline throughput measures.

## Reproduce

```sh
# fork mp/fastpair, CPU-only build
cargo build --release --bin onpair-chunk-bench
ONPAIR_OFFSET_COST=out.jsonl target/release/onpair-chunk-bench run \
  --parquet <col>.parquet --column <col> --dataset-id <id> \
  --bits 12,16 --chunk-bytes 1048576000 --threshold 0.2 --out-dir /tmp/vx
```
