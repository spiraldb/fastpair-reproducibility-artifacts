# OnPair CPU decode microbench — Intel(R) Xeon(R) Platinum 8488C

cores/socket: 4, threads/core: 2. Decode throughput (GiB/s of output), byte-identical across layouts. fat = data+code*16 (one independent load + over-copy); entries = variable-stride + over-copy; naive = variable-stride + exact copy (non-over-copying baseline).

| column | thr | fat | entries | naive | fat/naive | fat/entries |
|--|--:|--:|--:|--:|--:|--:|
| synthetic_url | 1 | 6.6 | 6.5 | 2.4 | 2.77x | 1.02x |
| synthetic_url | 4 | 23.8 | 22.9 | 9.1 | 2.61x | 1.04x |
| synthetic_url | 8 | 28.8 | 28.3 | 11.9 | 2.42x | 1.02x |
| tpch_comment | 1 | 7.4 | 7.3 | 2.1 | 3.55x | 1.01x |
| tpch_comment | 4 | 26.3 | 25.8 | 7.9 | 3.33x | 1.02x |
| tpch_comment | 8 | 31.9 | 31.0 | 10.9 | 2.92x | 1.03x |
| fineweb_text | 1 | 3.5 | 2.9 | 0.5 | 6.84x | 1.23x |
| fineweb_text | 4 | 12.5 | 10.9 | 2.0 | 6.10x | 1.15x |
| fineweb_text | 8 | 13.9 | 14.0 | 3.0 | 4.62x | 0.99x |
