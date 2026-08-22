# /// script
# requires-python = ">=3.9"
# dependencies = ["matplotlib", "numpy"]
# ///
"""Fig. grid: why K=6, and what B and T actually do to get there.

This is a MECHANISM figure, not a parameter search. The question is not "which cell won" but why
the winning region is where it is, and the answer is a single interaction: B decides whether the
compiler is allowed to spend registers, and once that is settled K and T are an algorithmic
trade with no occupancy term in it.

THE TWO PANELS ARE THE ARGUMENT.

  B=1 (left).  The launch bound asks for nothing, so ptxas allocates what the kernel wants -- 56
  registers per thread at every K -- and the hardware still resides 4 blocks per SM, unchanged
  across the whole sweep. Occupancy is FLAT. Whatever the rate curve does here is therefore the
  algorithm alone: more codes per lane amortise the scan and the drain until the live low-plane
  bytes stop paying for themselves. That peak is real and it is K=6 at T=256.

  B=8 (right).  Asking for eight resident blocks caps registers at R/(T*B) = 32. At small K that
  is affordable and buys nominal occupancy. At K>=6 it is not: the working set no longer fits, and
  residency FALLS to 5 blocks anyway. The constraint that was supposed to buy occupancy loses it,
  and the rate collapses to roughly a third.

So the deployment rule is the opposite of the intuition that more resident blocks are better: set
B low and let the compiler and the scheduler settle occupancy themselves. They arrive at the same
residency without being told, and without the register cap that breaks the large-K regime.

T IS THE THIRD PARAMETER AND IT MOVES THE OPTIMUM RATHER THAN THE CEILING. More warps per block
put more tokens in flight, so the K that best amortises a scan shifts up with T: T=64 and T=128
peak at K=4, T=256 at K=6, and T=256 reaches the highest rate of the three. T=128 is the safe
choice because it is never far from either regime -- a median 1.1% and at most 3.0% below the best
T per column -- and it is never the best one.

Curves are the MEDIAN over the ten real columns at OnPair-12; the shape is the claim, and one
column would invite a reader to take its peak as a rate. Registers and residency come from the
resource probe at the same coordinate, so the annotation is measured, not modelled.

Source: results/suite-<id>/b300/sweep_summary_*_boost.json (dg family) joined to
kernel_resources.jsonl on (K, T, B).
"""
import argparse
import json
import re
import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402
import suite as S  # noqa: E402

KS = list(range(1, 9))
TS = [64, 128, 256]
PANELS = [(1, "B=1: compiler unconstrained"), (8, "B=8: eight blocks demanded")]
T_COLOR = {64: "#9ecae1", 128: "#4292c6", 256: "#08519c"}
DEV, BITS = "b300", 12


def dg_rates(cell):
    out = {}
    g = cell.get("gpu") or {}
    db = g.get("decoded_bytes")
    for k in (g.get("kernels") or []):
        m = re.match(r"onpair_dg_k(\d+)_t(\d+)_b(\d+)$", k.get("kernel", ""))
        if m and k.get("decode_ns_iters") and db:
            out[(int(m.group(1)), int(m.group(2)), int(m.group(3)))] = db / min(k["decode_ns_iters"])
    return out


def resources(root, chip):
    """(K,T,B) -> probe row, H=1 only: the dg family carries no hoist."""
    out = {}
    f = Path(root) / chip / "kernel_resources.jsonl"
    if not f.exists():
        return out
    for line in open(f):
        if not line.strip():
            continue
        d = json.loads(line)
        if d.get("buildable") and d.get("held_high", 1) == 1:
            out[(d["tokens_per_thread"], d["block_threads"], d["min_blocks"])] = d
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
    grids = [g for g in (dg_rates(c) for (ds, col, bits), c in cells.items()
                         if (ds, col) in real and bits == BITS) if g]
    res = resources(root, DEV)
    if not grids:
        sys.exit("no dg coordinates found; is this a full-grid pass?")

    plt = C.apply_theme()
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.35), sharey=True)
    for ax, (B, title) in zip(axes, PANELS):
        for T in TS:
            ys = [st.median([g[(K, T, B)] for g in grids if (K, T, B) in g]) or None
                  if any((K, T, B) in g for g in grids) else None for K in KS]
            xs = [k for k, y in zip(KS, ys) if y]
            yy = [y for y in ys if y]
            ax.plot(xs, yy, marker="o", ms=3.0, lw=1.2, color=T_COLOR[T], label=f"T={T}")
        # Residency at T=256, the widest block, as the measured counterpoint to the rate curve.
        occ = [(K, res[(K, 256, B)]["blocks_per_sm"]) for K in KS if (K, 256, B) in res]
        if occ:
            ax2 = ax.twinx()
            ax2.plot([k for k, _ in occ], [b for _, b in occ], color="#b0413e", lw=1.0,
                     ls=(0, (3, 2)), zorder=1)
            ax2.set_ylim(0, 10)
            ax2.set_yticks([0, 4, 8])
            ax2.tick_params(axis="y", colors="#b0413e", labelsize=6)
            if B == PANELS[-1][0]:
                ax2.set_ylabel("blocks/SM at T=256", color="#b0413e", fontsize=6.5)
            else:
                ax2.set_yticklabels([])
        regs = res.get((6, 256, B), {}).get("regs_per_thread")
        if regs:
            ax.annotate(f"{regs} regs/thread", xy=(0.03, 0.06), xycoords="axes fraction",
                        fontsize=6.3, color=C.INK)
        ax.set_title(title, fontsize=7.5)
        ax.set_xticks([1, 2, 4, 6, 8])
        ax.set_xlabel("K (codes per lane)")
        ax.grid(alpha=.25, lw=.4)
        ax.set_axisbelow(True)
    axes[0].set_ylabel("decode (GB/s)")
    axes[0].set_ylim(0, None)

    from matplotlib.lines import Line2D
    handles = [Line2D([], [], color=T_COLOR[T], marker="o", ms=3, lw=1.2, label=f"T={T}")
               for T in TS]
    handles.append(Line2D([], [], color="#b0413e", lw=1.0, ls=(0, (3, 2)),
                          label="resident blocks/SM (T=256, measured)"))
    fig.legend(handles=handles, frameon=False, fontsize=6.5, ncol=4, loc="lower center",
               bbox_to_anchor=(0.5, -0.03), columnspacing=1.1, handlelength=1.6)
    fig.tight_layout(rect=(0, 0.10, 1, 1))
    C.save(fig, "fig_grid")

    for B, _ in PANELS:
        row = res.get((6, 256, B), {})
        peak = max(((K, st.median([g[(K, 256, B)] for g in grids if (K, 256, B) in g]))
                    for K in KS if any((K, 256, B) in g for g in grids)), key=lambda kv: kv[1])
        print(f"B={B}: T=256 regs={row.get('regs_per_thread')} "
              f"blocks(K=6)={row.get('blocks_per_sm')}  peak at K={peak[0]} ({peak[1]:.0f} GB/s)")
    for T in TS:
        peak = max(((K, st.median([g[(K, T, 1)] for g in grids if (K, T, 1) in g]))
                    for K in KS if any((K, T, 1) in g for g in grids)), key=lambda kv: kv[1])
        print(f"B=1, T={T}: peak at K={peak[0]} ({peak[1]:.0f} GB/s)")


if __name__ == "__main__":
    main()
