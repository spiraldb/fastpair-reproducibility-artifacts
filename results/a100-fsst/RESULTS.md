# FSST recipe-port results (A100, locked clocks)

Units: fsst_scan reports decimal GB/s (decoded bytes / kernel s / 1e9) — directly
comparable to GSST's published 191 GB/s. FastPair summary.json reports GiB/s
(convert x1.0737 for GB/s). Raw per-iteration ns retained in every JSON.

## FSST: naive (fsst.cu) vs recipe (fsst_4tpt.cu) vs GSST 191 GB/s

| cell | decoded MB | ratio | naive ok | recipe ok | naive GB/s | recipe GB/s | recipe/naive | recipe/GSST191 |
|---|---|---|---|---|---|---|---|---|
| tpch_l_comment | 1590 | 2.95x | True | True | 138.57 | 327.66 | 2.36x | 1.72x |
| tpch_l_shipinstruct | 720 | 6.00x | True | True | 202.1 | 570.09 | 2.82x | 2.98x |

## FastPair (shipped family) on the same cells

### fastpair_summary_dbtext.json

- dbtext/email b12: ratio=None auto=onpair_shmem_4tpt auto_gib_s=128.37523778822893 best=onpair_shmem_4tpt best_gib_s=128.37523778822893
- dbtext/email b16: ratio=None auto=onpair_shmem_4tpt auto_gib_s=106.97936482352412 best=onpair_shmem_4tpt_wpb8_occ best_gib_s=113.27226863667259
- dbtext/hex b12: ratio=None auto=onpair_shmem_s8_4tpt auto_gib_s=60.12684631665858 best=onpair_shmem_4tpt_split4read best_gib_s=65.59292325453664
- dbtext/hex b16: ratio=None auto=onpair_shmem_s8_4tpt auto_gib_s=60.12684631665858 best=onpair_shmem_4tpt_split4read_b128o12 best_gib_s=65.59292325453664
- dbtext/l_comment b12: ratio=None auto=onpair_shmem_4tpt auto_gib_s=160.43177311075848 best=onpair_shmem best_gib_s=171.8911854758127
- dbtext/l_comment b16: ratio=None auto=onpair_shmem_4tpt auto_gib_s=150.40478729133613 best=onpair_shmem best_gib_s=171.8911854758127
- dbtext/ps_comment b12: ratio=None auto=onpair_shmem_4tpt auto_gib_s=149.84216250013557 best=onpair_shmem best_gib_s=172.89480288477185
- dbtext/ps_comment b16: ratio=None auto=onpair_shmem_4tpt auto_gib_s=140.47702734387715 best=onpair_shmem best_gib_s=172.89480288477185
- dbtext/yago b12: ratio=None auto=onpair_shmem_4tpt_split8read auto_gib_s=103.85224413766993 best=onpair_shmem_4tpt_split8read_b128o12 best_gib_s=110.77572708018123
- dbtext/yago b16: ratio=None auto=onpair_shmem_4tpt auto_gib_s=92.31310590015104 best=onpair_shmem_4tpt_b128 best_gib_s=97.74328860015991

### fastpair_summary_tpch_lcomment.json

- tpch-sf10/l_comment b12: ratio=None auto=onpair_shmem_4tpt auto_gib_s=542.9818990176418 best=onpair_shmem_4tpt_b128 best_gib_s=589.0509591026879
- tpch-sf10/l_comment b16: ratio=None auto=onpair_shmem_4tpt auto_gib_s=365.84661337672975 best=onpair_shmem_4tpt_ldcs best_gib_s=366.7317261510283


See fsstbin_manifest.txt for blob provenance; run-env.txt for clocks/driver.
