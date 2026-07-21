# OnPair CPU decode microbench — Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz

cores/socket: 4, threads/core: 2. Decode throughput (GiB/s of output), byte-identical across layouts. fat = data+code*16 (one independent load + over-copy); entries = variable-stride + over-copy; naive = variable-stride + exact copy (non-over-copying baseline).

| column | bits | thr | fat | entries | naive | fat/naive | fat/entries |
|--|--:|--:|--:|--:|--:|--:|--:|
| synthetic_url | 12 | 1 | 5.6 | 5.3 | 2.2 | 2.55x | 1.06x |
| synthetic_url | 12 | 2 | 10.7 | 10.1 | 4.3 | 2.48x | 1.06x |
| synthetic_url | 12 | 4 | 18.8 | 18.1 | 8.7 | 2.16x | 1.04x |
| synthetic_url | 16 | 1 | 6.3 | 5.8 | 2.9 | 2.18x | 1.09x |
| synthetic_url | 16 | 2 | 11.7 | 10.9 | 5.6 | 2.07x | 1.07x |
| synthetic_url | 16 | 4 | 20.7 | 19.2 | 10.8 | 1.91x | 1.07x |
| tpch_comment | 12 | 1 | 6.7 | 6.4 | 2.1 | 3.17x | 1.04x |
| tpch_comment | 12 | 2 | 12.4 | 12.1 | 4.1 | 3.03x | 1.02x |
| tpch_comment | 12 | 4 | 21.4 | 21.1 | 8.0 | 2.69x | 1.02x |
| tpch_comment | 16 | 1 | 6.6 | 6.4 | 2.1 | 3.16x | 1.03x |
| tpch_comment | 16 | 2 | 12.4 | 12.1 | 4.1 | 3.05x | 1.03x |
| tpch_comment | 16 | 4 | 21.5 | 20.9 | 7.8 | 2.74x | 1.03x |
| fineweb_text | 12 | 1 | 2.8 | 2.6 | 0.5 | 5.57x | 1.11x |
| fineweb_text | 12 | 2 | 5.5 | 5.0 | 1.0 | 5.41x | 1.09x |
| fineweb_text | 12 | 4 | 10.5 | 9.6 | 2.0 | 5.23x | 1.09x |
| fineweb_text | 16 | 1 | 4.8 | 4.0 | 1.0 | 5.03x | 1.21x |
| fineweb_text | 16 | 2 | 9.2 | 7.6 | 1.9 | 4.86x | 1.21x |
| fineweb_text | 16 | 4 | 16.8 | 14.5 | 3.7 | 4.52x | 1.16x |
| clickbench_url | 12 | 1 | 4.5 | 3.9 | 0.8 | 5.71x | 1.14x |
| clickbench_url | 12 | 2 | 8.6 | 7.5 | 1.5 | 5.57x | 1.14x |
| clickbench_url | 12 | 4 | 15.8 | 14.2 | 3.0 | 5.21x | 1.11x |
| clickbench_url | 16 | 1 | 4.5 | 4.4 | 1.1 | 3.99x | 1.03x |
| clickbench_url | 16 | 2 | 8.4 | 8.5 | 2.2 | 3.74x | 0.99x |
| clickbench_url | 16 | 4 | 15.1 | 16.4 | 4.4 | 3.45x | 0.92x |
| l_comment | 12 | 1 | 5.2 | 4.8 | 0.9 | 5.83x | 1.09x |
| l_comment | 12 | 2 | 9.8 | 9.0 | 1.8 | 5.61x | 1.09x |
| l_comment | 12 | 4 | 17.6 | 16.6 | 3.4 | 5.10x | 1.06x |
| l_comment | 16 | 1 | 3.8 | 3.8 | 1.1 | 3.46x | 1.00x |
| l_comment | 16 | 2 | 7.3 | 7.3 | 2.1 | 3.40x | 1.00x |
| l_comment | 16 | 4 | 13.8 | 13.8 | 4.2 | 3.27x | 1.00x |
| l_shipinstruct | 12 | 1 | 6.3 | 5.8 | 1.3 | 4.99x | 1.09x |
| l_shipinstruct | 12 | 2 | 11.8 | 11.0 | 2.5 | 4.74x | 1.08x |
| l_shipinstruct | 12 | 4 | 20.4 | 19.1 | 4.8 | 4.22x | 1.07x |
| l_shipinstruct | 16 | 1 | 6.4 | 5.8 | 1.3 | 5.08x | 1.12x |
| l_shipinstruct | 16 | 2 | 11.8 | 10.8 | 2.5 | 4.74x | 1.09x |
| l_shipinstruct | 16 | 4 | 20.4 | 19.0 | 4.9 | 4.15x | 1.07x |
| book_reviews | 12 | 1 | 3.6 | 3.2 | 0.5 | 6.73x | 1.12x |
| book_reviews | 12 | 2 | 6.9 | 6.2 | 1.1 | 6.49x | 1.10x |
| book_reviews | 12 | 4 | 12.9 | 11.8 | 2.1 | 6.17x | 1.09x |
| book_reviews | 16 | 1 | 3.2 | 3.0 | 0.7 | 4.36x | 1.08x |
| book_reviews | 16 | 2 | 6.2 | 5.7 | 1.4 | 4.33x | 1.09x |
| book_reviews | 16 | 4 | 11.9 | 11.0 | 2.9 | 4.17x | 1.08x |
