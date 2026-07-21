# OnPair CPU decode microbench — AMD EPYC 9R14

cores/socket: 8, threads/core: 1. Decode throughput (GiB/s of output), byte-identical across layouts. fat = data+code*16 (one independent load + over-copy); entries = variable-stride + over-copy; naive = variable-stride + exact copy (non-over-copying baseline).

| column | thr | fat | entries | naive | fat/naive | fat/entries |
|--|--:|--:|--:|--:|--:|--:|
| synthetic_url | 1 | 5.6 | 4.9 | 2.6 | 2.17x | 1.13x |
| synthetic_url | 4 | 15.9 | 15.6 | 10.0 | 1.60x | 1.02x |
| synthetic_url | 8 | 19.2 | 19.2 | 15.5 | 1.24x | 1.00x |
| tpch_comment | 1 | 6.1 | 5.7 | 2.3 | 2.68x | 1.08x |
| tpch_comment | 4 | 16.4 | 16.2 | 8.6 | 1.92x | 1.01x |
| tpch_comment | 8 | 19.5 | 19.3 | 15.0 | 1.30x | 1.01x |
| fineweb_text | 1 | 2.9 | 2.3 | 0.6 | 4.67x | 1.25x |
| fineweb_text | 4 | 10.5 | 8.4 | 2.4 | 4.45x | 1.24x |
| fineweb_text | 8 | 16.9 | 14.7 | 4.5 | 3.73x | 1.15x |
