# Is FSST-12's trained dictionary platform-dependent?

**No.** Refutes a claim the paper carried in a comment under `tab:datasets`.

`cargo run --release` prints digests of the trained symbol table for four fixed inputs. Run it on
two platforms and compare; there is nothing to configure and no data to stage.

Two of the four inputs saturate the `(gain, length)` ties that are the only order-sensitive step in
training, one below the 1 MiB `FSST12_SAMPLETARGET` (sampler returns the input verbatim, isolating
the tie-break) and one above it (fixed-seed sampler runs too). Measured 2026-09-02 on aarch64 macOS
and x86_64 Linux: **all four byte-identical.**

```
tie_saturated   n_symbols=847   table_digest=2add3a93ec398d8d lens_digest=3d8300d079201475 compressed_total=728000
tie_sat_sampled n_symbols=912   table_digest=6bd900cee02f0575 lens_digest=04b50831d1514655 compressed_total=3640000
log_like        n_symbols=1219  table_digest=c9fa3c7879ab310c lens_digest=a42e381e36a1467d compressed_total=1455483
urlish          n_symbols=1123  table_digest=73d90f661ab99b45 lens_digest=9b0623fdc01f517a compressed_total=706403
```

Why it was never plausible: `fsst12` is the Rust `fsst-rs` crate, not C++. Its sampler is seeded
with a constant and its candidate dedup uses `FxHashMap`/`FxBuildHasher`, which carries no random
seed. The pin is identical at HEAD and at the leg revision.

What remains open is unrelated to platforms: five of fifteen columns in
`results/suite-flat-20260830/b300/fsst12_stored_components.jsonl` still miss the committed cell
totals. See `onpair-gpu-paper/docs/notes/2026-09-02-fsst12-platform-claim-refuted.md`.
