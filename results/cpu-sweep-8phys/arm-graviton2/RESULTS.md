# OnPair CPU decode microbench — Neoverse-N1

cores/socket: 16, threads/core: 1. Decode throughput (GiB/s of output), byte-identical across layouts. fat = data+code*16 (one independent load + over-copy); entries = variable-stride + over-copy; naive = variable-stride + exact copy (non-over-copying baseline).

| column | bits | thr | fat | entries | naive | fat/naive | fat/entries |
|--|--:|--:|--:|--:|--:|--:|--:|
| synthetic_url | 12 | 1 | 3.4 | 3.0 | 1.6 | 2.13x | 1.12x |
| synthetic_url | 12 | 4 | 12.2 | 11.0 | 6.0 | 2.05x | 1.11x |
| synthetic_url | 12 | 8 | 21.2 | 19.4 | 11.0 | 1.92x | 1.09x |
| synthetic_url | 16 | 1 | 3.7 | 3.0 | 1.7 | 2.20x | 1.24x |
| synthetic_url | 16 | 4 | 13.1 | 10.8 | 6.3 | 2.07x | 1.22x |
| synthetic_url | 16 | 8 | 22.9 | 19.0 | 11.5 | 1.99x | 1.21x |
| tpch_comment | 12 | 1 | 4.6 | 4.2 | 1.6 | 2.76x | 1.08x |
| tpch_comment | 12 | 4 | 15.9 | 14.9 | 6.2 | 2.59x | 1.06x |
| tpch_comment | 12 | 8 | 26.9 | 25.9 | 11.3 | 2.38x | 1.04x |
| tpch_comment | 16 | 1 | 4.5 | 4.2 | 1.6 | 2.73x | 1.07x |
| tpch_comment | 16 | 4 | 15.7 | 14.8 | 6.1 | 2.55x | 1.06x |
| tpch_comment | 16 | 8 | 26.9 | 25.7 | 11.3 | 2.39x | 1.05x |
| fineweb_text | 12 | 1 | 1.7 | 1.4 | 0.4 | 4.00x | 1.21x |
| fineweb_text | 12 | 4 | 6.2 | 5.2 | 1.6 | 3.79x | 1.20x |
| fineweb_text | 12 | 8 | 11.3 | 9.4 | 3.2 | 3.57x | 1.21x |
| fineweb_text | 16 | 1 | 2.1 | 1.2 | 0.7 | 3.14x | 1.71x |
| fineweb_text | 16 | 4 | 7.5 | 4.8 | 2.6 | 2.90x | 1.57x |
| fineweb_text | 16 | 8 | 13.5 | 9.1 | 5.0 | 2.73x | 1.49x |
| clickbench_url | 12 | 1 | 2.5 | 2.2 | 0.7 | 3.70x | 1.11x |
| clickbench_url | 12 | 4 | 8.9 | 8.2 | 2.5 | 3.48x | 1.09x |
| clickbench_url | 12 | 8 | 16.0 | 14.8 | 4.9 | 3.29x | 1.08x |
| clickbench_url | 16 | 1 | 2.6 | 2.1 | 0.9 | 2.90x | 1.28x |
| clickbench_url | 16 | 4 | 9.2 | 7.3 | 3.4 | 2.69x | 1.26x |
| clickbench_url | 16 | 8 | 16.8 | 13.3 | 6.5 | 2.60x | 1.26x |
| l_comment | 12 | 1 | 3.1 | 2.8 | 0.8 | 4.03x | 1.11x |
| l_comment | 12 | 4 | 11.2 | 10.3 | 3.0 | 3.77x | 1.09x |
| l_comment | 12 | 8 | 19.7 | 18.3 | 5.6 | 3.50x | 1.08x |
| l_comment | 16 | 1 | 2.3 | 1.4 | 0.8 | 2.99x | 1.69x |
| l_comment | 16 | 4 | 8.2 | 5.0 | 2.9 | 2.84x | 1.63x |
| l_comment | 16 | 8 | 15.2 | 9.4 | 5.6 | 2.70x | 1.61x |
| l_shipinstruct | 12 | 1 | 3.6 | 3.1 | 1.0 | 3.59x | 1.16x |
| l_shipinstruct | 12 | 4 | 12.8 | 11.1 | 3.8 | 3.33x | 1.15x |
| l_shipinstruct | 12 | 8 | 22.3 | 19.6 | 7.2 | 3.12x | 1.14x |
| l_shipinstruct | 16 | 1 | 3.6 | 3.2 | 1.1 | 3.25x | 1.11x |
| l_shipinstruct | 16 | 4 | 12.9 | 11.6 | 4.1 | 3.13x | 1.12x |
| l_shipinstruct | 16 | 8 | 22.6 | 20.3 | 7.6 | 2.95x | 1.11x |
| book_reviews | 12 | 1 | 2.1 | 1.8 | 0.5 | 4.56x | 1.16x |
| book_reviews | 12 | 4 | 7.6 | 6.7 | 1.8 | 4.29x | 1.15x |
| book_reviews | 12 | 8 | 13.7 | 12.2 | 3.5 | 3.97x | 1.12x |
| book_reviews | 16 | 1 | 1.6 | 1.1 | 0.5 | 3.06x | 1.50x |
| book_reviews | 16 | 4 | 6.0 | 4.3 | 2.1 | 2.87x | 1.40x |
| book_reviews | 16 | 8 | 11.5 | 8.2 | 4.0 | 2.86x | 1.41x |
