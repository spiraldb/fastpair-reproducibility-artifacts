# OnPair CPU decode microbench — Neoverse-V1

cores/socket: 8, threads/core: 1. Decode throughput (GiB/s of output), byte-identical across layouts. fat = data+code*16 (one independent load + over-copy); entries = variable-stride + over-copy; naive = variable-stride + exact copy (non-over-copying baseline).

| column | thr | fat | entries | naive | fat/naive | fat/entries |
|--|--:|--:|--:|--:|--:|--:|
| synthetic_url | 1 | 6.3 | 5.7 | 2.6 | 2.41x | 1.10x |
| synthetic_url | 4 | 21.4 | 20.9 | 9.5 | 2.24x | 1.02x |
| synthetic_url | 8 | 36.7 | 34.7 | 16.9 | 2.16x | 1.06x |
| tpch_comment | 1 | 8.4 | 7.9 | 2.4 | 3.46x | 1.07x |
| tpch_comment | 4 | 28.2 | 26.3 | 8.9 | 3.15x | 1.07x |
| tpch_comment | 8 | 45.9 | 43.3 | 15.9 | 2.89x | 1.06x |
| fineweb_text | 1 | 2.1 | 2.1 | 0.5 | 4.12x | 1.00x |
| fineweb_text | 4 | 8.0 | 7.8 | 2.0 | 3.95x | 1.03x |
| fineweb_text | 8 | 14.6 | 13.8 | 3.9 | 3.71x | 1.06x |
