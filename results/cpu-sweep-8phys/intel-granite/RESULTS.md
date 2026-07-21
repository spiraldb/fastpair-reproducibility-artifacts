# OnPair CPU decode microbench — Intel(R) Xeon(R) 6975P-C

cores/socket: 8, threads/core: 2. Decode throughput (GiB/s of output), byte-identical across layouts. fat = data+code*16 (one independent load + over-copy); entries = variable-stride + over-copy; naive = variable-stride + exact copy (non-over-copying baseline).

| column | bits | thr | fat | entries | naive | fat/naive | fat/entries |
|--|--:|--:|--:|--:|--:|--:|--:|
| synthetic_url | 12 | 1 | 7.1 | 6.9 | 3.1 | 2.31x | 1.04x |
| synthetic_url | 12 | 4 | 25.1 | 24.1 | 11.7 | 2.15x | 1.04x |
| synthetic_url | 12 | 8 | 41.6 | 38.3 | 22.2 | 1.87x | 1.09x |
| synthetic_url | 16 | 1 | 7.3 | 6.9 | 3.6 | 1.99x | 1.05x |
| synthetic_url | 16 | 4 | 25.4 | 24.0 | 13.6 | 1.87x | 1.06x |
| synthetic_url | 16 | 8 | 42.0 | 40.1 | 25.7 | 1.63x | 1.05x |
| tpch_comment | 12 | 1 | 7.8 | 7.8 | 2.6 | 2.94x | 1.01x |
| tpch_comment | 12 | 4 | 26.3 | 26.2 | 10.0 | 2.63x | 1.00x |
| tpch_comment | 12 | 8 | 42.9 | 42.9 | 19.2 | 2.23x | 1.00x |
| tpch_comment | 16 | 1 | 7.8 | 7.7 | 2.7 | 2.87x | 1.01x |
| tpch_comment | 16 | 4 | 26.4 | 25.7 | 10.2 | 2.59x | 1.03x |
| tpch_comment | 16 | 8 | 43.3 | 42.9 | 19.4 | 2.23x | 1.01x |
| fineweb_text | 12 | 1 | 3.6 | 3.2 | 0.6 | 5.76x | 1.14x |
| fineweb_text | 12 | 4 | 13.6 | 12.8 | 2.5 | 5.47x | 1.06x |
| fineweb_text | 12 | 8 | 24.5 | 24.9 | 4.9 | 5.04x | 0.99x |
| fineweb_text | 16 | 1 | 5.2 | 4.7 | 1.1 | 4.50x | 1.10x |
| fineweb_text | 16 | 4 | 19.0 | 17.1 | 4.4 | 4.32x | 1.11x |
| fineweb_text | 16 | 8 | 33.9 | 31.3 | 8.5 | 3.98x | 1.08x |
| clickbench_url | 12 | 1 | 5.7 | 5.3 | 1.0 | 5.57x | 1.06x |
| clickbench_url | 12 | 4 | 20.7 | 19.5 | 3.9 | 5.30x | 1.06x |
| clickbench_url | 12 | 8 | 36.1 | 34.5 | 7.6 | 4.75x | 1.05x |
| clickbench_url | 16 | 1 | 5.7 | 6.2 | 1.5 | 3.83x | 0.90x |
| clickbench_url | 16 | 4 | 20.8 | 21.8 | 5.7 | 3.67x | 0.95x |
| clickbench_url | 16 | 8 | 36.6 | 37.5 | 11.0 | 3.33x | 0.97x |
| l_comment | 12 | 1 | 6.4 | 6.3 | 1.1 | 5.74x | 1.02x |
| l_comment | 12 | 4 | 23.0 | 22.2 | 4.3 | 5.29x | 1.03x |
| l_comment | 12 | 8 | 38.5 | 38.2 | 8.4 | 4.60x | 1.01x |
| l_comment | 16 | 1 | 5.7 | 5.3 | 1.4 | 3.98x | 1.06x |
| l_comment | 16 | 4 | 20.3 | 18.9 | 5.5 | 3.70x | 1.07x |
| l_comment | 16 | 8 | 35.4 | 34.0 | 10.6 | 3.33x | 1.04x |
| l_shipinstruct | 12 | 1 | 7.5 | 7.3 | 1.7 | 4.44x | 1.02x |
| l_shipinstruct | 12 | 4 | 26.2 | 25.4 | 6.5 | 4.04x | 1.03x |
| l_shipinstruct | 12 | 8 | 42.3 | 40.2 | 12.4 | 3.42x | 1.05x |
| l_shipinstruct | 16 | 1 | 7.5 | 7.4 | 1.7 | 4.43x | 1.01x |
| l_shipinstruct | 16 | 4 | 26.1 | 25.2 | 6.5 | 4.01x | 1.04x |
| l_shipinstruct | 16 | 8 | 42.5 | 41.1 | 12.4 | 3.43x | 1.03x |
| book_reviews | 12 | 1 | 4.5 | 4.2 | 0.7 | 6.94x | 1.08x |
| book_reviews | 12 | 4 | 17.0 | 15.9 | 2.6 | 6.60x | 1.07x |
| book_reviews | 12 | 8 | 30.2 | 28.6 | 5.0 | 6.01x | 1.06x |
| book_reviews | 16 | 1 | 4.8 | 4.4 | 0.9 | 5.24x | 1.08x |
| book_reviews | 16 | 4 | 17.8 | 16.3 | 3.5 | 5.04x | 1.09x |
| book_reviews | 16 | 8 | 32.0 | 29.9 | 6.9 | 4.66x | 1.07x |
