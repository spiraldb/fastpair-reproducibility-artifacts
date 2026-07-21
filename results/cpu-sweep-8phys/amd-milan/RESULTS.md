# OnPair CPU decode microbench — AMD EPYC 7R13 Processor

cores/socket: 8, threads/core: 2. Decode throughput (GiB/s of output), byte-identical across layouts. fat = data+code*16 (one independent load + over-copy); entries = variable-stride + over-copy; naive = variable-stride + exact copy (non-over-copying baseline).

| column | bits | thr | fat | entries | naive | fat/naive | fat/entries |
|--|--:|--:|--:|--:|--:|--:|--:|
| synthetic_url | 12 | 1 | 4.2 | 4.0 | 2.1 | 2.00x | 1.04x |
| synthetic_url | 12 | 4 | 12.5 | 12.2 | 7.6 | 1.65x | 1.02x |
| synthetic_url | 12 | 8 | 15.1 | 14.9 | 12.9 | 1.17x | 1.01x |
| synthetic_url | 16 | 1 | 4.8 | 4.5 | 2.7 | 1.75x | 1.05x |
| synthetic_url | 16 | 4 | 12.5 | 12.6 | 9.6 | 1.30x | 0.99x |
| synthetic_url | 16 | 8 | 15.1 | 15.2 | 13.4 | 1.12x | 0.99x |
| tpch_comment | 12 | 1 | 5.4 | 5.3 | 2.2 | 2.41x | 1.03x |
| tpch_comment | 12 | 4 | 13.7 | 13.5 | 8.2 | 1.67x | 1.01x |
| tpch_comment | 12 | 8 | 15.9 | 15.9 | 13.3 | 1.20x | 1.00x |
| tpch_comment | 16 | 1 | 5.5 | 5.2 | 2.3 | 2.42x | 1.06x |
| tpch_comment | 16 | 4 | 13.9 | 13.6 | 8.2 | 1.70x | 1.02x |
| tpch_comment | 16 | 8 | 16.0 | 16.0 | 13.1 | 1.22x | 1.00x |
| fineweb_text | 12 | 1 | 1.6 | 1.5 | 0.6 | 2.72x | 1.02x |
| fineweb_text | 12 | 4 | 5.6 | 5.5 | 2.2 | 2.56x | 1.02x |
| fineweb_text | 12 | 8 | 9.9 | 9.9 | 4.2 | 2.38x | 1.01x |
| fineweb_text | 16 | 1 | 3.6 | 3.5 | 1.1 | 3.18x | 1.02x |
| fineweb_text | 16 | 4 | 11.6 | 11.6 | 4.2 | 2.77x | 1.00x |
| fineweb_text | 16 | 8 | 14.8 | 14.8 | 7.6 | 1.94x | 1.00x |
| clickbench_url | 12 | 1 | 2.7 | 2.6 | 0.9 | 3.04x | 1.01x |
| clickbench_url | 12 | 4 | 9.5 | 9.3 | 3.3 | 2.87x | 1.03x |
| clickbench_url | 12 | 8 | 13.4 | 13.4 | 6.2 | 2.18x | 1.00x |
| clickbench_url | 16 | 1 | 3.9 | 3.3 | 1.2 | 3.12x | 1.17x |
| clickbench_url | 16 | 4 | 11.9 | 11.0 | 4.6 | 2.57x | 1.07x |
| clickbench_url | 16 | 8 | 14.7 | 14.8 | 8.4 | 1.75x | 0.99x |
| l_comment | 12 | 1 | 3.8 | 3.7 | 1.0 | 3.77x | 1.03x |
| l_comment | 12 | 4 | 12.0 | 11.7 | 3.8 | 3.18x | 1.03x |
| l_comment | 12 | 8 | 14.8 | 14.6 | 6.9 | 2.14x | 1.01x |
| l_comment | 16 | 1 | 3.4 | 3.0 | 1.2 | 2.93x | 1.12x |
| l_comment | 16 | 4 | 11.3 | 10.3 | 4.3 | 2.61x | 1.09x |
| l_comment | 16 | 8 | 14.7 | 14.5 | 7.9 | 1.86x | 1.01x |
| l_shipinstruct | 12 | 1 | 4.4 | 4.3 | 1.4 | 3.07x | 1.03x |
| l_shipinstruct | 12 | 4 | 12.5 | 12.4 | 5.2 | 2.38x | 1.00x |
| l_shipinstruct | 12 | 8 | 15.1 | 15.2 | 9.3 | 1.63x | 0.99x |
| l_shipinstruct | 16 | 1 | 4.3 | 4.1 | 1.4 | 3.06x | 1.05x |
| l_shipinstruct | 16 | 4 | 12.5 | 12.5 | 5.2 | 2.40x | 1.00x |
| l_shipinstruct | 16 | 8 | 15.2 | 15.0 | 9.3 | 1.64x | 1.02x |
| book_reviews | 12 | 1 | 2.1 | 2.1 | 0.6 | 3.54x | 1.03x |
| book_reviews | 12 | 4 | 7.8 | 7.5 | 2.3 | 3.33x | 1.03x |
| book_reviews | 12 | 8 | 12.7 | 12.6 | 4.4 | 2.89x | 1.01x |
| book_reviews | 16 | 1 | 2.6 | 2.2 | 0.8 | 3.24x | 1.18x |
| book_reviews | 16 | 4 | 9.0 | 8.0 | 3.0 | 2.94x | 1.12x |
| book_reviews | 16 | 8 | 13.5 | 12.7 | 5.8 | 2.34x | 1.06x |
