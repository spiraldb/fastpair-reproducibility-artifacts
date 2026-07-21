# OnPair CPU decode microbench — AMD EPYC 7R13 Processor

cores/socket: 4, threads/core: 2. Decode throughput (GiB/s of output), byte-identical across layouts. fat = data+code*16 (one independent load + over-copy); entries = variable-stride + over-copy; naive = variable-stride + exact copy (non-over-copying baseline).

| column | bits | thr | fat | entries | naive | fat/naive | fat/entries |
|--|--:|--:|--:|--:|--:|--:|--:|
| synthetic_url | 12 | 1 | 4.1 | 4.0 | 2.3 | 1.75x | 1.03x |
| synthetic_url | 12 | 2 | 7.8 | 7.5 | 4.5 | 1.73x | 1.03x |
| synthetic_url | 12 | 4 | 12.4 | 12.5 | 8.4 | 1.48x | 1.00x |
| synthetic_url | 16 | 1 | 4.7 | 4.3 | 2.3 | 2.01x | 1.07x |
| synthetic_url | 16 | 2 | 9.4 | 8.2 | 4.5 | 2.10x | 1.14x |
| synthetic_url | 16 | 4 | 12.5 | 12.7 | 8.3 | 1.50x | 0.98x |
| tpch_comment | 12 | 1 | 5.5 | 5.2 | 2.3 | 2.42x | 1.04x |
| tpch_comment | 12 | 2 | 10.0 | 9.7 | 4.4 | 2.29x | 1.03x |
| tpch_comment | 12 | 4 | 13.8 | 13.8 | 8.1 | 1.70x | 1.00x |
| tpch_comment | 16 | 1 | 5.5 | 5.2 | 2.2 | 2.46x | 1.05x |
| tpch_comment | 16 | 2 | 10.0 | 9.8 | 4.3 | 2.32x | 1.03x |
| tpch_comment | 16 | 4 | 13.9 | 13.8 | 8.2 | 1.71x | 1.01x |
| fineweb_text | 12 | 1 | 1.5 | 1.5 | 0.6 | 2.78x | 1.02x |
| fineweb_text | 12 | 2 | 3.2 | 2.9 | 1.1 | 2.96x | 1.11x |
| fineweb_text | 12 | 4 | 5.7 | 5.6 | 2.1 | 2.64x | 1.02x |
| fineweb_text | 16 | 1 | 3.2 | 2.5 | 1.0 | 3.26x | 1.31x |
| fineweb_text | 16 | 2 | 6.1 | 4.8 | 1.9 | 3.17x | 1.28x |
| fineweb_text | 16 | 4 | 10.9 | 8.8 | 3.7 | 2.93x | 1.24x |
| clickbench_url | 12 | 1 | 2.7 | 2.6 | 0.9 | 3.02x | 1.01x |
| clickbench_url | 12 | 2 | 5.5 | 5.0 | 1.7 | 3.16x | 1.09x |
| clickbench_url | 12 | 4 | 9.4 | 9.3 | 3.3 | 2.83x | 1.01x |
| clickbench_url | 16 | 1 | 3.9 | 3.4 | 1.2 | 3.21x | 1.16x |
| clickbench_url | 16 | 2 | 7.3 | 6.4 | 2.4 | 3.10x | 1.15x |
| clickbench_url | 16 | 4 | 12.0 | 11.2 | 4.5 | 2.67x | 1.07x |
| l_comment | 12 | 1 | 3.8 | 3.7 | 1.0 | 3.73x | 1.03x |
| l_comment | 12 | 2 | 7.2 | 7.0 | 2.0 | 3.64x | 1.04x |
| l_comment | 12 | 4 | 12.2 | 12.2 | 3.8 | 3.23x | 1.01x |
| l_comment | 16 | 1 | 3.4 | 3.0 | 1.1 | 2.97x | 1.12x |
| l_comment | 16 | 2 | 6.3 | 5.8 | 2.2 | 2.82x | 1.09x |
| l_comment | 16 | 4 | 11.3 | 10.6 | 4.3 | 2.61x | 1.06x |
| l_shipinstruct | 12 | 1 | 4.4 | 4.2 | 1.4 | 3.07x | 1.04x |
| l_shipinstruct | 12 | 2 | 8.2 | 8.0 | 2.8 | 2.94x | 1.02x |
| l_shipinstruct | 12 | 4 | 12.7 | 12.5 | 5.2 | 2.42x | 1.02x |
| l_shipinstruct | 16 | 1 | 4.3 | 4.3 | 1.4 | 3.04x | 1.00x |
| l_shipinstruct | 16 | 2 | 8.3 | 8.0 | 2.8 | 2.98x | 1.04x |
| l_shipinstruct | 16 | 4 | 12.7 | 12.7 | 5.2 | 2.44x | 1.01x |
| book_reviews | 12 | 1 | 2.1 | 2.1 | 0.6 | 3.53x | 1.03x |
| book_reviews | 12 | 2 | 4.2 | 4.1 | 1.2 | 3.45x | 1.01x |
| book_reviews | 12 | 4 | 7.8 | 7.6 | 2.4 | 3.33x | 1.03x |
| book_reviews | 16 | 1 | 2.7 | 2.2 | 0.8 | 3.37x | 1.22x |
| book_reviews | 16 | 2 | 5.0 | 4.3 | 1.6 | 3.22x | 1.16x |
| book_reviews | 16 | 4 | 9.6 | 8.0 | 3.0 | 3.17x | 1.20x |
