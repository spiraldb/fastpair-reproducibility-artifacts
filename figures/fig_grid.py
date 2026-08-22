# /// script
# requires-python = ">=3.9"
# dependencies = ["matplotlib", "numpy"]
# ///
"""Fig. grid: the launch parameters K, T and B in one picture.

Sections 4.1 and 4.2 are one experiment: the launch shape IS (K, T, B), and the three cannot be
read apart. K sets how many codes a lane covers, B forces the register ceiling
R/(T*B) the compiler must honour, and T scales both. Reporting them as separate sweeps invited
the reader to add three independent sensitivities that do not add.

WHAT EACH CHANNEL CARRIES. x is K, the parameter that dominates. One line per T. One panel per B,
so B's behaviour is the DIFFERENCE BETWEEN PANELS rather than a fourth line: the panels are nearly
identical at low K and separate only once K is large enough that the register cap binds, which is
the threshold claim stated as a shape instead of a number.

Curves are the MEDIAN over the ten real columns at OnPair-12, not a single column: the shape is
the claim, and one column would invite the reader to take its peak as a rate. Generated columns
are excluded here for the same reason they are panelled separately elsewhere.

RATE IS THE BEST KERNEL AT EACH (K,T,B) CELL, which for the dg family is the cell itself -- there
is exactly one dg kernel per coordinate. No selection is happening in this figure.

Source: results/suite-<id>/b300/sweep_summary_*_boost.json, dg family, 120 coordinates per cell.
"""
import argparse
import re
import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402
import suite as S  # noqa: E402

KS = list(range(1, 9))
TS = [64, 128, 256]
BS = [1, 2, 4, 6, 8]
T_COLOR = {64: "#9ecae1", 128: "#4292c6", 256: "#08519c"}
DEV = "b300"
BITS = 12


def dg_rates(cell):
    """(K,T,B) -> GB/s for the dg family of one cell."""
    out = {}
    g = cell.get("gpu") or {}
    db = g.get("decoded_bytes")
    for k in (g.get("kernels") or []):
        m = re.match(r"onpair_dg_k(\d+)_t(\d+)_b(\d+)$", k.get("kernel", ""))
        if m and k.get("decode_ns_iters") and db:
            out[(int(m.group(1)), int(m.group(2)), int(m.group(3)))] = db / min(k["decode_ns_iters"])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--suite-id", default=None)
    a = ap.parse_args()
    root = S.latest_root(a.suite_id)
    if root is None:
        sys.exit("no results/suite-* directory found")

    cells = S.cells(root, DEV, "boost", "onpair")
    real = {(ds, col) for _, ds, col in S.REAL}
    # The FIGURE draws one preset so the shape is legible; the STATISTICS below are computed
    # over both, which is the basis the paper's claim macros use. Reporting a figure-scoped
    # number beside a prose number derived differently is how the two silently disagree.
    grids = [g for g in (dg_rates(c) for (ds, col, bits), c in cells.items()
                         if (ds, col) in real and bits == BITS) if g]
    grids_all = [g for g in (dg_rates(c) for (ds, col, bits), c in cells.items()
                             if (ds, col) in real) if g]
    if not grids:
        sys.exit("no dg coordinates found; is this a full-grid pass?")

    plt = C.apply_theme()
    fig, axes = plt.subplots(1, len(BS), figsize=(7.0, 1.95), sharey=True)
    for ax, B in zip(axes, BS):
        for T in TS:
            ys = []
            for K in KS:
                vals = [g[(K, T, B)] for g in grids if (K, T, B) in g]
                ys.append(st.median(vals) if vals else None)
            xs = [k for k, y in zip(KS, ys) if y is not None]
            yy = [y for y in ys if y is not None]
            ax.plot(xs, yy, marker="o", ms=2.6, lw=1.0, color=T_COLOR[T], label=f"T={T}")
        ax.set_title(f"B={B}", fontsize=7.5)
        ax.set_xticks([1, 2, 4, 6, 8])
        ax.set_xlabel("K")
        ax.grid(alpha=.25, lw=.4)
        ax.set_axisbelow(True)
    axes[0].set_ylabel("decode (GB/s)")
    axes[0].set_ylim(0, None)

    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, frameon=False, fontsize=6.6, ncol=3, loc="lower center",
               bbox_to_anchor=(0.5, -0.04), columnspacing=1.2, handlelength=1.4)
    fig.tight_layout(rect=(0, 0.10, 1, 1))
    C.save(fig, "fig_grid")

    # The numbers the prose states, derived from the same data the figure draws.
    spreads, argK, argT = [], {}, {}
    for g in grids_all:
        for T in TS:
            for B in BS:
                vs = [g[(K, T, B)] for K in KS if (K, T, B) in g]
                if len(vs) == len(KS):
                    spreads.append(100 * (max(vs) / min(vs) - 1))
        best = max(g.items(), key=lambda kv: kv[1])[0]
        argK[best[0]] = argK.get(best[0], 0) + 1
        argT[best[1]] = argT.get(best[1], 0) + 1
    print(f"[both presets, {len(grids_all)} column-preset pairs] K spread at fixed (T,B): "
          f"median {st.median(spreads):.0f}%, max {max(spreads):.0f}%, n={len(spreads)}")
    print(f"[figure scope: OnPair-{BITS}, {len(grids)} columns]")
    print(f"argmax K: {dict(sorted(argK.items()))}   argmax T: {dict(sorted(argT.items()))}")
    # B as a threshold: the spread over the binding rungs against the non-binding ones.
    for label, rungs in (("B in {1,2,4}", [1, 2, 4]), ("B in {4,6,8}", [4, 6, 8])):
        sp = []
        for g in grids_all:
            for K in KS:
                for T in TS:
                    vs = [g[(K, T, B)] for B in rungs if (K, T, B) in g]
                    if len(vs) == len(rungs):
                        sp.append(100 * (max(vs) / min(vs) - 1))
        print(f"{label}: median spread {st.median(sp):.1f}%")


if __name__ == "__main__":
    main()
