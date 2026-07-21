# OnPair CPU decode microbench — Intel(R) Xeon(R) Platinum 8488C

cores/socket: 8, threads/core: 2. Decode throughput (GiB/s of output), byte-identical across layouts. fat = data+code*16 (one independent load + over-copy); entries = variable-stride + over-copy; naive = variable-stride + exact copy (non-over-copying baseline).

| column | bits | thr | fat | entries | naive | fat/naive | fat/entries |
|--|--:|--:|--:|--:|--:|--:|--:|
| synthetic_url | 12 | 1 | 7.5 | 7.2 | 2.7 | 2.79x | 1.04x |
| synthetic_url | 12 | 4 | 27.0 | 26.1 | 10.3 | 2.61x | 1.04x |
| synthetic_url | 12 | 8 | 44.9 | 43.3 | 19.2 | 2.33x | 1.04x |
| synthetic_url | 16 | 1 | 6.5 | 6.9 | 2.9 | 2.27x | 0.94x |
| synthetic_url | 16 | 4 | 24.1 | 25.1 | 11.0 | 2.20x | 0.96x |
| synthetic_url | 16 | 8 | 40.5 | 42.2 | 20.3 | 1.99x | 0.96x |
| tpch_comment | 12 | 1 | 8.3 | 7.8 | 2.5 | 3.30x | 1.06x |
| tpch_comment | 12 | 4 | 29.8 | 27.9 | 9.7 | 3.07x | 1.07x |
| tpch_comment | 12 | 8 | 48.1 | 45.5 | 18.1 | 2.65x | 1.06x |
| tpch_comment | 16 | 1 | 8.3 | 7.8 | 2.5 | 3.30x | 1.06x |
| tpch_comment | 16 | 4 | 29.5 | 27.8 | 9.7 | 3.04x | 1.06x |
| tpch_comment | 16 | 8 | 47.8 | 45.1 | 18.1 | 2.63x | 1.06x |
| fineweb_text | 12 | 1 | 4.0 | 3.4 | 0.6 | 6.79x | 1.18x |
| fineweb_text | 12 | 4 | 14.8 | 12.9 | 2.3 | 6.38x | 1.15x |
| fineweb_text | 12 | 8 | 27.0 | 23.9 | 4.5 | 6.04x | 1.13x |
| fineweb_text | 16 | 1 | 6.0 | 5.2 | 1.1 | 5.37x | 1.15x |
| fineweb_text | 16 | 4 | 21.8 | 19.4 | 4.4 | 4.98x | 1.12x |
| fineweb_text | 16 | 8 | 37.8 | 34.5 | 8.2 | 4.59x | 1.10x |
| clickbench_url | 12 | 1 | 6.0 | 5.5 | 0.9 | 6.96x | 1.10x |
| clickbench_url | 12 | 4 | 23.2 | 20.2 | 3.4 | 6.84x | 1.15x |
| clickbench_url | 12 | 8 | 36.6 | 35.7 | 6.5 | 5.67x | 1.02x |
| clickbench_url | 16 | 1 | 5.8 | 6.0 | 1.3 | 4.47x | 0.96x |
| clickbench_url | 16 | 4 | 21.4 | 22.1 | 5.0 | 4.27x | 0.97x |
| clickbench_url | 16 | 8 | 36.7 | 38.1 | 9.4 | 3.91x | 0.96x |
| l_comment | 12 | 1 | 6.9 | 6.3 | 1.0 | 6.70x | 1.09x |
| l_comment | 12 | 4 | 24.9 | 22.8 | 4.0 | 6.25x | 1.09x |
| l_comment | 12 | 8 | 42.2 | 38.9 | 7.6 | 5.58x | 1.09x |
| l_comment | 16 | 1 | 5.8 | 5.3 | 1.3 | 4.59x | 1.10x |
| l_comment | 16 | 4 | 21.3 | 19.4 | 4.9 | 4.31x | 1.09x |
| l_comment | 16 | 8 | 36.9 | 34.5 | 9.2 | 3.99x | 1.07x |
| l_shipinstruct | 12 | 1 | 8.0 | 7.5 | 1.5 | 5.24x | 1.07x |
| l_shipinstruct | 12 | 4 | 28.8 | 26.9 | 6.0 | 4.83x | 1.07x |
| l_shipinstruct | 12 | 8 | 46.7 | 43.9 | 11.2 | 4.17x | 1.06x |
| l_shipinstruct | 16 | 1 | 8.1 | 7.5 | 1.5 | 5.26x | 1.08x |
| l_shipinstruct | 16 | 4 | 28.9 | 26.7 | 6.0 | 4.84x | 1.08x |
| l_shipinstruct | 16 | 8 | 46.8 | 43.8 | 11.2 | 4.17x | 1.07x |
| book_reviews | 12 | 1 | 5.0 | 4.2 | 0.6 | 8.13x | 1.18x |
| book_reviews | 12 | 4 | 18.7 | 15.9 | 2.4 | 7.68x | 1.18x |
| book_reviews | 12 | 8 | 32.7 | 28.7 | 4.7 | 6.99x | 1.14x |
| book_reviews | 16 | 1 | 4.6 | 4.2 | 0.8 | 5.50x | 1.11x |
| book_reviews | 16 | 4 | 17.2 | 15.5 | 3.3 | 5.22x | 1.11x |
| book_reviews | 16 | 8 | 30.6 | 28.3 | 6.3 | 4.87x | 1.08x |
