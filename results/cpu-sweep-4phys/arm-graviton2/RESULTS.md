# OnPair CPU decode microbench — Neoverse-N1

cores/socket: 8, threads/core: 1. Decode throughput (GiB/s of output), byte-identical across layouts. fat = data+code*16 (one independent load + over-copy); entries = variable-stride + over-copy; naive = variable-stride + exact copy (non-over-copying baseline).

| column | bits | thr | fat | entries | naive | fat/naive | fat/entries |
|--|--:|--:|--:|--:|--:|--:|--:|
| synthetic_url | 12 | 1 | 3.5 | 3.0 | 1.6 | 2.14x | 1.15x |
| synthetic_url | 12 | 2 | 6.5 | 5.9 | 3.2 | 2.04x | 1.11x |
| synthetic_url | 12 | 4 | 12.6 | 11.2 | 6.1 | 2.06x | 1.13x |
| synthetic_url | 16 | 1 | 3.6 | 3.1 | 1.7 | 2.15x | 1.15x |
| synthetic_url | 16 | 2 | 6.9 | 5.5 | 3.1 | 2.19x | 1.26x |
| synthetic_url | 16 | 4 | 12.8 | 11.2 | 6.2 | 2.09x | 1.15x |
| tpch_comment | 12 | 1 | 4.5 | 4.2 | 1.7 | 2.68x | 1.06x |
| tpch_comment | 12 | 2 | 8.6 | 8.1 | 3.2 | 2.66x | 1.07x |
| tpch_comment | 12 | 4 | 15.6 | 14.9 | 6.2 | 2.52x | 1.05x |
| tpch_comment | 16 | 1 | 4.5 | 4.0 | 1.6 | 2.74x | 1.12x |
| tpch_comment | 16 | 2 | 8.6 | 8.0 | 3.2 | 2.68x | 1.07x |
| tpch_comment | 16 | 4 | 15.8 | 14.9 | 6.1 | 2.59x | 1.06x |
| fineweb_text | 12 | 1 | 1.6 | 1.4 | 0.4 | 4.03x | 1.21x |
| fineweb_text | 12 | 2 | 3.2 | 2.7 | 0.8 | 3.96x | 1.19x |
| fineweb_text | 12 | 4 | 6.2 | 5.2 | 1.6 | 3.85x | 1.19x |
| fineweb_text | 16 | 1 | 2.7 | 2.0 | 0.7 | 3.73x | 1.33x |
| fineweb_text | 16 | 2 | 5.3 | 4.0 | 1.5 | 3.62x | 1.32x |
| fineweb_text | 16 | 4 | 9.8 | 7.6 | 2.9 | 3.34x | 1.29x |
| clickbench_url | 12 | 1 | 2.5 | 2.2 | 0.7 | 3.67x | 1.11x |
| clickbench_url | 12 | 2 | 4.8 | 4.3 | 1.3 | 3.61x | 1.10x |
| clickbench_url | 12 | 4 | 8.9 | 8.2 | 2.6 | 3.46x | 1.08x |
| clickbench_url | 16 | 1 | 2.5 | 1.9 | 0.9 | 2.85x | 1.35x |
| clickbench_url | 16 | 2 | 4.8 | 3.7 | 1.8 | 2.77x | 1.32x |
| clickbench_url | 16 | 4 | 9.2 | 7.1 | 3.4 | 2.69x | 1.29x |
| l_comment | 12 | 1 | 3.1 | 2.8 | 0.8 | 3.96x | 1.10x |
| l_comment | 12 | 2 | 5.9 | 5.4 | 1.5 | 3.87x | 1.10x |
| l_comment | 12 | 4 | 11.1 | 10.2 | 3.0 | 3.71x | 1.09x |
| l_comment | 16 | 1 | 2.1 | 1.3 | 0.8 | 2.76x | 1.58x |
| l_comment | 16 | 2 | 4.1 | 2.7 | 1.5 | 2.74x | 1.54x |
| l_comment | 16 | 4 | 7.6 | 5.2 | 3.0 | 2.55x | 1.47x |
| l_shipinstruct | 12 | 1 | 3.6 | 3.1 | 1.0 | 3.61x | 1.15x |
| l_shipinstruct | 12 | 2 | 6.9 | 6.0 | 1.9 | 3.55x | 1.15x |
| l_shipinstruct | 12 | 4 | 12.3 | 11.1 | 3.7 | 3.29x | 1.11x |
| l_shipinstruct | 16 | 1 | 3.5 | 3.1 | 1.0 | 3.57x | 1.15x |
| l_shipinstruct | 16 | 2 | 6.9 | 6.0 | 1.9 | 3.54x | 1.15x |
| l_shipinstruct | 16 | 4 | 12.7 | 11.1 | 3.7 | 3.40x | 1.15x |
| book_reviews | 12 | 1 | 2.0 | 1.8 | 0.5 | 4.44x | 1.15x |
| book_reviews | 12 | 2 | 4.0 | 3.5 | 0.9 | 4.41x | 1.15x |
| book_reviews | 12 | 4 | 7.6 | 6.7 | 1.8 | 4.21x | 1.14x |
| book_reviews | 16 | 1 | 1.6 | 1.1 | 0.5 | 3.03x | 1.46x |
| book_reviews | 16 | 2 | 3.2 | 2.2 | 1.1 | 2.94x | 1.42x |
| book_reviews | 16 | 4 | 5.8 | 4.4 | 2.1 | 2.69x | 1.31x |
