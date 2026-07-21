# Full-metric NCU raw exports (backup)

These are `ncu --import <rep> --csv --page raw` dumps — the **complete** ~2,500-metric
Nsight Compute capture, wide format (one row per kernel launch, one column per metric).
The `*_details.csv` files committed elsewhere under `results/{b200,h100}-ncu/` carry only
the per-section *summary* (SOL %-of-peak, hit rates, occupancy). The detailed metrics the
paper's prose cites but the summary omits live **only here**:

- L1/TEX load-vs-store split: `l1tex__t_{requests,sectors}_pipe_lsu_mem_global_op_{ld,st}.sum`
  (+ `_lookup_{hit,miss}`). On the filling `synthetic_url` cell, requests split ~53% load /
  47% store — the staged-drain stores co-bind the L1/TEX request path, not just the gather.
- Warp-stall reasons: `smsp__average_warps_issue_stalled_{long_scoreboard,mio_throttle,
  lg_throttle,...}_per_issue_active.ratio`.

## Coverage / provenance

B200 (Blackwell), dict-12 only — the two cells whose raw exports survived the harness
cleanup of `runs/`:

| file | column | bits | note |
|---|---|---|---|
| `ncu_raw_l_comment_b12.csv`   | tpch-sf10 l_comment | 12 | 50 MB sample, underfilled (L1/TEX ~24%, occ ~3.8%) |
| `ncu_raw_synthetic_url_b12.csv` | synthetic url     | 12 | GPU-filling (L1/TEX bound), the meaningful cell |

The source `.ncu-rep` binaries (27 MB + 55 MB, too large for this repo) are stashed at
`~/data/onpair-ncu-archive/` on the orchestrating laptop. Full breadth (B200 + H100, both
presets, the filling columns + book-reviews) is the job of the planned pristine NCU run,
which will export a curated subset of these metrics to committed CSVs.
