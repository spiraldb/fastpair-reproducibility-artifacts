# Request-rate roofline: findings

**Question.** Does a simple hardware-counter model predict measured OnPair decode
throughput from cache-request (sector) rates? The paper's thesis (Sec 5.2 /
`fig:costsurface`) is that the decode is *cache-request bound*: it runs as fast as its
binding pipe — the per-SM **L1** on the B300 (sm_103), the device-wide **L2** on the H100
and L40S — can serve the scattered dictionary gather's sector requests.

**Model tested.**

```
predicted_GB/s = decoded_bytes / (binding_sectors / peak_sector_rate)
               = decoded_bytes * peak_sector_rate / binding_sectors
```

interpreted as: *if the binding pipe saturates, the kernel decodes `decoded_bytes` in the
time it takes that pipe to move `binding_sectors` sectors at its hardware peak rate.*

**Exact metrics (median over the 16 profiled launches per cell).**

| quantity | source |
|---|---|
| `decoded_bytes` | the capture's own `gpu.decoded_bytes` in `results/{b300,l40s}-ncu/*_b*.log` (identical per cell across arches — same sample — so borrowed for the h100 captures, which ship no `.log`) |
| binding `sectors`, L2 | `lts__t_sectors.sum` (device-wide) |
| binding `sectors`, L1 (B300) | `l1tex__t_sectors.sum` (device-aggregated across SMs) |
| `peak_sector_rate`, L2 | `lts__t_sectors.sum.per_second / (lts__t_sectors.sum.pct_of_peak_sustained_elapsed / 100)` — a timing-independent hardware constant (≈ 869 sector/ns B300, 410 H100, 136 L40S) |
| `peak_sector_rate`, L1 (B300) | same ratio, reconstructed from the sector count over the profiled duration and the SOL `l1tex__throughput...pct_of_peak_sustained_elapsed` (no `per_second` column exists for L1); ≈ 130–210 sector/ns |
| `measured` | `figures/common.best_shipped(cell)` (best shipped-kernel decode GB/s) |

**Cell selection.** Only captures with achieved occupancy > 30% (`Occupancy / Achieved
Occupancy` in `*_details.csv`) *and* a committed `*_raw.csv` (needed for the sector
counts). This drops the underfilled ~3–5%-occupancy captures (fineweb, wikipedia, most
dbtext, `l_comment` b12) and, on the H100, leaves only the three cells that ship raw
(clickbench b12, synthetic b12, `l_shipinstruct` b12) — matching the task's known-filled
list exactly. Result: **21 cells**.

Reproduce: `uv run figures/fig_roofline.py` (table to stdout + `figures/out/fig_roofline.csv`,
scatter to `figures/out/fig_roofline.pdf`).

---

## Per-cell table (predicted vs measured)

`ratio = measured / predicted`, which is also the shipped kernel's **implied binding-pipe
utilisation** (fraction of hardware peak it would need if it moved the capture's sector
count). `pred_l2` / `ratio_l2` repeat the model with the clean device-wide L2 metric on
*all* arches, as a robustness check.

| arch | col | bits | occ% | binding | sec/byte | pred GB/s | meas GB/s | ratio | implied util | pred_l2 | ratio_l2 |
|---|---|---:|---:|:--:|---:|---:|---:|---:|---:|---:|---:|
| b300 | clickbench_URL | 12 | 64.6 | L1 | 4.694 | 28.8 | 961.8 | **33.4×** | 3338% | 188.1 | 5.11 |
| b300 | clickbench_URL | 16 | 64.2 | L1 | 2.648 | 50.0 | 1093.7 | 21.9× | 2189% | 320.1 | 3.42 |
| b300 | synthetic_url | 12 | 74.3 | L1 | 2.275 | 66.2 | 1689.4 | 25.5× | 2552% | 439.2 | 3.85 |
| b300 | synthetic_url | 16 | 74.6 | L1 | 2.303 | 66.4 | 1654.6 | 24.9× | 2490% | 442.1 | 3.74 |
| b300 | l_comment | 16 | 71.0 | L1 | 2.413 | 88.4 | 1066.4 | 12.1× | 1207% | 454.4 | 2.35 |
| b300 | l_shipinstruct | 12 | 73.4 | L1 | 0.965 | 159.1 | 1672.7 | 10.5× | 1051% | 750.2 | 2.23 |
| b300 | l_shipinstruct | 16 | 73.4 | L1 | 0.970 | 159.5 | 1663.0 | 10.4× | 1043% | 750.2 | 2.22 |
| b300 | ps_comment | 12 | 73.2 | L1 | 3.009 | 57.5 | 1447.3 | 25.2× | 2518% | 385.6 | 3.75 |
| b300 | ps_comment | 16 | 69.1 | L1 | 2.499 | 54.3 | 1198.1 | 22.1× | 2207% | 391.9 | 3.06 |
| h100 | clickbench_URL | 12 | 68.1 | L2 | 4.611 | 89.0 | 841.8 | 9.5× | 946% | 89.0 | 9.46 |
| h100 | synthetic_url | 12 | 69.4 | L2 | 2.005 | 204.6 | 1434.0 | 7.0× | 701% | 204.6 | 7.01 |
| h100 | l_shipinstruct | 12 | 74.2 | L2 | 1.150 | 356.8 | 1460.6 | 4.1× | 409% | 356.8 | 4.09 |
| l40s | clickbench_URL | 12 | 88.2 | L2 | 3.343 | 40.8 | 463.3 | 11.4× | 1136% | 40.8 | 11.36 |
| l40s | clickbench_URL | 16 | 88.5 | L2 | 2.039 | 66.8 | 461.3 | 6.9× | 691% | 66.8 | 6.91 |
| l40s | synthetic_url | 12 | 83.9 | L2 | 1.448 | 94.1 | 535.9 | 5.7× | 570% | 94.1 | 5.70 |
| l40s | synthetic_url | 16 | 84.0 | L2 | 1.400 | 97.5 | 536.5 | 5.5× | 550% | 97.5 | 5.50 |
| l40s | l_comment | 16 | 93.7 | L2 | 1.688 | 80.8 | 443.1 | 5.5× | 548% | 80.8 | 5.48 |
| l40s | l_shipinstruct | 12 | 97.3 | L2 | 0.766 | 178.6 | 516.5 | 2.9× | 289% | 178.6 | 2.89 |
| l40s | l_shipinstruct | 16 | 97.2 | L2 | 0.766 | 178.2 | 515.0 | 2.9× | 289% | 178.2 | 2.89 |
| l40s | ps_comment | 12 | 85.3 | L2 | 1.776 | 76.8 | 522.9 | 6.8× | 681% | 76.8 | 6.81 |
| l40s | ps_comment | 16 | 87.6 | L2 | 2.105 | 64.8 | 494.3 | 7.6× | 763% | 64.8 | 6.81 |

## Fit quality

- **R² about y = x: −3.35** (the model is worse than predicting the mean measured rate).
- **Pearson r in log–log space: 0.17** — the roofline does not even track the *ranking* of
  throughput across cells.
- **Median |relative error|: 89%.**
- **measured / predicted: median 9.5×, range 2.9×–33.4×.** Equivalently, the shipped kernel
  would have to run its binding pipe at **289%–3338% of hardware peak** to move the sector
  counts in these captures — physically impossible.
- The L2-everywhere variant (`ratio_l2`) is uniformly > 1 as well (2.2×–11.4×), so the
  failure is **not** an artifact of the L1 peak reconstruction on the B300.

Every point sits far **above** y = x in `fig_roofline.pdf`: measured throughput is many
times what the model predicts, and the miss is a *per-cell-varying* factor, not a constant.

## Which cells miss, and why — the diagnosis

**All 21 miss, and the miss is not fixable by re-choosing the metric.** The task flagged the
usual suspects; none of them explain it:

- *sectors vs. requests* — `lts__t_requests.sum ≈ 0.82 × lts__t_sectors.sum`, so a
  request-based roofline would predict an even **lower** rate (larger miss).
- *per-SM vs. device-aggregate* — the L2 metric (`lts`) is already device-wide; the B300 L1
  `.sum` is the device aggregate. Neither leaves a hidden ×(#SM) or ×(#slice) factor, and if
  one did it would be a *constant* per arch, whereas the miss varies 2.9×–33× within an arch.

The miss instead tracks the cell's **sector intensity** (`sec/byte`): clickbench b12 (4.69
sectors/decoded-byte) misses 33×, while `l_shipinstruct` (≈ 0.97) misses only ~10×/2.9×.
That is the signature of the root cause:

> **The committed NSight Compute captures do not profile the shipped kernel.** They profile
> the *base scalar `onpair` kernel* (or an equivalently un-optimized reference), which moves
> far more binding-pipe sectors per decoded byte than the shipped
> `onpair_shmem_4tpt_split8read` kernel whose throughput `best_shipped()` reports.

Three independent, decisive pieces of evidence (all from the captures themselves, e.g. b300
clickbench b12):

1. **Zero shared memory.** `Static Shared Memory Per Block = 0` and `Dynamic Shared Memory
   Per Block = 0` on every filled capture, all three arches. The shipped kernel allocates a
   static `__shared__ __align__(16) uint8_t s_buf_all[...]` staging buffer
   (`experiments/bench/gpu/onpair_shmem_4tpt_split8read.cu`), so it *cannot* report 0.
2. **64-thread blocks.** `Block Size = (64,1,1)` everywhere. The shipped kernel is
   `__launch_bounds__(512, 2)` and the auto-selected variant is `...b128o12` (128 threads);
   even the `b64` shipped variants use shared memory (ruled out by #1).
3. **~24× too slow.** The profiled `Duration` implies a decode rate at the (locked)
   profiling clock of ~22.5 GB/s for b300 clickbench b12; the base `onpair` kernel's summary
   rate is 38.2 GiB/s ≈ 41 GB/s, and 41 / 22.5 = 1.82 = the locked:boost clock ratio. The
   shipped kernel decodes the same cell at **962 GB/s** — the profiled kernel is ~24× slower.
   The same holds on H100 (profiled 20.5 vs base 21 GB/s locked≈boost) and L40S (10.4 vs 15).

Consequence for the roofline: the sector counts belong to a kernel ~24× slower than, and
with a different memory access pattern from, the throughput being predicted. On b300
clickbench the base kernel gathers 4.69 L1 sectors/byte; a kernel sustaining 962 GB/s
against the ~135 sector/ns L1 peak can afford only ~0.14 sector/byte. The shipped kernel's
whole point — shared-memory output staging + the `split8read` 32 KB hot-dict path — is to
issue ~an order of magnitude fewer binding-pipe requests per byte, so a roofline calibrated
on the base kernel's request count structurally under-predicts it, and does so by a
data-dependent (cardinality-dependent) factor rather than a constant.

**Worst three cells:** b300 clickbench b12 (33.4×), b300 synthetic b12 (25.5×), b300
ps_comment b12 (25.2×) — the B300 L1 cells, where the base kernel's sector intensity is
highest *and* the L1 peak is reconstructed rather than read directly. **Least bad:** l40s
`l_shipinstruct` b12/b16 (2.9×) and h100 `l_shipinstruct` b12 (4.1×) — the 5-token
dictionary makes the gather nearly free, so base and shipped kernels have similar (low)
sector intensity and the gap narrows, but the model still overshoots hardware peak (289%).

---

## Verdict

**No — the paper cannot, from these committed NSight Compute captures, claim that the
binding pipe's sector rate predicts (shipped) decode throughput.** The model misses measured
throughput by a median of 9.5× (R² = −3.35 about y = x; log–log r = 0.17), and the miss is
not a fixable scalar because it implies the shipped kernel runs its binding pipe at
289%–3338% of hardware peak, which is impossible. The root cause is that the committed
captures profile the *base scalar `onpair` kernel* (zero shared memory, 64-thread blocks,
~24× slower at the profiling clock), not the shipped `onpair_shmem_4tpt_split8read` kernel —
so a request-rate roofline needs NSight Compute re-run on the shipped auto-selected kernel
(recording its `decoded_bytes`, binding-pipe sector count, and an explicit L1 sector-peak
metric) before the claim can be supported quantitatively.

> **Flagged implication (out of scope, for the authors):** `fig:costsurface`,
> `tab:bottleneck`, and the `long_scoreboard` stall analysis in §5.2 are built from these
> *same* captures. If the intent was to characterize the shipped decode, the profiled kernel
> (0 shared memory, 64-thread blocks, ~24× slower) is structurally inconsistent with it and
> should be re-captured; if the intent was to motivate the optimization from the naive
> gather, that should be stated. This does not overturn the qualitative "a cache pipe binds,
> not HBM" observation, but it does undercut any *quantitative* roofline tied to the shipped
> rates.

---

# v2 addendum: same model, clean shipped-kernel captures (2026-07-05)

The recapture requested above now exists (main worktree,
`results/{a100,l40s,h100,b300}-ncu-v2/`, 14 cells × 4 arches, 16 launches/file, every
launch a verified `onpair_shmem_4tpt[_split8read]` — 512-thread blocks, 33.28 KB static
shared memory, locked clocks). `figures/fig_roofline_v2.py` re-runs the identical model
against it (adaptations forced by the v2 export are listed in its docstring; notably
l_comment b12 is a 50 MB sample decoded in 5 chunked launches, so its per-launch
decoded_bytes is `decoded_bytes/5`). Outputs: `figures/out/fig_roofline_v2.{csv,pdf}`.

**The v1 failure was entirely wrong-kernel provenance. On clean data the roofline works
on the three arches where a pipe actually saturates, and the binding pipe is L1/TEX
everywhere it saturates — including H100 and A100, not just B300.**

| fit (n=56 cells) | v1 (base kernel, 21 cells) | v2 (shipped kernel) |
|---|---|---|
| binding pipe | b300 L1 / h100+l40s L2 (paper map) | max-SOL pipe (= L1 on a100/h100/b300; mixed, unsaturated on l40s) |
| R² about y=x | −3.35 | **0.38** (0.93–0.99 per-arch after one clock scalar, below) |
| Pearson r, log–log | 0.17 | **0.80** (a100 .98, h100 .99, b300 .997; l40s .55) |
| median \|rel err\| | 89% | **22%** |
| measured/predicted | 9.5× median, 2.9–33.4× | **1.23× median, 0.51–1.93×** |
| implied binding-pipe util | 289–3338% (impossible) | ≤ 100% × clock ratio (physical) |

The residual ratio is a **per-arch constant = the boost:locked clock ratio** (captures are
clock-locked; `best_shipped` runs at boost). Scaling each arch's predictions by its median
ratio — one physical free parameter per arch — gives:

| arch | clock scale | R² about y=x | median \|rel\| | max \|rel\| |
|---|---:|---:|---:|---:|
| b300 | 1.82 (= the locked:boost ratio measured in v1 §evidence-3) | 0.989 | 1.7% | 5.9% |
| h100 | 1.22 | 0.961 | 3.8% | 16.2% |
| a100 | 1.22 | 0.930 | 8.0% | 27.2% |
| l40s | 0.82 | −0.79 | 19.2% | 61.2% |

- **B300 is the showcase:** L1/TEX SOL 87–96% on every full-dictionary cell, DRAM ≤ 12%,
  and the L1 sector-rate roofline × 1.82 predicts all 14 measured rates to a median 1.7%
  (worst 5.9% = l_comment b12, the chunked 10 MB-per-launch capture vs a 1 GB measured
  launch). H100/A100 behave the same with more spread; the low-SOL cells (fineweb/wikipedia
  b12, L1 ≈ 72–75%) are the ones that drift, i.e. the model is exact where the pipe is
  actually saturated and an upper bound where it isn't.
- **L40S is the honest failure case and confirms the same rule:** nothing saturates
  (L1 46–79%, L2 30–88%, DRAM ≤ 63% on full-dict cells, 81–82% on the small-dict
  synthetic/l_shipinstruct columns), so no single-pipe roofline predicts it — measured
  lands at 51–84% of the max-SOL pipe's peak on the L2/DRAM-led cells.
- **Stall profile of the shipped kernel** (per-cell top stalls in the CSV): `mio_throttle`
  dominates (share rises with dict-16), `short_scoreboard` second; `long_scoreboard` is
  only 8–38% of stall cycles and leads only on a few dict-12 text/URL cells. The v1-era
  `long_scoreboard`-dominant story was the base kernel's, not the shipped kernel's.

**What survives of v1 / what dies.** Survives: the wrong-kernel diagnosis (this recapture
is its direct confirmation), the "a cache pipe binds, not HBM" qualitative claim, and the
1.82 locked:boost B300 clock ratio. Dies: the v1 verdict that the committed data cannot
support a quantitative request-rate roofline (v2 data can); the paper map's "L2 binds on
Hopper" (base-kernel provenance — on the shipped kernel L1/TEX is the binding pipe on
A100/H100/B300 alike, and the per-chip L1-vs-L2 contrast was an artifact); and the v1
sector intensities (shipped kernel gathers 0.06–0.60 L1 sectors/byte, not 0.97–4.7).

**Caveats for a paper figure:** (1) the L1 prediction is algebraically
`in-capture rate / L1-SOL`, so its content is "SOL is high + the residual is the clock
constant", not an independent counter-only prediction — state it that way; (2) the capture
profiles the auto-selected kernel variant while `best_shipped` takes the max over variants
(same family, few-% spread); (3) l_comment b12's capture is a 10 MB chunk-launch, not
device-filling.
