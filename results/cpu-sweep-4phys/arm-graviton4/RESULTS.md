# OnPair CPU decode microbench — Neoverse-V2

cores/socket: 8, threads/core: 1. Decode throughput (GiB/s of output), byte-identical across layouts. fat = data+code*16 (one independent load + over-copy); entries = variable-stride + over-copy; naive = variable-stride + exact copy (non-over-copying baseline).

| column | bits | thr | fat | entries | naive | fat/naive | fat/entries |
|--|--:|--:|--:|--:|--:|--:|--:|
| synthetic_url | 12 | 1 | 8.2 | 7.0 | 2.9 | 2.84x | 1.17x |
| synthetic_url | 12 | 2 | 15.9 | 13.8 | 5.7 | 2.82x | 1.15x |
| synthetic_url | 12 | 4 | 28.7 | 25.3 | 10.7 | 2.67x | 1.14x |
| synthetic_url | 16 | 1 | 9.9 | 8.3 | 4.3 | 2.31x | 1.19x |
| synthetic_url | 16 | 2 | 18.1 | 15.4 | 8.3 | 2.19x | 1.18x |
| synthetic_url | 16 | 4 | 31.7 | 27.8 | 15.5 | 2.05x | 1.14x |
| tpch_comment | 12 | 1 | 10.7 | 9.4 | 3.0 | 3.56x | 1.15x |
| tpch_comment | 12 | 2 | 19.7 | 17.8 | 5.8 | 3.38x | 1.11x |
| tpch_comment | 12 | 4 | 35.2 | 31.3 | 11.1 | 3.17x | 1.12x |
| tpch_comment | 16 | 1 | 10.4 | 9.3 | 3.0 | 3.48x | 1.12x |
| tpch_comment | 16 | 2 | 19.9 | 17.5 | 5.8 | 3.42x | 1.14x |
| tpch_comment | 16 | 4 | 35.1 | 31.4 | 11.1 | 3.17x | 1.12x |
| fineweb_text | 12 | 1 | 3.1 | 2.4 | 0.6 | 4.95x | 1.27x |
| fineweb_text | 12 | 2 | 6.1 | 5.0 | 1.2 | 4.84x | 1.21x |
| fineweb_text | 12 | 4 | 11.4 | 9.2 | 2.5 | 4.65x | 1.24x |
| fineweb_text | 16 | 1 | 6.8 | 4.7 | 1.4 | 4.98x | 1.44x |
| fineweb_text | 16 | 2 | 13.1 | 9.3 | 2.7 | 4.89x | 1.40x |
| fineweb_text | 16 | 4 | 23.1 | 16.4 | 5.1 | 4.50x | 1.41x |
| clickbench_url | 12 | 1 | 5.5 | 4.2 | 1.1 | 5.14x | 1.30x |
| clickbench_url | 12 | 2 | 10.3 | 8.6 | 2.1 | 4.91x | 1.20x |
| clickbench_url | 12 | 4 | 18.8 | 15.7 | 4.0 | 4.64x | 1.19x |
| clickbench_url | 16 | 1 | 7.1 | 5.7 | 1.6 | 4.49x | 1.26x |
| clickbench_url | 16 | 2 | 14.0 | 10.8 | 3.1 | 4.51x | 1.30x |
| clickbench_url | 16 | 4 | 24.3 | 19.6 | 6.0 | 4.07x | 1.24x |
| l_comment | 12 | 1 | 7.9 | 6.3 | 1.2 | 6.38x | 1.24x |
| l_comment | 12 | 2 | 14.6 | 12.2 | 2.4 | 6.08x | 1.20x |
| l_comment | 12 | 4 | 26.6 | 21.1 | 4.6 | 5.76x | 1.26x |
| l_comment | 16 | 1 | 6.8 | 4.6 | 1.6 | 4.31x | 1.46x |
| l_comment | 16 | 2 | 12.9 | 9.1 | 3.1 | 4.14x | 1.42x |
| l_comment | 16 | 4 | 22.9 | 16.9 | 6.0 | 3.83x | 1.35x |
| l_shipinstruct | 12 | 1 | 8.0 | 7.7 | 1.9 | 4.23x | 1.04x |
| l_shipinstruct | 12 | 2 | 15.9 | 14.7 | 3.7 | 4.28x | 1.08x |
| l_shipinstruct | 12 | 4 | 30.4 | 26.7 | 7.1 | 4.26x | 1.14x |
| l_shipinstruct | 16 | 1 | 8.5 | 8.0 | 1.9 | 4.48x | 1.06x |
| l_shipinstruct | 16 | 2 | 16.2 | 14.9 | 3.7 | 4.38x | 1.09x |
| l_shipinstruct | 16 | 4 | 29.6 | 27.5 | 7.2 | 4.14x | 1.08x |
| book_reviews | 12 | 1 | 4.2 | 3.4 | 0.7 | 6.05x | 1.26x |
| book_reviews | 12 | 2 | 8.4 | 6.4 | 1.4 | 6.02x | 1.30x |
| book_reviews | 12 | 4 | 14.8 | 12.0 | 2.7 | 5.47x | 1.23x |
| book_reviews | 16 | 1 | 4.8 | 3.3 | 1.0 | 4.97x | 1.47x |
| book_reviews | 16 | 2 | 9.4 | 6.5 | 1.9 | 4.90x | 1.46x |
| book_reviews | 16 | 4 | 16.8 | 11.7 | 3.7 | 4.49x | 1.43x |
