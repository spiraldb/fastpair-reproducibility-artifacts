# OnPair CPU decode microbench — Intel(R) Xeon(R) 6975P-C

cores/socket: 4, threads/core: 2. Decode throughput (GiB/s of output), byte-identical across layouts. fat = data+code*16 (one independent load + over-copy); entries = variable-stride + over-copy; naive = variable-stride + exact copy (non-over-copying baseline).

| column | thr | fat | entries | naive | fat/naive | fat/entries |
|--|--:|--:|--:|--:|--:|--:|
| synthetic_url | 1 | 7.0 | 6.9 | 2.7 | 2.54x | 1.01x |
| synthetic_url | 4 | 24.7 | 24.6 | 10.4 | 2.38x | 1.01x |
| synthetic_url | 8 | 31.9 | 31.8 | 13.9 | 2.29x | 1.00x |
| tpch_comment | 1 | 7.8 | 7.6 | 2.4 | 3.23x | 1.03x |
| tpch_comment | 4 | 26.8 | 26.0 | 9.3 | 2.88x | 1.03x |
| tpch_comment | 8 | 34.2 | 33.6 | 13.8 | 2.47x | 1.02x |
| fineweb_text | 1 | 3.6 | 3.1 | 0.6 | 5.77x | 1.17x |
| fineweb_text | 4 | 13.6 | 12.4 | 2.4 | 5.60x | 1.10x |
| fineweb_text | 8 | 17.0 | 16.8 | 3.7 | 4.60x | 1.02x |
