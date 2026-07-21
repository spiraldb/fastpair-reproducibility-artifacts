# OnPair CPU decode microbench — Intel(R) Xeon(R) 6975P-C

cores/socket: 4, threads/core: 2. Decode throughput (GiB/s of output), byte-identical across layouts. fat = data+code*16 (one independent load + over-copy); entries = variable-stride + over-copy; naive = variable-stride + exact copy (non-over-copying baseline).

| column | bits | thr | fat | entries | naive | fat/naive | fat/entries |
|--|--:|--:|--:|--:|--:|--:|--:|
| synthetic_url | 12 | 1 | 7.2 | 6.9 | 3.2 | 2.28x | 1.05x |
| synthetic_url | 12 | 2 | 13.7 | 13.1 | 6.2 | 2.22x | 1.05x |
| synthetic_url | 12 | 4 | 25.8 | 24.5 | 12.1 | 2.14x | 1.05x |
| synthetic_url | 16 | 1 | 6.9 | 6.7 | 2.9 | 2.37x | 1.03x |
| synthetic_url | 16 | 2 | 13.4 | 13.0 | 5.7 | 2.36x | 1.03x |
| synthetic_url | 16 | 4 | 24.8 | 24.2 | 11.2 | 2.21x | 1.03x |
| tpch_comment | 12 | 1 | 7.8 | 7.8 | 2.6 | 2.94x | 1.00x |
| tpch_comment | 12 | 2 | 14.6 | 14.7 | 5.2 | 2.82x | 0.99x |
| tpch_comment | 12 | 4 | 27.4 | 26.9 | 10.2 | 2.68x | 1.02x |
| tpch_comment | 16 | 1 | 7.8 | 7.8 | 2.7 | 2.91x | 1.01x |
| tpch_comment | 16 | 2 | 14.4 | 14.3 | 5.2 | 2.75x | 1.00x |
| tpch_comment | 16 | 4 | 27.1 | 27.0 | 10.3 | 2.64x | 1.00x |
| fineweb_text | 12 | 1 | 3.7 | 3.2 | 0.6 | 5.70x | 1.14x |
| fineweb_text | 12 | 2 | 7.1 | 6.2 | 1.3 | 5.54x | 1.14x |
| fineweb_text | 12 | 4 | 13.8 | 12.5 | 2.5 | 5.44x | 1.10x |
| fineweb_text | 16 | 1 | 6.0 | 5.4 | 1.2 | 4.98x | 1.12x |
| fineweb_text | 16 | 2 | 11.6 | 10.1 | 2.4 | 4.89x | 1.15x |
| fineweb_text | 16 | 4 | 21.2 | 19.5 | 4.7 | 4.54x | 1.09x |
| clickbench_url | 12 | 1 | 5.7 | 5.3 | 1.0 | 5.67x | 1.07x |
| clickbench_url | 12 | 2 | 11.0 | 10.3 | 2.0 | 5.55x | 1.07x |
| clickbench_url | 12 | 4 | 21.4 | 19.7 | 3.9 | 5.47x | 1.09x |
| clickbench_url | 16 | 1 | 5.6 | 6.2 | 1.5 | 3.79x | 0.91x |
| clickbench_url | 16 | 2 | 11.1 | 11.9 | 2.9 | 3.83x | 0.93x |
| clickbench_url | 16 | 4 | 21.2 | 22.6 | 5.8 | 3.68x | 0.94x |
| l_comment | 12 | 1 | 6.5 | 6.4 | 1.1 | 5.76x | 1.02x |
| l_comment | 12 | 2 | 12.5 | 12.1 | 2.2 | 5.61x | 1.03x |
| l_comment | 12 | 4 | 23.8 | 22.9 | 4.4 | 5.43x | 1.04x |
| l_comment | 16 | 1 | 5.8 | 5.4 | 1.4 | 4.02x | 1.07x |
| l_comment | 16 | 2 | 11.1 | 10.2 | 2.8 | 3.96x | 1.09x |
| l_comment | 16 | 4 | 21.0 | 19.6 | 5.5 | 3.78x | 1.07x |
| l_shipinstruct | 12 | 1 | 7.6 | 7.4 | 1.7 | 4.51x | 1.03x |
| l_shipinstruct | 12 | 2 | 14.5 | 13.9 | 3.3 | 4.36x | 1.04x |
| l_shipinstruct | 12 | 4 | 26.2 | 25.3 | 6.5 | 4.02x | 1.03x |
| l_shipinstruct | 16 | 1 | 7.6 | 7.4 | 1.7 | 4.52x | 1.03x |
| l_shipinstruct | 16 | 2 | 14.5 | 13.9 | 3.3 | 4.40x | 1.04x |
| l_shipinstruct | 16 | 4 | 26.4 | 25.3 | 6.5 | 4.08x | 1.04x |
| book_reviews | 12 | 1 | 4.7 | 4.2 | 0.7 | 6.93x | 1.09x |
| book_reviews | 12 | 2 | 9.0 | 8.3 | 1.3 | 6.80x | 1.08x |
| book_reviews | 12 | 4 | 17.2 | 16.3 | 2.6 | 6.53x | 1.06x |
| book_reviews | 16 | 1 | 4.8 | 4.5 | 0.9 | 5.31x | 1.08x |
| book_reviews | 16 | 2 | 9.3 | 8.6 | 1.8 | 5.22x | 1.08x |
| book_reviews | 16 | 4 | 18.1 | 16.7 | 3.6 | 5.09x | 1.08x |
