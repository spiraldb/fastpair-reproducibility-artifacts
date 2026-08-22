# /// script
# requires-python = ">=3.9"
# dependencies = ["matplotlib", "numpy"]
# ///
"""Fig. hoist: three configurations per K, as bars.

A grouped bar chart, because the comparison is categorical: three named configurations at each K.
Earlier drafts drew it as lines and then as arrows, both of which asked the reader to decode a
custom encoding for something a bar chart states directly.

H holds up to H-1 long-token requests across rounds instead of re-issuing them. Measured at
B=8 it looks like the campaign's largest single win: the H=1 baseline at K=6, T=256 sits at
362 GB/s and the best H rung lifts it to 617, about +70%.

THAT COMPARISON HAS THE WRONG BASELINE, and this figure is the correction. The 362 is not a
neutral starting point; it is what the kernel degrades to once B=8 caps registers at 32 and the
working set at K=6 no longer fits. Setting B=1 -- asking the scheduler for nothing and letting
ptxas keep its 56 registers -- reaches 1191 GB/s at the same K and T with no hoist at all.

So the recovery closes about half of a hole that the launch bound dug. The shaded band is what
the hoist never gets back. Read against the configuration one would actually ship, the best H
result is a 48% REGRESSION, not a 70% gain.

At K=2 and K=3 the picture legitimately reverses and B=8 leads: the register cap is affordable
while the working set is small, which is the same threshold fig_grid shows from the other side.
The hoist is not what changes there either.

One column, Loghub Windows at OnPair-12, T=256, min-of-100 per cell.

Source: results/suite-<id>/b300/sweep_summary_*_boost.json, dh family against dg at the same
coordinate.
"""
import argparse
import re
import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402
import suite as S  # noqa: E402

KS = list(range(2, 9))
T = 256
DEV, BITS = "b300", 12
COLUMN = ("loghub-windows", "line")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--suite-id", default=None)
    a = ap.parse_args()
    root = S.latest_root(a.suite_id)
    if root is None:
        sys.exit("no results/suite-* directory found")

    cells = S.cells(root, DEV, "boost", "onpair")
    c = cells.get((COLUMN[0], COLUMN[1], BITS))
    if c is None:
        sys.exit(f"column {COLUMN} absent from this leg")
    g = c.get("gpu") or {}
    db = g.get("decoded_bytes")
    R = {k["kernel"]: db / min(k["decode_ns_iters"])
         for k in (g.get("kernels") or []) if k.get("decode_ns_iters") and db}

    def med(name):
        return R.get(name)

    ref, coll, rec = [], [], []
    for K in KS:
        ref.append(med(f"onpair_dg_k{K}_t{T}_b1"))
        coll.append(med(f"onpair_dg_k{K}_t{T}_b8"))
        hs = [med(f"onpair_dh_k{K}_t{T}_b8_h{h}") for h in range(2, min(K, 4) + 1)]
        hs = [x for x in hs if x]
        rec.append(max(hs) if hs else None)
    if not any(ref):
        sys.exit("no dg/dh coordinates found; is this a full-grid pass?")

    plt = C.apply_theme()
    import numpy as np
    fig, ax = plt.subplots(figsize=(7.0, 2.2))
    x = np.arange(len(KS))
    w = 0.27
    for off, vals, color, lab in ((-w, ref, "#08519c", "B=1, H=1"),
                                  (0.0, coll, "#9ecae1", "B=8, H=1"),
                                  (w, rec, "#b0413e", "B=8, best H")):
        ax.bar(x + off, [v or 0 for v in vals], width=w, color=color, label=lab,
               linewidth=0, zorder=3)
    ax.set_xticks(x)
    ax.set_xticklabels([str(k) for k in KS])
    ax.set_xlabel("K (codes per lane), T=256")
    ax.set_ylabel("decode (GB/s)")
    from matplotlib.ticker import FixedLocator
    ax.set_ylim(0, 2000)
    ax.yaxis.set_major_locator(FixedLocator([0, 500, 1000, 1500, 2000]))
    ax.grid(axis="y", alpha=.25, lw=.4)
    ax.set_axisbelow(True)
    ax.legend(fontsize=6.6, frameon=False, ncol=3, loc="upper right", handlelength=1.2)
    fig.tight_layout()
    C.save(fig, "fig_hoist")

    print(f"{'K':>3}{'B=1 H=1':>10}{'B=8 H=1':>10}{'B=8 bestH':>11}{'% of B=1':>10}")
    for i, K in enumerate(KS):
        if ref[i] and coll[i] and rec[i]:
            print(f"{K:>3}{ref[i]:>10.0f}{coll[i]:>10.0f}{rec[i]:>11.0f}"
                  f"{100 * rec[i] / ref[i]:>9.1f}%")


if __name__ == "__main__":
    main()
