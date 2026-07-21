# OnPair CPU decode microbench — Neoverse-V1

cores/socket: 16, threads/core: 1. Decode throughput (GiB/s of output), byte-identical across layouts. fat = data+code*16 (one independent load + over-copy); entries = variable-stride + over-copy; naive = variable-stride + exact copy (non-over-copying baseline).

| column | bits | thr | fat | entries | naive | fat/naive | fat/entries |
|--|--:|--:|--:|--:|--:|--:|--:|
| synthetic_url | 12 | 1 | 6.5 | 6.0 | 2.8 | 2.38x | 1.09x |
| synthetic_url | 12 | 4 | 22.1 | 21.4 | 10.0 | 2.21x | 1.04x |
| synthetic_url | 12 | 8 | 38.3 | 37.0 | 17.8 | 2.15x | 1.04x |
| synthetic_url | 16 | 1 | 7.1 | 6.6 | 2.8 | 2.59x | 1.07x |
| synthetic_url | 16 | 4 | 24.4 | 22.8 | 10.0 | 2.44x | 1.07x |
| synthetic_url | 16 | 8 | 40.4 | 38.7 | 17.9 | 2.25x | 1.04x |
| tpch_comment | 12 | 1 | 8.4 | 8.1 | 2.4 | 3.45x | 1.04x |
| tpch_comment | 12 | 4 | 28.2 | 28.1 | 8.9 | 3.15x | 1.00x |
| tpch_comment | 12 | 8 | 48.0 | 47.4 | 16.2 | 2.95x | 1.01x |
| tpch_comment | 16 | 1 | 8.3 | 8.2 | 2.5 | 3.39x | 1.01x |
| tpch_comment | 16 | 4 | 28.5 | 26.6 | 8.9 | 3.19x | 1.07x |
| tpch_comment | 16 | 8 | 47.8 | 46.9 | 16.2 | 2.95x | 1.02x |
| fineweb_text | 12 | 1 | 2.2 | 2.2 | 0.5 | 4.09x | 0.97x |
| fineweb_text | 12 | 4 | 8.4 | 8.3 | 2.1 | 4.07x | 1.01x |
| fineweb_text | 12 | 8 | 15.0 | 14.3 | 4.0 | 3.76x | 1.04x |
| fineweb_text | 16 | 1 | 4.1 | 3.0 | 0.9 | 4.35x | 1.37x |
| fineweb_text | 16 | 4 | 14.3 | 10.8 | 3.6 | 3.99x | 1.32x |
| fineweb_text | 16 | 8 | 23.8 | 19.4 | 6.7 | 3.53x | 1.23x |
| clickbench_url | 12 | 1 | 4.1 | 3.8 | 0.9 | 4.74x | 1.09x |
| clickbench_url | 12 | 4 | 15.0 | 13.5 | 3.3 | 4.56x | 1.11x |
| clickbench_url | 12 | 8 | 26.8 | 23.9 | 6.2 | 4.32x | 1.12x |
| clickbench_url | 16 | 1 | 5.0 | 4.3 | 1.2 | 3.98x | 1.16x |
| clickbench_url | 16 | 4 | 17.4 | 15.2 | 4.7 | 3.72x | 1.14x |
| clickbench_url | 16 | 8 | 29.8 | 26.2 | 8.6 | 3.49x | 1.14x |
| l_comment | 12 | 1 | 5.5 | 5.1 | 1.0 | 5.53x | 1.07x |
| l_comment | 12 | 4 | 19.6 | 17.9 | 3.7 | 5.25x | 1.10x |
| l_comment | 12 | 8 | 33.4 | 31.1 | 7.0 | 4.79x | 1.08x |
| l_comment | 16 | 1 | 4.5 | 3.4 | 1.1 | 4.02x | 1.33x |
| l_comment | 16 | 4 | 15.8 | 12.2 | 4.2 | 3.73x | 1.29x |
| l_comment | 16 | 8 | 27.0 | 21.6 | 7.8 | 3.44x | 1.25x |
| l_shipinstruct | 12 | 1 | 6.5 | 6.3 | 1.5 | 4.46x | 1.03x |
| l_shipinstruct | 12 | 4 | 23.2 | 21.8 | 5.5 | 4.22x | 1.06x |
| l_shipinstruct | 12 | 8 | 39.2 | 37.3 | 10.1 | 3.87x | 1.05x |
| l_shipinstruct | 16 | 1 | 6.9 | 6.1 | 1.5 | 4.72x | 1.12x |
| l_shipinstruct | 16 | 4 | 23.2 | 21.8 | 5.5 | 4.25x | 1.07x |
| l_shipinstruct | 16 | 8 | 38.9 | 37.4 | 10.2 | 3.83x | 1.04x |
| book_reviews | 12 | 1 | 3.0 | 2.8 | 0.6 | 5.32x | 1.06x |
| book_reviews | 12 | 4 | 11.2 | 10.0 | 2.2 | 5.12x | 1.12x |
| book_reviews | 12 | 8 | 19.9 | 18.3 | 4.2 | 4.71x | 1.08x |
| book_reviews | 16 | 1 | 3.2 | 2.8 | 0.8 | 4.17x | 1.16x |
| book_reviews | 16 | 4 | 11.4 | 10.0 | 2.9 | 3.87x | 1.13x |
| book_reviews | 16 | 8 | 19.9 | 17.9 | 5.5 | 3.58x | 1.11x |
