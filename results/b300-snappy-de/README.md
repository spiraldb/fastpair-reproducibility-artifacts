# B300-native DE-Snappy confirmation (2026-07-05, paper worklist F1)

Same question and shape as ../b200-snappy-de/, now on the B300 itself (uk-south1,
PREEMPTIBLE pool — landed first attempt after 41 on-demand stockouts, survived the full
~1 h run). Fork rev ba16fad7f, trimmed non-HF datasets, locked clocks.

Verdict, matching the B200: **DEFLATE-hi leads every throughput-bound column; Snappy
tracks LZ4 within ±1.3% and never leads one** (clickbench URL 373.2 vs LZ4 370.0, both
under DEFLATE-hi 398.3 GiB/s). Fresh engine rates reproduce the committed results/b300
DE data within ~1% (l_comment 321.9 vs 325.3; synthetic 638.8 vs 644.9). On the tiny
launch-bound dbtext columns the LZ-class codecs trade sub-percent leads run-to-run
(email: LZ4 here, Snappy on the B200; yago: the reverse) — noise, disclosed as such.

The paper's §6.1 Snappy clause cites this run (same-chip provenance).
