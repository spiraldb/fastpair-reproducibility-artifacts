# OnPair CPU decode microbench — AMD EPYC 9R45

cores/socket: 8, threads/core: 1. Decode throughput (GiB/s of output), byte-identical across layouts. fat = data+code*16 (one independent load + over-copy); entries = variable-stride + over-copy; naive = variable-stride + exact copy (non-over-copying baseline).

| column | bits | thr | fat | entries | naive | fat/naive | fat/entries |
|--|--:|--:|--:|--:|--:|--:|--:|
| synthetic_url | 12 | 1 | 14.9 | 12.7 | 3.7 | 4.01x | 1.17x |
| synthetic_url | 12 | 2 | 25.5 | 24.5 | 7.3 | 3.48x | 1.04x |
| synthetic_url | 12 | 4 | 29.0 | 28.6 | 14.3 | 2.03x | 1.02x |
| synthetic_url | 16 | 1 | 15.5 | 14.0 | 5.3 | 2.94x | 1.10x |
| synthetic_url | 16 | 2 | 24.6 | 24.0 | 10.3 | 2.38x | 1.02x |
| synthetic_url | 16 | 4 | 29.0 | 28.9 | 20.0 | 1.45x | 1.00x |
| tpch_comment | 12 | 1 | 21.6 | 18.6 | 3.8 | 5.75x | 1.16x |
| tpch_comment | 12 | 2 | 26.7 | 26.3 | 7.5 | 3.57x | 1.01x |
| tpch_comment | 12 | 4 | 29.2 | 28.9 | 14.5 | 2.01x | 1.01x |
| tpch_comment | 16 | 1 | 21.6 | 18.7 | 3.8 | 5.66x | 1.15x |
| tpch_comment | 16 | 2 | 26.7 | 26.2 | 7.5 | 3.58x | 1.02x |
| tpch_comment | 16 | 4 | 29.2 | 29.1 | 14.6 | 2.00x | 1.00x |
| fineweb_text | 12 | 1 | 5.4 | 4.8 | 0.8 | 7.28x | 1.12x |
| fineweb_text | 12 | 2 | 10.7 | 9.6 | 1.5 | 7.26x | 1.11x |
| fineweb_text | 12 | 4 | 20.3 | 18.8 | 2.9 | 6.95x | 1.08x |
| fineweb_text | 16 | 1 | 9.7 | 9.0 | 1.6 | 6.02x | 1.08x |
| fineweb_text | 16 | 2 | 18.6 | 17.7 | 3.2 | 5.86x | 1.05x |
| fineweb_text | 16 | 4 | 27.0 | 27.0 | 6.2 | 4.34x | 1.00x |
| clickbench_url | 12 | 1 | 9.3 | 8.4 | 1.1 | 8.49x | 1.10x |
| clickbench_url | 12 | 2 | 18.0 | 16.3 | 2.2 | 8.33x | 1.10x |
| clickbench_url | 12 | 4 | 26.9 | 26.5 | 4.3 | 6.29x | 1.01x |
| clickbench_url | 16 | 1 | 11.4 | 10.4 | 1.9 | 6.12x | 1.10x |
| clickbench_url | 16 | 2 | 20.3 | 19.3 | 3.7 | 5.48x | 1.05x |
| clickbench_url | 16 | 4 | 27.7 | 27.6 | 7.3 | 3.79x | 1.00x |
| l_comment | 12 | 1 | 10.6 | 9.8 | 1.4 | 7.62x | 1.08x |
| l_comment | 12 | 2 | 20.2 | 18.4 | 2.8 | 7.32x | 1.10x |
| l_comment | 12 | 4 | 28.0 | 27.7 | 5.4 | 5.17x | 1.01x |
| l_comment | 16 | 1 | 9.8 | 9.5 | 1.9 | 5.24x | 1.03x |
| l_comment | 16 | 2 | 18.2 | 17.8 | 3.7 | 4.89x | 1.02x |
| l_comment | 16 | 4 | 26.7 | 26.9 | 7.4 | 3.62x | 0.99x |
| l_shipinstruct | 12 | 1 | 18.3 | 15.5 | 2.2 | 8.48x | 1.18x |
| l_shipinstruct | 12 | 2 | 25.9 | 25.7 | 4.3 | 6.05x | 1.01x |
| l_shipinstruct | 12 | 4 | 28.9 | 28.8 | 8.4 | 3.46x | 1.00x |
| l_shipinstruct | 16 | 1 | 18.0 | 15.3 | 2.2 | 8.33x | 1.18x |
| l_shipinstruct | 16 | 2 | 25.9 | 25.6 | 4.3 | 6.07x | 1.01x |
| l_shipinstruct | 16 | 4 | 28.9 | 28.7 | 8.4 | 3.46x | 1.01x |
| book_reviews | 12 | 1 | 6.9 | 6.6 | 0.8 | 9.14x | 1.05x |
| book_reviews | 12 | 2 | 13.9 | 12.7 | 1.5 | 9.32x | 1.10x |
| book_reviews | 12 | 4 | 24.2 | 24.2 | 3.0 | 8.18x | 1.00x |
| book_reviews | 16 | 1 | 8.2 | 7.4 | 1.2 | 7.05x | 1.11x |
| book_reviews | 16 | 2 | 15.5 | 14.3 | 2.3 | 6.75x | 1.08x |
| book_reviews | 16 | 4 | 25.4 | 25.0 | 4.5 | 5.63x | 1.02x |
