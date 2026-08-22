# /// script
# requires-python = ">=3.9"
# dependencies = ["matplotlib", "numpy"]
# ///
"""Fig. hoist: the hoist's best result is worth less than not asking for occupancy.

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

Curves are the median over the ten real columns at OnPair-12, T=256, min-of-100 per cell.

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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--suite-id", default=None)
    a = ap.parse_args()
    root = S.latest_root(a.suite_id)
    if root is None:
        sys.exit("no results/suite-* directory found")

    cells = S.cells(root, DEV, "boost", "onpair")
    real = {(ds, col) for _, ds, col in S.REAL}
    R = {}
    for (ds, col, bits), c in cells.items():
        if (ds, col) not in real or bits != BITS:
            continue
        g = c.get("gpu") or {}
        db = g.get("decoded_bytes")
        for k in (g.get("kernels") or []):
            if k.get("decode_ns_iters") and db:
                R.setdefault(k["kernel"], []).append(db / min(k["decode_ns_iters"]))

    def med(name):
        return st.median(R[name]) if name in R else None

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
    fig, ax = plt.subplots(figsize=(7.0, 2.2))
    # A DUMBBELL, not lines. Each line in the previous form encoded two parameters at once (which
    # B, which H), so the reader had to decode a legend to see a comparison that is categorical.
    # Here one arrow per K IS the hoist -- from the H=1 baseline to the best H at the same B=8 --
    # and the reference marker is what B=1 reaches without it. The arrow either reaches the
    # reference or it does not.
    for i, K in enumerate(KS):
        if coll[i] is None or rec[i] is None:
            continue
        ax.annotate("", xy=(K, rec[i]), xytext=(K, coll[i]),
                    arrowprops=dict(arrowstyle="-|>", lw=1.4, color="#b0413e",
                                    shrinkA=0, shrinkB=0, mutation_scale=7))
    ax.scatter(KS, coll, s=13, color="#9ecae1", zorder=4, linewidths=0)
    ax.scatter(KS, ref, s=34, marker="_", color="#08519c", zorder=5, linewidths=1.6)
    ax.set_xticks(KS)
    ax.set_xlabel("K (codes per lane), T=256")
    ax.set_ylabel("decode (GB/s)")
    ax.set_ylim(0, None)
    ax.grid(alpha=.25, lw=.4)
    ax.set_axisbelow(True)
    from matplotlib.lines import Line2D
    ax.legend(handles=[
        Line2D([], [], color="#08519c", marker="_", ls="", ms=7, mew=1.6, label="B=1, H=1"),
        Line2D([], [], color="#9ecae1", marker="o", ls="", ms=3.6, label="B=8, H=1"),
        Line2D([], [], color="#b0413e", lw=1.4, label="B=8, H=1 to best H"),
    ], fontsize=6.4, frameon=False, loc="lower left", ncol=1, handlelength=1.8)
    fig.tight_layout()
    C.save(fig, "fig_hoist")

    print(f"{'K':>3}{'B=1 H=1':>10}{'B=8 H=1':>10}{'B=8 bestH':>11}{'% of B=1':>10}")
    for i, K in enumerate(KS):
        if ref[i] and coll[i] and rec[i]:
            print(f"{K:>3}{ref[i]:>10.0f}{coll[i]:>10.0f}{rec[i]:>11.0f}"
                  f"{100 * rec[i] / ref[i]:>9.1f}%")


if __name__ == "__main__":
    main()
