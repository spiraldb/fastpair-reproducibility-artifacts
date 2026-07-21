# OnPair CPU decode microbench — AMD EPYC 7R32

cores/socket: 8, threads/core: 2. Decode throughput (GiB/s of output), byte-identical across layouts. fat = data+code*16 (one independent load + over-copy); entries = variable-stride + over-copy; naive = variable-stride + exact copy (non-over-copying baseline).

| column | bits | thr | fat | entries | naive | fat/naive | fat/entries |
|--|--:|--:|--:|--:|--:|--:|--:|
| synthetic_url | 12 | 1 | 4.1 | 3.9 | 2.0 | 2.03x | 1.07x |
| synthetic_url | 12 | 4 | 11.6 | 11.0 | 7.1 | 1.63x | 1.06x |
| synthetic_url | 12 | 8 | 14.1 | 13.9 | 11.7 | 1.21x | 1.01x |
| synthetic_url | 16 | 1 | 4.4 | 4.2 | 1.9 | 2.27x | 1.04x |
| synthetic_url | 16 | 4 | 11.7 | 11.5 | 6.9 | 1.70x | 1.02x |
| synthetic_url | 16 | 8 | 13.9 | 13.9 | 11.5 | 1.21x | 1.00x |
| tpch_comment | 12 | 1 | 5.2 | 5.1 | 1.9 | 2.79x | 1.03x |
| tpch_comment | 12 | 4 | 12.8 | 11.7 | 6.6 | 1.94x | 1.09x |
| tpch_comment | 12 | 8 | 14.9 | 14.9 | 11.2 | 1.33x | 1.00x |
| tpch_comment | 16 | 1 | 5.1 | 4.9 | 1.8 | 2.81x | 1.06x |
| tpch_comment | 16 | 4 | 13.0 | 11.9 | 6.4 | 2.02x | 1.09x |
| tpch_comment | 16 | 8 | 14.9 | 13.9 | 11.0 | 1.35x | 1.07x |
| fineweb_text | 12 | 1 | 1.8 | 1.7 | 0.5 | 3.83x | 1.04x |
| fineweb_text | 12 | 4 | 6.5 | 6.2 | 1.8 | 3.56x | 1.04x |
| fineweb_text | 12 | 8 | 11.0 | 10.7 | 3.4 | 3.22x | 1.03x |
| fineweb_text | 16 | 1 | 2.4 | 2.0 | 0.8 | 2.97x | 1.22x |
| fineweb_text | 16 | 4 | 8.4 | 6.9 | 3.1 | 2.72x | 1.21x |
| fineweb_text | 16 | 8 | 12.2 | 11.6 | 5.7 | 2.16x | 1.05x |
| clickbench_url | 12 | 1 | 3.0 | 2.6 | 0.7 | 4.37x | 1.13x |
| clickbench_url | 12 | 4 | 10.1 | 8.8 | 2.5 | 3.95x | 1.14x |
| clickbench_url | 12 | 8 | 13.2 | 12.1 | 4.7 | 2.81x | 1.10x |
| clickbench_url | 16 | 1 | 3.5 | 3.0 | 1.0 | 3.48x | 1.16x |
| clickbench_url | 16 | 4 | 10.8 | 9.9 | 3.7 | 2.93x | 1.09x |
| clickbench_url | 16 | 8 | 13.7 | 13.4 | 6.6 | 2.07x | 1.02x |
| l_comment | 12 | 1 | 3.5 | 3.2 | 0.8 | 4.23x | 1.12x |
| l_comment | 12 | 4 | 11.0 | 10.6 | 3.1 | 3.54x | 1.03x |
| l_comment | 12 | 8 | 13.8 | 13.5 | 5.6 | 2.46x | 1.02x |
| l_comment | 16 | 1 | 2.9 | 2.4 | 1.0 | 2.93x | 1.24x |
| l_comment | 16 | 4 | 10.0 | 8.0 | 3.7 | 2.71x | 1.26x |
| l_comment | 16 | 8 | 13.7 | 12.2 | 6.6 | 2.05x | 1.12x |
| l_shipinstruct | 12 | 1 | 4.3 | 4.1 | 1.2 | 3.55x | 1.05x |
| l_shipinstruct | 12 | 4 | 12.5 | 11.3 | 4.3 | 2.88x | 1.10x |
| l_shipinstruct | 12 | 8 | 13.9 | 13.6 | 7.5 | 1.84x | 1.02x |
| l_shipinstruct | 16 | 1 | 4.3 | 4.1 | 1.2 | 3.52x | 1.04x |
| l_shipinstruct | 16 | 4 | 12.3 | 11.5 | 4.3 | 2.83x | 1.07x |
| l_shipinstruct | 16 | 8 | 13.8 | 13.8 | 7.5 | 1.84x | 1.00x |
| book_reviews | 12 | 1 | 2.2 | 2.1 | 0.5 | 4.48x | 1.06x |
| book_reviews | 12 | 4 | 7.7 | 7.3 | 1.9 | 4.06x | 1.06x |
| book_reviews | 12 | 8 | 12.0 | 11.5 | 3.6 | 3.35x | 1.04x |
| book_reviews | 16 | 1 | 2.1 | 1.8 | 0.7 | 3.19x | 1.21x |
| book_reviews | 16 | 4 | 7.5 | 6.3 | 2.6 | 2.95x | 1.19x |
| book_reviews | 16 | 8 | 12.0 | 10.9 | 4.8 | 2.53x | 1.11x |
