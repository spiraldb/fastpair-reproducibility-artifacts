# OnPair CPU decode microbench — Neoverse-V2

cores/socket: 8, threads/core: 1. Decode throughput (GiB/s of output), byte-identical across layouts. fat = data+code*16 (one independent load + over-copy); entries = variable-stride + over-copy; naive = variable-stride + exact copy (non-over-copying baseline).

| column | thr | fat | entries | naive | fat/naive | fat/entries |
|--|--:|--:|--:|--:|--:|--:|
| synthetic_url | 1 | 8.2 | 7.0 | 3.1 | 2.65x | 1.18x |
| synthetic_url | 4 | 27.3 | 23.1 | 11.4 | 2.40x | 1.19x |
| synthetic_url | 8 | 46.0 | 39.7 | 20.6 | 2.24x | 1.16x |
| tpch_comment | 1 | 10.4 | 9.3 | 3.0 | 3.50x | 1.12x |
| tpch_comment | 4 | 34.5 | 31.0 | 10.9 | 3.15x | 1.11x |
| tpch_comment | 8 | 57.4 | 51.5 | 19.7 | 2.91x | 1.11x |
| fineweb_text | 1 | 2.9 | 2.4 | 0.7 | 4.42x | 1.19x |
| fineweb_text | 4 | 10.4 | 8.7 | 2.5 | 4.07x | 1.20x |
| fineweb_text | 8 | 17.8 | 15.6 | 4.9 | 3.63x | 1.14x |
