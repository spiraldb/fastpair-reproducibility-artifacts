# OnPair CPU decode microbench — AMD EPYC 9R14

cores/socket: 8, threads/core: 1. Decode throughput (GiB/s of output), byte-identical across layouts. fat = data+code*16 (one independent load + over-copy); entries = variable-stride + over-copy; naive = variable-stride + exact copy (non-over-copying baseline).

| column | bits | thr | fat | entries | naive | fat/naive | fat/entries |
|--|--:|--:|--:|--:|--:|--:|--:|
| synthetic_url | 12 | 1 | 5.4 | 4.8 | 2.5 | 2.20x | 1.13x |
| synthetic_url | 12 | 2 | 10.3 | 9.2 | 5.1 | 2.03x | 1.11x |
| synthetic_url | 12 | 4 | 16.0 | 15.5 | 9.0 | 1.78x | 1.03x |
| synthetic_url | 16 | 1 | 5.5 | 5.2 | 3.0 | 1.87x | 1.06x |
| synthetic_url | 16 | 2 | 10.3 | 9.0 | 5.8 | 1.78x | 1.15x |
| synthetic_url | 16 | 4 | 15.6 | 15.2 | 10.8 | 1.44x | 1.02x |
| tpch_comment | 12 | 1 | 6.0 | 5.7 | 2.3 | 2.62x | 1.07x |
| tpch_comment | 12 | 2 | 11.4 | 10.4 | 4.5 | 2.50x | 1.09x |
| tpch_comment | 12 | 4 | 16.4 | 16.1 | 8.5 | 1.94x | 1.01x |
| tpch_comment | 16 | 1 | 6.0 | 5.5 | 2.3 | 2.63x | 1.10x |
| tpch_comment | 16 | 2 | 11.3 | 10.2 | 4.5 | 2.52x | 1.12x |
| tpch_comment | 16 | 4 | 16.3 | 16.1 | 8.5 | 1.93x | 1.02x |
| fineweb_text | 12 | 1 | 2.6 | 2.3 | 0.6 | 4.56x | 1.16x |
| fineweb_text | 12 | 2 | 5.5 | 4.4 | 1.1 | 4.83x | 1.25x |
| fineweb_text | 12 | 4 | 9.6 | 8.4 | 2.2 | 4.24x | 1.14x |
| fineweb_text | 16 | 1 | 3.8 | 3.5 | 1.1 | 3.31x | 1.08x |
| fineweb_text | 16 | 2 | 7.3 | 6.7 | 2.2 | 3.27x | 1.10x |
| fineweb_text | 16 | 4 | 13.0 | 12.3 | 4.3 | 3.03x | 1.06x |
| clickbench_url | 12 | 1 | 4.0 | 3.6 | 0.9 | 4.36x | 1.11x |
| clickbench_url | 12 | 2 | 7.7 | 6.8 | 1.8 | 4.28x | 1.13x |
| clickbench_url | 12 | 4 | 13.7 | 12.7 | 3.5 | 3.92x | 1.08x |
| clickbench_url | 16 | 1 | 4.3 | 3.9 | 1.3 | 3.27x | 1.09x |
| clickbench_url | 16 | 2 | 8.1 | 7.4 | 2.6 | 3.14x | 1.09x |
| clickbench_url | 16 | 4 | 13.9 | 13.4 | 4.9 | 2.83x | 1.04x |
| l_comment | 12 | 1 | 4.8 | 4.0 | 1.0 | 4.57x | 1.20x |
| l_comment | 12 | 2 | 9.0 | 7.7 | 2.0 | 4.41x | 1.17x |
| l_comment | 12 | 4 | 15.5 | 13.7 | 3.9 | 3.93x | 1.13x |
| l_comment | 16 | 1 | 3.7 | 3.5 | 1.2 | 2.98x | 1.07x |
| l_comment | 16 | 2 | 7.2 | 6.7 | 2.5 | 2.93x | 1.07x |
| l_comment | 16 | 4 | 13.0 | 12.4 | 4.7 | 2.75x | 1.04x |
| l_shipinstruct | 12 | 1 | 6.7 | 6.3 | 1.5 | 4.52x | 1.07x |
| l_shipinstruct | 12 | 2 | 12.0 | 11.8 | 3.1 | 3.85x | 1.02x |
| l_shipinstruct | 12 | 4 | 16.3 | 16.2 | 5.5 | 2.95x | 1.01x |
| l_shipinstruct | 16 | 1 | 6.8 | 6.2 | 1.5 | 4.50x | 1.09x |
| l_shipinstruct | 16 | 2 | 11.9 | 11.5 | 3.1 | 3.83x | 1.03x |
| l_shipinstruct | 16 | 4 | 16.4 | 16.1 | 5.5 | 2.97x | 1.02x |
| book_reviews | 12 | 1 | 3.4 | 2.9 | 0.6 | 5.36x | 1.18x |
| book_reviews | 12 | 2 | 6.6 | 5.6 | 1.3 | 5.28x | 1.18x |
| book_reviews | 12 | 4 | 12.2 | 10.5 | 2.5 | 4.96x | 1.16x |
| book_reviews | 16 | 1 | 3.2 | 2.9 | 0.9 | 3.69x | 1.11x |
| book_reviews | 16 | 2 | 6.0 | 5.6 | 1.7 | 3.56x | 1.07x |
| book_reviews | 16 | 4 | 11.4 | 10.7 | 3.3 | 3.42x | 1.06x |
