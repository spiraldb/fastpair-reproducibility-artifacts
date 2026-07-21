# OnPair CPU decode microbench — Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz

cores/socket: 8, threads/core: 2. Decode throughput (GiB/s of output), byte-identical across layouts. fat = data+code*16 (one independent load + over-copy); entries = variable-stride + over-copy; naive = variable-stride + exact copy (non-over-copying baseline).

| column | bits | thr | fat | entries | naive | fat/naive | fat/entries |
|--|--:|--:|--:|--:|--:|--:|--:|
| synthetic_url | 12 | 1 | 5.5 | 5.2 | 2.1 | 2.57x | 1.06x |
| synthetic_url | 12 | 4 | 18.3 | 17.8 | 8.0 | 2.28x | 1.03x |
| synthetic_url | 12 | 8 | 29.6 | 29.6 | 14.9 | 1.99x | 1.00x |
| synthetic_url | 16 | 1 | 5.8 | 5.3 | 2.1 | 2.80x | 1.09x |
| synthetic_url | 16 | 4 | 18.7 | 18.1 | 7.9 | 2.37x | 1.03x |
| synthetic_url | 16 | 8 | 30.3 | 29.9 | 14.7 | 2.06x | 1.01x |
| tpch_comment | 12 | 1 | 6.7 | 6.5 | 2.1 | 3.21x | 1.04x |
| tpch_comment | 12 | 4 | 21.3 | 20.8 | 7.8 | 2.73x | 1.03x |
| tpch_comment | 12 | 8 | 30.9 | 30.0 | 14.5 | 2.14x | 1.03x |
| tpch_comment | 16 | 1 | 6.1 | 5.7 | 2.0 | 3.01x | 1.07x |
| tpch_comment | 16 | 4 | 19.4 | 18.5 | 7.8 | 2.49x | 1.04x |
| tpch_comment | 16 | 8 | 29.5 | 28.9 | 14.3 | 2.06x | 1.02x |
| fineweb_text | 12 | 1 | 2.8 | 2.5 | 0.5 | 5.33x | 1.11x |
| fineweb_text | 12 | 4 | 10.3 | 9.4 | 2.0 | 5.06x | 1.09x |
| fineweb_text | 12 | 8 | 18.9 | 17.6 | 4.0 | 4.74x | 1.07x |
| fineweb_text | 16 | 1 | 4.7 | 4.0 | 1.0 | 4.92x | 1.20x |
| fineweb_text | 16 | 4 | 16.6 | 14.5 | 3.7 | 4.45x | 1.15x |
| fineweb_text | 16 | 8 | 27.5 | 25.4 | 7.2 | 3.84x | 1.08x |
| clickbench_url | 12 | 1 | 4.3 | 3.8 | 0.8 | 5.74x | 1.15x |
| clickbench_url | 12 | 4 | 15.0 | 13.2 | 3.0 | 5.08x | 1.13x |
| clickbench_url | 12 | 8 | 23.8 | 22.6 | 5.7 | 4.18x | 1.05x |
| clickbench_url | 16 | 1 | 4.1 | 4.3 | 1.1 | 3.68x | 0.95x |
| clickbench_url | 16 | 4 | 13.7 | 14.5 | 4.3 | 3.20x | 0.94x |
| clickbench_url | 16 | 8 | 23.3 | 25.9 | 8.2 | 2.85x | 0.90x |
| l_comment | 12 | 1 | 4.8 | 4.5 | 0.9 | 5.43x | 1.07x |
| l_comment | 12 | 4 | 16.2 | 15.9 | 3.3 | 4.90x | 1.02x |
| l_comment | 12 | 8 | 26.6 | 25.8 | 6.6 | 4.02x | 1.03x |
| l_comment | 16 | 1 | 3.6 | 3.7 | 1.1 | 3.35x | 0.99x |
| l_comment | 16 | 4 | 13.0 | 13.2 | 4.2 | 3.10x | 0.98x |
| l_comment | 16 | 8 | 22.5 | 23.8 | 8.0 | 2.79x | 0.94x |
| l_shipinstruct | 12 | 1 | 5.9 | 5.5 | 1.3 | 4.67x | 1.07x |
| l_shipinstruct | 12 | 4 | 18.0 | 18.2 | 4.8 | 3.75x | 0.99x |
| l_shipinstruct | 12 | 8 | 29.5 | 29.5 | 9.1 | 3.23x | 1.00x |
| l_shipinstruct | 16 | 1 | 5.9 | 5.6 | 1.2 | 4.70x | 1.05x |
| l_shipinstruct | 16 | 4 | 19.5 | 18.6 | 4.8 | 4.04x | 1.05x |
| l_shipinstruct | 16 | 8 | 31.5 | 30.0 | 9.2 | 3.44x | 1.05x |
| book_reviews | 12 | 1 | 3.5 | 3.2 | 0.5 | 6.45x | 1.09x |
| book_reviews | 12 | 4 | 12.8 | 11.7 | 2.1 | 6.05x | 1.10x |
| book_reviews | 12 | 8 | 22.7 | 21.2 | 4.1 | 5.48x | 1.07x |
| book_reviews | 16 | 1 | 3.1 | 2.9 | 0.7 | 4.25x | 1.06x |
| book_reviews | 16 | 4 | 11.6 | 11.0 | 2.9 | 4.03x | 1.05x |
| book_reviews | 16 | 8 | 20.8 | 20.1 | 5.5 | 3.74x | 1.03x |
