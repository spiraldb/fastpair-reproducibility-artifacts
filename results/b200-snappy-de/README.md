# B200 DE-Snappy ordering run (2026-07-05, paper worklist F1)

One question: does the Decompression Engine's fourth codec family, Snappy, ever beat the
best engine codec the paper reports? Run on a Nebius me-west1 B200 (the DE silicon is
byte-identical B200/B300) at fork rev ba16fad7f (adds the Snappy leg to nvcomp_hw_bench.cu),
trimmed to the non-HF datasets: 11 of the 16 DE columns, including the floor-setting
ClickBench URL and synthetic cells.

Verdict: **Snappy never leads a throughput-bound column.** DEFLATE-hi leads every
throughput-bound cell; Snappy tracks LZ4 within ~1-3% (e.g. clickbench URL 354.8 vs LZ4
351.3 GiB/s, both under DEFLATE-hi's 377.8). Its single nominal lead is dbtext/email
(launch-bound, 2 MB): 67.6 vs LZ4's 67.0 GiB/s, +0.9%, inside run noise at sizes where no
decoder is throughput-limited. The committed B300 best-(codec,chunk) reduction is unaffected.

The full-sweep B200 summaries for the five datasets are in the harness run dir
(runs/b200-snappy-de-20260705-021702), not committed: this directory carries only the DE
comparison the paper cites. B300-native confirmation: ../b300-snappy-de/ (same verdict, same-chip).
