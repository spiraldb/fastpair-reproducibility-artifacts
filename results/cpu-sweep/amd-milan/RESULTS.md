# OnPair CPU decode microbench — AMD EPYC 7R13 Processor

cores/socket: 4, threads/core: 2. Decode throughput (GiB/s of output), byte-identical across layouts. fat = data+code*16 (one independent load + over-copy); entries = variable-stride + over-copy; naive = variable-stride + exact copy (non-over-copying baseline).

| column | thr | fat | entries | naive | fat/naive | fat/entries |
|--|--:|--:|--:|--:|--:|--:|
| synthetic_url | 1 | 4.2 | 4.1 | 2.3 | 1.78x | 1.02x |
| synthetic_url | 4 | 12.3 | 12.3 | 8.5 | 1.46x | 1.00x |
| synthetic_url | 8 | 14.2 | 14.1 | 10.5 | 1.35x | 1.01x |
| tpch_comment | 1 | 5.5 | 5.2 | 2.2 | 2.48x | 1.05x |
| tpch_comment | 4 | 13.6 | 13.4 | 8.0 | 1.70x | 1.01x |
| tpch_comment | 8 | 15.0 | 15.1 | 10.7 | 1.41x | 0.99x |
| fineweb_text | 1 | 1.6 | 1.5 | 0.6 | 2.69x | 1.04x |
| fineweb_text | 4 | 5.7 | 5.5 | 2.2 | 2.54x | 1.03x |
| fineweb_text | 8 | 8.2 | 7.0 | 3.2 | 2.58x | 1.17x |
