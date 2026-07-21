# OnPair CPU decode microbench — Neoverse-V1

cores/socket: 8, threads/core: 1. Decode throughput (GiB/s of output), byte-identical across layouts. fat = data+code*16 (one independent load + over-copy); entries = variable-stride + over-copy; naive = variable-stride + exact copy (non-over-copying baseline).

| column | bits | thr | fat | entries | naive | fat/naive | fat/entries |
|--|--:|--:|--:|--:|--:|--:|--:|
| synthetic_url | 12 | 1 | 6.3 | 5.7 | 2.7 | 2.35x | 1.11x |
| synthetic_url | 12 | 2 | 11.3 | 11.3 | 5.2 | 2.19x | 1.01x |
| synthetic_url | 12 | 4 | 21.8 | 20.4 | 9.8 | 2.21x | 1.07x |
| synthetic_url | 16 | 1 | 7.1 | 6.3 | 2.5 | 2.88x | 1.12x |
| synthetic_url | 16 | 2 | 13.3 | 11.6 | 4.7 | 2.83x | 1.15x |
| synthetic_url | 16 | 4 | 23.7 | 21.2 | 9.0 | 2.63x | 1.12x |
| tpch_comment | 12 | 1 | 8.0 | 7.9 | 2.4 | 3.26x | 1.01x |
| tpch_comment | 12 | 2 | 14.9 | 14.5 | 4.7 | 3.17x | 1.03x |
| tpch_comment | 12 | 4 | 26.7 | 26.2 | 9.0 | 2.98x | 1.02x |
| tpch_comment | 16 | 1 | 7.8 | 7.7 | 2.4 | 3.21x | 1.02x |
| tpch_comment | 16 | 2 | 14.9 | 14.8 | 4.7 | 3.14x | 1.01x |
| tpch_comment | 16 | 4 | 26.9 | 26.2 | 8.9 | 3.00x | 1.02x |
| fineweb_text | 12 | 1 | 2.1 | 2.1 | 0.5 | 4.02x | 0.98x |
| fineweb_text | 12 | 2 | 4.3 | 4.1 | 1.0 | 4.20x | 1.05x |
| fineweb_text | 12 | 4 | 8.2 | 8.0 | 2.0 | 4.04x | 1.03x |
| fineweb_text | 16 | 1 | 5.2 | 4.1 | 1.1 | 4.94x | 1.28x |
| fineweb_text | 16 | 2 | 9.7 | 7.9 | 2.1 | 4.66x | 1.22x |
| fineweb_text | 16 | 4 | 18.4 | 14.7 | 4.0 | 4.61x | 1.26x |
| clickbench_url | 12 | 1 | 4.1 | 3.8 | 0.9 | 4.76x | 1.08x |
| clickbench_url | 12 | 2 | 7.9 | 7.5 | 1.7 | 4.65x | 1.05x |
| clickbench_url | 12 | 4 | 15.5 | 13.9 | 3.3 | 4.71x | 1.12x |
| clickbench_url | 16 | 1 | 4.5 | 3.9 | 1.2 | 3.78x | 1.16x |
| clickbench_url | 16 | 2 | 8.7 | 7.6 | 2.4 | 3.70x | 1.14x |
| clickbench_url | 16 | 4 | 15.8 | 14.2 | 4.5 | 3.50x | 1.11x |
| l_comment | 12 | 1 | 5.6 | 4.9 | 1.0 | 5.65x | 1.14x |
| l_comment | 12 | 2 | 10.4 | 9.8 | 1.9 | 5.36x | 1.07x |
| l_comment | 12 | 4 | 19.5 | 17.9 | 3.7 | 5.22x | 1.09x |
| l_comment | 16 | 1 | 4.4 | 3.0 | 1.1 | 3.97x | 1.45x |
| l_comment | 16 | 2 | 8.2 | 5.7 | 2.1 | 3.89x | 1.44x |
| l_comment | 16 | 4 | 15.0 | 10.8 | 4.1 | 3.65x | 1.40x |
| l_shipinstruct | 12 | 1 | 6.7 | 6.2 | 1.5 | 4.56x | 1.09x |
| l_shipinstruct | 12 | 2 | 12.0 | 11.9 | 2.9 | 4.17x | 1.01x |
| l_shipinstruct | 12 | 4 | 22.7 | 21.2 | 5.5 | 4.11x | 1.07x |
| l_shipinstruct | 16 | 1 | 6.4 | 6.5 | 1.5 | 4.30x | 0.98x |
| l_shipinstruct | 16 | 2 | 12.2 | 11.6 | 2.9 | 4.22x | 1.05x |
| l_shipinstruct | 16 | 4 | 22.3 | 21.9 | 5.5 | 4.03x | 1.01x |
| book_reviews | 12 | 1 | 3.0 | 2.9 | 0.6 | 5.19x | 1.03x |
| book_reviews | 12 | 2 | 6.1 | 5.4 | 1.1 | 5.37x | 1.13x |
| book_reviews | 12 | 4 | 11.1 | 10.5 | 2.2 | 4.98x | 1.06x |
| book_reviews | 16 | 1 | 3.1 | 2.6 | 0.8 | 4.09x | 1.20x |
| book_reviews | 16 | 2 | 5.9 | 5.0 | 1.5 | 3.98x | 1.19x |
| book_reviews | 16 | 4 | 11.0 | 9.4 | 2.9 | 3.79x | 1.16x |
