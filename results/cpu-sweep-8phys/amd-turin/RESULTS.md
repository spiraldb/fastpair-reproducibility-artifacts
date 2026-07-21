# OnPair CPU decode microbench — AMD EPYC 9R45

cores/socket: 16, threads/core: 1. Decode throughput (GiB/s of output), byte-identical across layouts. fat = data+code*16 (one independent load + over-copy); entries = variable-stride + over-copy; naive = variable-stride + exact copy (non-over-copying baseline).

| column | bits | thr | fat | entries | naive | fat/naive | fat/entries |
|--|--:|--:|--:|--:|--:|--:|--:|
| synthetic_url | 12 | 1 | 15.7 | 13.5 | 4.6 | 3.40x | 1.16x |
| synthetic_url | 12 | 4 | 28.9 | 28.8 | 17.8 | 1.62x | 1.00x |
| synthetic_url | 12 | 8 | 30.1 | 29.8 | 28.0 | 1.08x | 1.01x |
| synthetic_url | 16 | 1 | 15.6 | 13.3 | 4.5 | 3.45x | 1.17x |
| synthetic_url | 16 | 4 | 29.2 | 28.7 | 17.6 | 1.66x | 1.02x |
| synthetic_url | 16 | 8 | 30.6 | 30.4 | 27.4 | 1.12x | 1.00x |
| tpch_comment | 12 | 1 | 21.6 | 18.7 | 3.8 | 5.62x | 1.15x |
| tpch_comment | 12 | 4 | 29.4 | 29.3 | 14.7 | 2.00x | 1.00x |
| tpch_comment | 12 | 8 | 30.1 | 30.0 | 27.2 | 1.10x | 1.00x |
| tpch_comment | 16 | 1 | 21.9 | 18.8 | 3.8 | 5.77x | 1.17x |
| tpch_comment | 16 | 4 | 29.4 | 29.2 | 14.7 | 2.01x | 1.01x |
| tpch_comment | 16 | 8 | 30.1 | 30.0 | 27.2 | 1.11x | 1.00x |
| fineweb_text | 12 | 1 | 5.5 | 5.0 | 0.7 | 7.55x | 1.10x |
| fineweb_text | 12 | 4 | 20.8 | 18.8 | 2.9 | 7.26x | 1.11x |
| fineweb_text | 12 | 8 | 27.6 | 27.4 | 5.6 | 4.89x | 1.01x |
| fineweb_text | 16 | 1 | 10.1 | 9.1 | 1.6 | 6.35x | 1.11x |
| fineweb_text | 16 | 4 | 27.6 | 27.0 | 6.2 | 4.45x | 1.02x |
| fineweb_text | 16 | 8 | 30.1 | 30.0 | 11.9 | 2.52x | 1.00x |
| clickbench_url | 12 | 1 | 9.4 | 8.4 | 1.1 | 8.66x | 1.11x |
| clickbench_url | 12 | 4 | 26.7 | 26.5 | 4.2 | 6.31x | 1.01x |
| clickbench_url | 12 | 8 | 29.4 | 29.0 | 8.2 | 3.58x | 1.01x |
| clickbench_url | 16 | 1 | 11.4 | 11.0 | 1.9 | 6.08x | 1.04x |
| clickbench_url | 16 | 4 | 27.8 | 27.5 | 7.3 | 3.82x | 1.01x |
| clickbench_url | 16 | 8 | 30.3 | 30.1 | 14.1 | 2.15x | 1.01x |
| l_comment | 12 | 1 | 10.8 | 9.9 | 1.4 | 7.72x | 1.10x |
| l_comment | 12 | 4 | 28.0 | 27.8 | 5.5 | 5.11x | 1.00x |
| l_comment | 12 | 8 | 29.9 | 29.8 | 10.6 | 2.81x | 1.00x |
| l_comment | 16 | 1 | 9.6 | 9.3 | 1.9 | 5.08x | 1.03x |
| l_comment | 16 | 4 | 27.0 | 26.1 | 7.4 | 3.65x | 1.03x |
| l_comment | 16 | 8 | 29.8 | 29.6 | 14.3 | 2.09x | 1.01x |
| l_shipinstruct | 12 | 1 | 18.6 | 15.5 | 2.1 | 8.70x | 1.20x |
| l_shipinstruct | 12 | 4 | 28.9 | 28.8 | 8.4 | 3.46x | 1.01x |
| l_shipinstruct | 12 | 8 | 29.3 | 29.2 | 16.2 | 1.81x | 1.00x |
| l_shipinstruct | 16 | 1 | 18.6 | 15.6 | 2.2 | 8.59x | 1.19x |
| l_shipinstruct | 16 | 4 | 28.9 | 28.8 | 8.4 | 3.45x | 1.00x |
| l_shipinstruct | 16 | 8 | 29.3 | 29.2 | 16.2 | 1.81x | 1.01x |
| book_reviews | 12 | 1 | 6.8 | 6.5 | 0.8 | 9.13x | 1.05x |
| book_reviews | 12 | 4 | 24.2 | 24.4 | 2.9 | 8.22x | 0.99x |
| book_reviews | 12 | 8 | 28.2 | 28.3 | 5.7 | 4.92x | 1.00x |
| book_reviews | 16 | 1 | 7.9 | 7.5 | 1.2 | 6.82x | 1.05x |
| book_reviews | 16 | 4 | 26.2 | 24.6 | 4.5 | 5.79x | 1.07x |
| book_reviews | 16 | 8 | 29.2 | 29.2 | 8.8 | 3.33x | 1.00x |
