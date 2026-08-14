# `a100-widthncu-eval` — the access-width capture on the A100, PARTIAL

A100-SXM4 40GB (sm_80), GCP us-central1-f, 2026-08-14. Harness run
`a100-widthncu-20260814-014524`, vortex rev `2d909147f`. Four captures, all
**CAPTURE-VERIFIED**: FineWeb `text` and Wikipedia `text`, each under `split8read` and the
stride-16 `onpair_shmem_4tpt` — the same four cells as `b300-widthncu-eval`, so the legs are
directly comparable.

## Read this before citing it: it does NOT carry the width mechanism

The paper's width isolation rests on two counters moving in opposite ways — LSU **wavefronts**
falling about a quarter while **sector** count stays flat, which is what separates "each access
is narrower" from "the table got more cache-resident". **Neither counter is in this capture.**

    l1tex__data_pipe_lsu_wavefronts.avg    B300: 2069587.91    A100: ABSENT
    l1tex__t_sectors.sum                   B300:  584375405    A100: ABSENT

This is a property of the architecture and the profiler build, not a fault in this run. The job
collects `--set full`, and on sm_80 that set does not include these counters; the previously
committed `results/a100-shdict-ncu` (a different, earlier run) is missing them too. Re-running
this job unchanged would reproduce the gap exactly. Obtaining them needs an explicit
`--metrics l1tex__data_pipe_lsu_wavefronts.sum,l1tex__t_sectors.sum` pass, which is a change to
`jobs/onpair-shdict-ncu.sh` and another A100 session, and it is not certain sm_80 exposes them
under those names.

## What it does support

split8read relative to stride-16:

| column | sm cycles | L1 hit% |
|---|---|---|
| FineWeb `text` | 0.890 | 87.7 -> 90.4 |
| Wikipedia `text` | 0.915 | 87.9 -> 90.3 |

For comparison, the same two cells on the B300 (`b300-widthncu-eval`): cycles 0.893 and 0.903,
hit rate 89.0 -> 90.9 and 89.1 -> 91.0.

So the A100 reproduces the *outcome* — split8read costs about 9 to 11% fewer SM cycles, and the
L1 hit rate moves by under three points, far too little to explain the gain by residency. It
corroborates the account on a fourth chip and is consistent with the B300 to within a point on
both quantities. It cannot, on its own, establish the wavefront-versus-sector mechanism; that
evidence remains B300, H100 and L40S.

This matters for §6's A100 claim specifically. The A100 is the one chip where FSST-12 decodes
faster than OnPair-12 on all five text columns, which §6 reads through the access-width account.
That reading is supported by the bottleneck table and by this capture's cycle and hit-rate
movement, but the direct wavefront evidence on this chip is still missing, and §6 says so rather
than implying a four-chip mechanism result.
