# OnPair CPU decode microbench — Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz

cores/socket: 4, threads/core: 2. Decode throughput (GiB/s of output), byte-identical across layouts. fat = data+code*16 (one independent load + over-copy); entries = variable-stride + over-copy; naive = variable-stride + exact copy (non-over-copying baseline).

| column | thr | fat | entries | naive | fat/naive | fat/entries |
|--|--:|--:|--:|--:|--:|--:|
| synthetic_url | 1 | 5.7 | 5.3 | 1.9 | 2.99x | 1.07x |
| synthetic_url | 4 | 19.0 | 18.3 | 7.6 | 2.50x | 1.04x |
| synthetic_url | 8 | 25.3 | 24.2 | 10.2 | 2.47x | 1.04x |
| tpch_comment | 1 | 6.7 | 6.5 | 2.2 | 3.02x | 1.04x |
| tpch_comment | 4 | 21.8 | 21.2 | 8.5 | 2.56x | 1.03x |
| tpch_comment | 8 | 28.1 | 28.0 | 12.1 | 2.32x | 1.00x |
| fineweb_text | 1 | 2.9 | 2.5 | 0.5 | 5.27x | 1.12x |
| fineweb_text | 4 | 10.6 | 9.7 | 2.1 | 4.97x | 1.10x |
| fineweb_text | 8 | 12.8 | 11.5 | 3.1 | 4.20x | 1.11x |
