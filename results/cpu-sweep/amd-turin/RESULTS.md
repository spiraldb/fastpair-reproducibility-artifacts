# OnPair CPU decode microbench — AMD EPYC 9R45

cores/socket: 8, threads/core: 1. Decode throughput (GiB/s of output), byte-identical across layouts. fat = data+code*16 (one independent load + over-copy); entries = variable-stride + over-copy; naive = variable-stride + exact copy (non-over-copying baseline).

| column | thr | fat | entries | naive | fat/naive | fat/entries |
|--|--:|--:|--:|--:|--:|--:|
| synthetic_url | 1 | 15.3 | 13.4 | 4.1 | 3.75x | 1.14x |
| synthetic_url | 4 | 28.7 | 28.5 | 15.7 | 1.82x | 1.00x |
| synthetic_url | 8 | 29.8 | 29.7 | 27.0 | 1.10x | 1.00x |
| tpch_comment | 1 | 21.3 | 18.4 | 3.6 | 5.87x | 1.16x |
| tpch_comment | 4 | 29.2 | 29.0 | 14.2 | 2.05x | 1.01x |
| tpch_comment | 8 | 30.1 | 29.8 | 26.8 | 1.12x | 1.01x |
| fineweb_text | 1 | 5.5 | 5.0 | 0.7 | 7.45x | 1.12x |
| fineweb_text | 4 | 20.9 | 19.0 | 2.9 | 7.16x | 1.10x |
| fineweb_text | 8 | 27.3 | 27.6 | 5.7 | 4.84x | 0.99x |
