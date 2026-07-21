# OnPair CPU decode microbench — Neoverse-N1

cores/socket: 8, threads/core: 1. Decode throughput (GiB/s of output), byte-identical across layouts. fat = data+code*16 (one independent load + over-copy); entries = variable-stride + over-copy; naive = variable-stride + exact copy (non-over-copying baseline).

| column | thr | fat | entries | naive | fat/naive | fat/entries |
|--|--:|--:|--:|--:|--:|--:|
| synthetic_url | 1 | 3.5 | 3.0 | 1.5 | 2.37x | 1.14x |
| synthetic_url | 4 | 12.4 | 10.9 | 5.5 | 2.28x | 1.14x |
| synthetic_url | 8 | 20.7 | 19.1 | 10.1 | 2.05x | 1.08x |
| tpch_comment | 1 | 4.5 | 4.2 | 1.6 | 2.73x | 1.07x |
| tpch_comment | 4 | 15.6 | 14.8 | 6.1 | 2.55x | 1.06x |
| tpch_comment | 8 | 26.3 | 25.4 | 11.2 | 2.34x | 1.04x |
| fineweb_text | 1 | 1.7 | 1.4 | 0.4 | 3.98x | 1.15x |
| fineweb_text | 4 | 6.2 | 5.5 | 1.6 | 3.77x | 1.13x |
| fineweb_text | 8 | 11.3 | 10.2 | 3.2 | 3.56x | 1.11x |
