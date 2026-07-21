# OnPair CPU decode microbench — AMD EPYC 9R14

cores/socket: 16, threads/core: 1. Decode throughput (GiB/s of output), byte-identical across layouts. fat = data+code*16 (one independent load + over-copy); entries = variable-stride + over-copy; naive = variable-stride + exact copy (non-over-copying baseline).

| column | bits | thr | fat | entries | naive | fat/naive | fat/entries |
|--|--:|--:|--:|--:|--:|--:|--:|
| synthetic_url | 12 | 1 | 5.5 | 4.8 | 2.6 | 2.16x | 1.14x |
| synthetic_url | 12 | 4 | 15.9 | 15.4 | 10.0 | 1.60x | 1.03x |
| synthetic_url | 12 | 8 | 19.3 | 19.1 | 15.4 | 1.25x | 1.01x |
| synthetic_url | 16 | 1 | 5.6 | 5.2 | 2.4 | 2.33x | 1.08x |
| synthetic_url | 16 | 4 | 15.8 | 15.3 | 8.8 | 1.79x | 1.03x |
| synthetic_url | 16 | 8 | 19.0 | 18.8 | 15.0 | 1.27x | 1.01x |
| tpch_comment | 12 | 1 | 6.3 | 5.5 | 2.3 | 2.69x | 1.15x |
| tpch_comment | 12 | 4 | 16.4 | 16.1 | 8.5 | 1.93x | 1.02x |
| tpch_comment | 12 | 8 | 19.5 | 19.2 | 15.0 | 1.30x | 1.02x |
| tpch_comment | 16 | 1 | 6.0 | 5.5 | 2.3 | 2.62x | 1.09x |
| tpch_comment | 16 | 4 | 16.5 | 16.1 | 8.5 | 1.94x | 1.03x |
| tpch_comment | 16 | 8 | 19.5 | 19.2 | 14.8 | 1.31x | 1.02x |
| fineweb_text | 12 | 1 | 2.7 | 2.3 | 0.6 | 4.62x | 1.18x |
| fineweb_text | 12 | 4 | 10.5 | 8.4 | 2.2 | 4.67x | 1.25x |
| fineweb_text | 12 | 8 | 16.8 | 14.6 | 4.3 | 3.92x | 1.15x |
| fineweb_text | 16 | 1 | 3.8 | 3.5 | 1.1 | 3.36x | 1.08x |
| fineweb_text | 16 | 4 | 13.5 | 12.4 | 4.3 | 3.12x | 1.09x |
| fineweb_text | 16 | 8 | 17.8 | 17.7 | 7.9 | 2.25x | 1.01x |
| clickbench_url | 12 | 1 | 4.0 | 3.5 | 0.9 | 4.40x | 1.14x |
| clickbench_url | 12 | 4 | 13.6 | 12.7 | 3.5 | 3.90x | 1.07x |
| clickbench_url | 12 | 8 | 17.8 | 17.6 | 6.5 | 2.75x | 1.02x |
| clickbench_url | 16 | 1 | 4.3 | 3.9 | 1.3 | 3.29x | 1.12x |
| clickbench_url | 16 | 4 | 13.9 | 13.4 | 4.9 | 2.84x | 1.04x |
| clickbench_url | 16 | 8 | 18.2 | 17.7 | 8.9 | 2.03x | 1.03x |
| l_comment | 12 | 1 | 4.8 | 4.0 | 1.1 | 4.53x | 1.21x |
| l_comment | 12 | 4 | 15.3 | 13.8 | 4.0 | 3.86x | 1.11x |
| l_comment | 12 | 8 | 19.1 | 17.7 | 7.3 | 2.60x | 1.08x |
| l_comment | 16 | 1 | 3.7 | 3.5 | 1.2 | 2.97x | 1.06x |
| l_comment | 16 | 4 | 12.9 | 12.4 | 4.7 | 2.74x | 1.04x |
| l_comment | 16 | 8 | 17.6 | 17.3 | 8.6 | 2.04x | 1.02x |
| l_shipinstruct | 12 | 1 | 6.8 | 6.2 | 1.5 | 4.55x | 1.10x |
| l_shipinstruct | 12 | 4 | 16.2 | 16.2 | 5.9 | 2.73x | 1.00x |
| l_shipinstruct | 12 | 8 | 19.5 | 19.4 | 9.9 | 1.97x | 1.00x |
| l_shipinstruct | 16 | 1 | 6.6 | 6.2 | 1.5 | 4.47x | 1.06x |
| l_shipinstruct | 16 | 4 | 16.2 | 16.2 | 6.0 | 2.71x | 1.00x |
| l_shipinstruct | 16 | 8 | 19.7 | 19.4 | 9.9 | 1.99x | 1.02x |
| book_reviews | 12 | 1 | 3.4 | 2.9 | 0.6 | 5.32x | 1.18x |
| book_reviews | 12 | 4 | 12.2 | 10.7 | 2.5 | 4.92x | 1.14x |
| book_reviews | 12 | 8 | 17.4 | 16.9 | 4.7 | 3.70x | 1.03x |
| book_reviews | 16 | 1 | 3.2 | 2.9 | 0.9 | 3.67x | 1.11x |
| book_reviews | 16 | 4 | 11.3 | 9.6 | 3.3 | 3.43x | 1.18x |
| book_reviews | 16 | 8 | 17.1 | 16.9 | 6.2 | 2.75x | 1.01x |
