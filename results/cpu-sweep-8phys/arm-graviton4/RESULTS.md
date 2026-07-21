# OnPair CPU decode microbench — Neoverse-V2

cores/socket: 16, threads/core: 1. Decode throughput (GiB/s of output), byte-identical across layouts. fat = data+code*16 (one independent load + over-copy); entries = variable-stride + over-copy; naive = variable-stride + exact copy (non-over-copying baseline).

| column | bits | thr | fat | entries | naive | fat/naive | fat/entries |
|--|--:|--:|--:|--:|--:|--:|--:|
| synthetic_url | 12 | 1 | 8.5 | 7.2 | 2.9 | 2.93x | 1.19x |
| synthetic_url | 12 | 4 | 28.6 | 25.0 | 10.8 | 2.65x | 1.14x |
| synthetic_url | 12 | 8 | 48.7 | 43.3 | 19.6 | 2.48x | 1.12x |
| synthetic_url | 16 | 1 | 9.6 | 7.8 | 3.4 | 2.87x | 1.22x |
| synthetic_url | 16 | 4 | 32.6 | 27.3 | 12.3 | 2.65x | 1.19x |
| synthetic_url | 16 | 8 | 53.0 | 44.8 | 22.1 | 2.40x | 1.19x |
| tpch_comment | 12 | 1 | 10.8 | 9.4 | 3.0 | 3.60x | 1.14x |
| tpch_comment | 12 | 4 | 36.3 | 32.6 | 11.1 | 3.27x | 1.11x |
| tpch_comment | 12 | 8 | 60.1 | 54.2 | 20.0 | 3.01x | 1.11x |
| tpch_comment | 16 | 1 | 10.6 | 9.3 | 3.0 | 3.57x | 1.14x |
| tpch_comment | 16 | 4 | 35.5 | 32.3 | 11.0 | 3.23x | 1.10x |
| tpch_comment | 16 | 8 | 59.8 | 53.3 | 20.1 | 2.98x | 1.12x |
| fineweb_text | 12 | 1 | 2.8 | 2.6 | 0.6 | 4.54x | 1.09x |
| fineweb_text | 12 | 4 | 11.3 | 9.7 | 2.4 | 4.68x | 1.17x |
| fineweb_text | 12 | 8 | 19.6 | 17.0 | 4.6 | 4.22x | 1.15x |
| fineweb_text | 16 | 1 | 5.7 | 3.9 | 1.2 | 4.65x | 1.49x |
| fineweb_text | 16 | 4 | 20.7 | 14.0 | 4.6 | 4.46x | 1.48x |
| fineweb_text | 16 | 8 | 34.5 | 24.2 | 8.5 | 4.06x | 1.43x |
| clickbench_url | 12 | 1 | 5.5 | 4.5 | 1.1 | 5.09x | 1.23x |
| clickbench_url | 12 | 4 | 20.3 | 16.3 | 4.1 | 4.97x | 1.25x |
| clickbench_url | 12 | 8 | 34.5 | 29.1 | 7.6 | 4.52x | 1.19x |
| clickbench_url | 16 | 1 | 7.1 | 5.7 | 1.6 | 4.51x | 1.26x |
| clickbench_url | 16 | 4 | 25.5 | 19.8 | 5.9 | 4.31x | 1.28x |
| clickbench_url | 16 | 8 | 42.0 | 34.1 | 11.0 | 3.84x | 1.23x |
| l_comment | 12 | 1 | 8.0 | 6.3 | 1.2 | 6.51x | 1.28x |
| l_comment | 12 | 4 | 27.1 | 23.1 | 4.6 | 5.89x | 1.17x |
| l_comment | 12 | 8 | 45.0 | 38.0 | 8.5 | 5.31x | 1.19x |
| l_comment | 16 | 1 | 6.8 | 4.9 | 1.6 | 4.28x | 1.39x |
| l_comment | 16 | 4 | 24.1 | 17.1 | 6.0 | 4.02x | 1.40x |
| l_comment | 16 | 8 | 40.3 | 30.3 | 11.1 | 3.65x | 1.33x |
| l_shipinstruct | 12 | 1 | 8.1 | 7.9 | 1.9 | 4.25x | 1.02x |
| l_shipinstruct | 12 | 4 | 29.6 | 27.9 | 7.1 | 4.17x | 1.06x |
| l_shipinstruct | 12 | 8 | 50.3 | 46.6 | 13.1 | 3.84x | 1.08x |
| l_shipinstruct | 16 | 1 | 8.9 | 7.5 | 1.9 | 4.70x | 1.19x |
| l_shipinstruct | 16 | 4 | 28.9 | 27.9 | 7.2 | 4.04x | 1.03x |
| l_shipinstruct | 16 | 8 | 50.0 | 46.4 | 13.1 | 3.81x | 1.08x |
| book_reviews | 12 | 1 | 4.1 | 3.4 | 0.7 | 5.84x | 1.19x |
| book_reviews | 12 | 4 | 15.1 | 12.6 | 2.7 | 5.60x | 1.20x |
| book_reviews | 12 | 8 | 26.2 | 22.4 | 5.2 | 5.08x | 1.17x |
| book_reviews | 16 | 1 | 4.9 | 3.2 | 1.0 | 5.08x | 1.52x |
| book_reviews | 16 | 4 | 17.5 | 12.1 | 3.7 | 4.74x | 1.45x |
| book_reviews | 16 | 8 | 29.9 | 21.1 | 7.0 | 4.30x | 1.42x |
