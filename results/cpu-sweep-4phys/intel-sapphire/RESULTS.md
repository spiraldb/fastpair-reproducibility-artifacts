# OnPair CPU decode microbench — Intel(R) Xeon(R) Platinum 8488C

cores/socket: 4, threads/core: 2. Decode throughput (GiB/s of output), byte-identical across layouts. fat = data+code*16 (one independent load + over-copy); entries = variable-stride + over-copy; naive = variable-stride + exact copy (non-over-copying baseline).

| column | bits | thr | fat | entries | naive | fat/naive | fat/entries |
|--|--:|--:|--:|--:|--:|--:|--:|
| synthetic_url | 12 | 1 | 7.5 | 7.1 | 3.0 | 2.54x | 1.05x |
| synthetic_url | 12 | 2 | 14.8 | 13.6 | 5.8 | 2.54x | 1.09x |
| synthetic_url | 12 | 4 | 26.6 | 26.1 | 11.3 | 2.35x | 1.02x |
| synthetic_url | 16 | 1 | 7.4 | 7.1 | 4.0 | 1.82x | 1.03x |
| synthetic_url | 16 | 2 | 14.3 | 13.9 | 8.0 | 1.80x | 1.03x |
| synthetic_url | 16 | 4 | 26.3 | 25.4 | 15.2 | 1.73x | 1.04x |
| tpch_comment | 12 | 1 | 8.4 | 7.9 | 2.6 | 3.25x | 1.06x |
| tpch_comment | 12 | 2 | 15.9 | 15.0 | 5.1 | 3.11x | 1.06x |
| tpch_comment | 12 | 4 | 29.5 | 27.6 | 9.9 | 2.98x | 1.07x |
| tpch_comment | 16 | 1 | 8.3 | 7.9 | 2.6 | 3.21x | 1.05x |
| tpch_comment | 16 | 2 | 15.9 | 15.2 | 5.1 | 3.12x | 1.05x |
| tpch_comment | 16 | 4 | 29.2 | 27.6 | 9.8 | 2.97x | 1.06x |
| fineweb_text | 12 | 1 | 4.0 | 3.4 | 0.6 | 6.64x | 1.18x |
| fineweb_text | 12 | 2 | 7.9 | 6.8 | 1.2 | 6.55x | 1.17x |
| fineweb_text | 12 | 4 | 14.9 | 12.9 | 2.4 | 6.23x | 1.15x |
| fineweb_text | 16 | 1 | 6.1 | 5.3 | 1.1 | 5.28x | 1.15x |
| fineweb_text | 16 | 2 | 11.7 | 10.2 | 2.3 | 5.14x | 1.15x |
| fineweb_text | 16 | 4 | 21.9 | 19.4 | 4.5 | 4.89x | 1.13x |
| clickbench_url | 12 | 1 | 6.4 | 5.6 | 0.9 | 7.22x | 1.14x |
| clickbench_url | 12 | 2 | 12.4 | 10.8 | 1.8 | 7.08x | 1.14x |
| clickbench_url | 12 | 4 | 23.4 | 20.4 | 3.5 | 6.77x | 1.14x |
| clickbench_url | 16 | 1 | 5.9 | 6.2 | 1.4 | 4.24x | 0.95x |
| clickbench_url | 16 | 2 | 11.5 | 12.0 | 2.8 | 4.14x | 0.96x |
| clickbench_url | 16 | 4 | 21.5 | 23.4 | 5.5 | 3.94x | 0.92x |
| l_comment | 12 | 1 | 7.0 | 6.7 | 1.1 | 6.66x | 1.04x |
| l_comment | 12 | 2 | 13.6 | 13.1 | 2.1 | 6.53x | 1.04x |
| l_comment | 12 | 4 | 25.2 | 23.8 | 4.1 | 6.16x | 1.06x |
| l_comment | 16 | 1 | 5.9 | 5.3 | 1.3 | 4.52x | 1.11x |
| l_comment | 16 | 2 | 11.5 | 10.3 | 2.6 | 4.45x | 1.12x |
| l_comment | 16 | 4 | 21.4 | 19.6 | 5.0 | 4.25x | 1.09x |
| l_shipinstruct | 12 | 1 | 8.1 | 7.6 | 1.6 | 5.09x | 1.06x |
| l_shipinstruct | 12 | 2 | 15.4 | 14.3 | 3.1 | 4.96x | 1.07x |
| l_shipinstruct | 12 | 4 | 28.7 | 26.0 | 6.1 | 4.71x | 1.11x |
| l_shipinstruct | 16 | 1 | 8.0 | 7.7 | 1.6 | 5.09x | 1.04x |
| l_shipinstruct | 16 | 2 | 15.5 | 14.6 | 3.1 | 5.02x | 1.06x |
| l_shipinstruct | 16 | 4 | 28.2 | 26.5 | 6.1 | 4.64x | 1.06x |
| book_reviews | 12 | 1 | 5.0 | 4.3 | 0.6 | 8.23x | 1.18x |
| book_reviews | 12 | 2 | 9.9 | 8.4 | 1.2 | 8.08x | 1.18x |
| book_reviews | 12 | 4 | 18.4 | 15.9 | 2.4 | 7.57x | 1.16x |
| book_reviews | 16 | 1 | 4.9 | 4.2 | 0.9 | 5.67x | 1.15x |
| book_reviews | 16 | 2 | 9.5 | 8.1 | 1.7 | 5.58x | 1.17x |
| book_reviews | 16 | 4 | 18.1 | 15.6 | 3.4 | 5.38x | 1.16x |
