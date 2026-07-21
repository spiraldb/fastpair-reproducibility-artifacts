# OnPair CPU decode microbench — AMD EPYC 7R32

cores/socket: 4, threads/core: 2. Decode throughput (GiB/s of output), byte-identical across layouts. fat = data+code*16 (one independent load + over-copy); entries = variable-stride + over-copy; naive = variable-stride + exact copy (non-over-copying baseline).

| column | thr | fat | entries | naive | fat/naive | fat/entries |
|--|--:|--:|--:|--:|--:|--:|
| synthetic_url | 1 | 4.1 | 3.8 | 2.3 | 1.79x | 1.08x |
| synthetic_url | 4 | 11.7 | 11.5 | 7.8 | 1.50x | 1.02x |
| synthetic_url | 8 | 13.3 | 13.1 | 9.6 | 1.39x | 1.02x |
| tpch_comment | 1 | 5.1 | 5.0 | 1.9 | 2.75x | 1.02x |
| tpch_comment | 4 | 13.0 | 12.0 | 6.6 | 1.98x | 1.09x |
| tpch_comment | 8 | 14.4 | 14.3 | 8.8 | 1.65x | 1.01x |
| fineweb_text | 1 | 1.8 | 1.7 | 0.5 | 3.86x | 1.04x |
| fineweb_text | 4 | 6.5 | 6.2 | 1.8 | 3.60x | 1.04x |
| fineweb_text | 8 | 7.6 | 7.1 | 2.8 | 2.76x | 1.07x |
