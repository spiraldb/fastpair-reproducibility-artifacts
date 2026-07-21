# OnPair CPU decode microbench — AMD EPYC 7R32

cores/socket: 4, threads/core: 2. Decode throughput (GiB/s of output), byte-identical across layouts. fat = data+code*16 (one independent load + over-copy); entries = variable-stride + over-copy; naive = variable-stride + exact copy (non-over-copying baseline).

| column | bits | thr | fat | entries | naive | fat/naive | fat/entries |
|--|--:|--:|--:|--:|--:|--:|--:|
| synthetic_url | 12 | 1 | 4.0 | 3.8 | 1.7 | 2.34x | 1.06x |
| synthetic_url | 12 | 2 | 7.4 | 7.0 | 3.3 | 2.24x | 1.05x |
| synthetic_url | 12 | 4 | 11.2 | 11.1 | 6.1 | 1.84x | 1.01x |
| synthetic_url | 16 | 1 | 4.4 | 4.0 | 1.9 | 2.30x | 1.10x |
| synthetic_url | 16 | 2 | 7.8 | 7.4 | 3.7 | 2.12x | 1.06x |
| synthetic_url | 16 | 4 | 11.0 | 11.0 | 6.8 | 1.62x | 1.00x |
| tpch_comment | 12 | 1 | 5.0 | 4.5 | 1.9 | 2.70x | 1.11x |
| tpch_comment | 12 | 2 | 9.0 | 8.2 | 3.6 | 2.52x | 1.09x |
| tpch_comment | 12 | 4 | 12.6 | 11.5 | 6.5 | 1.93x | 1.09x |
| tpch_comment | 16 | 1 | 5.1 | 5.0 | 1.9 | 2.79x | 1.03x |
| tpch_comment | 16 | 2 | 9.1 | 8.2 | 3.5 | 2.56x | 1.11x |
| tpch_comment | 16 | 4 | 12.6 | 11.6 | 6.5 | 1.94x | 1.09x |
| fineweb_text | 12 | 1 | 1.8 | 1.7 | 0.5 | 3.92x | 1.06x |
| fineweb_text | 12 | 2 | 3.5 | 3.3 | 0.9 | 3.80x | 1.05x |
| fineweb_text | 12 | 4 | 6.5 | 6.2 | 1.8 | 3.63x | 1.05x |
| fineweb_text | 16 | 1 | 2.4 | 2.0 | 0.8 | 2.94x | 1.23x |
| fineweb_text | 16 | 2 | 4.7 | 3.8 | 1.6 | 2.90x | 1.24x |
| fineweb_text | 16 | 4 | 8.2 | 6.9 | 3.1 | 2.63x | 1.19x |
| clickbench_url | 12 | 1 | 3.0 | 2.6 | 0.7 | 4.35x | 1.15x |
| clickbench_url | 12 | 2 | 5.7 | 4.9 | 1.3 | 4.24x | 1.16x |
| clickbench_url | 12 | 4 | 10.0 | 8.8 | 2.5 | 3.90x | 1.14x |
| clickbench_url | 16 | 1 | 3.4 | 2.9 | 1.0 | 3.28x | 1.16x |
| clickbench_url | 16 | 2 | 6.3 | 5.5 | 2.0 | 3.13x | 1.15x |
| clickbench_url | 16 | 4 | 10.2 | 9.5 | 3.8 | 2.67x | 1.08x |
| l_comment | 12 | 1 | 3.5 | 3.1 | 0.8 | 4.19x | 1.12x |
| l_comment | 12 | 2 | 6.6 | 5.9 | 1.6 | 4.02x | 1.11x |
| l_comment | 12 | 4 | 10.9 | 10.4 | 3.1 | 3.53x | 1.05x |
| l_comment | 16 | 1 | 2.9 | 2.3 | 1.0 | 2.89x | 1.24x |
| l_comment | 16 | 2 | 5.5 | 4.4 | 2.0 | 2.83x | 1.26x |
| l_comment | 16 | 4 | 9.7 | 7.8 | 3.7 | 2.63x | 1.25x |
| l_shipinstruct | 12 | 1 | 4.2 | 4.1 | 1.2 | 3.51x | 1.04x |
| l_shipinstruct | 12 | 2 | 7.7 | 7.5 | 2.3 | 3.31x | 1.02x |
| l_shipinstruct | 12 | 4 | 11.4 | 11.4 | 4.3 | 2.64x | 1.00x |
| l_shipinstruct | 16 | 1 | 4.2 | 4.1 | 1.2 | 3.49x | 1.03x |
| l_shipinstruct | 16 | 2 | 7.7 | 7.6 | 2.3 | 3.30x | 1.01x |
| l_shipinstruct | 16 | 4 | 11.3 | 11.4 | 4.3 | 2.61x | 0.99x |
| book_reviews | 12 | 1 | 2.2 | 2.0 | 0.5 | 4.46x | 1.07x |
| book_reviews | 12 | 2 | 4.2 | 3.9 | 1.0 | 4.37x | 1.08x |
| book_reviews | 12 | 4 | 7.7 | 7.2 | 1.9 | 4.09x | 1.07x |
| book_reviews | 16 | 1 | 2.1 | 1.8 | 0.7 | 3.15x | 1.19x |
| book_reviews | 16 | 2 | 4.1 | 3.4 | 1.3 | 3.07x | 1.20x |
| book_reviews | 16 | 4 | 7.6 | 6.3 | 2.6 | 2.93x | 1.20x |
