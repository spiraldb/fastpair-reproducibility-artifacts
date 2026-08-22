# /// script
# requires-python = ">=3.9"
# dependencies = ["matplotlib", "numpy"]
# ///
"""Fig. hoist: decode rate over (K, H), at three launch bounds.

The hoist is not a one-parameter change, which is why lines, arrows and bars all read badly here:
each series had to carry which B AND which H at once, so the reader was asked to hold two
encodings in mind to see a single comparison. It is a surface. Two inputs, K and H, one output,
repeated at each launch bound. B=4 is included because fig_grid shows it is where the register
ceiling still clears the kernel's demand, so it should behave like B=1 rather than like B=8 --- a
prediction this figure either confirms or breaks.

So: a grid. K across, H up, decode rate as colour, one panel per B, ONE shared scale so the panels
can be compared directly. Cells above H = min(K,4) do not exist and are left blank.

WHAT TO LOOK AT. At B=1 and B=4 the colour is flat up each column: raising H changes nothing,
because registers were never scarce, and the two panels are indistinguishable. At B=8 the H=1 row
darkens sharply from K=5 on -- that is the register cap, not the hoist -- and raising H lightens it
again without ever reaching the shade the other two panels hold at the same K. The hoist recovers
ground the launch bound gave away.

The B=4 panel is the prediction fig_grid makes, tested: the ceiling R/(T*B) is 64 registers there
against the kernel's 56, so it should behave like B=1, and it does.

Source: results/suite-<id>/b300/sweep_summary_*_boost.json, dh family for H>1 and dg for H=1, at
matched (K,T,B).
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402
import suite as S  # noqa: E402

KS = list(range(2, 9))
HS = [1, 2, 3, 4]
BS = [1, 4, 8]
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

    import numpy as np
    grids = {}
    for B in BS:
        M = np.full((len(HS), len(KS)), np.nan)
        for j, K in enumerate(KS):
            for i, H in enumerate(HS):
                if H > min(K, 4):
                    continue
                name = (f"onpair_dg_k{K}_t{T}_b{B}" if H == 1
                        else f"onpair_dh_k{K}_t{T}_b{B}_h{H}")
                if name in R:
                    M[i, j] = R[name]
        grids[B] = M
    allv = np.concatenate([m[~np.isnan(m)] for m in grids.values()])
    if not allv.size:
        sys.exit("no dg/dh coordinates found; is this a full-grid pass?")
    vmin, vmax = allv.min(), allv.max()

    plt = C.apply_theme()
    fig, axes = plt.subplots(1, len(BS), figsize=(7.0, 1.45), sharey=True)
    im = None
    for ax, B in zip(axes, BS):
        im = ax.imshow(grids[B], origin="lower", aspect="auto", cmap="viridis",
                       vmin=vmin, vmax=vmax,
                       extent=(-0.5, len(KS) - 0.5, -0.5, len(HS) - 0.5))
        # The rate is printed in the cell: a reader comparing two panels should not have to
        # estimate a number from a colour.
        for j in range(len(KS)):
            for i in range(len(HS)):
                v = grids[B][i, j]
                if not np.isnan(v):
                    ax.text(j, i, f"{v:.0f}", ha="center", va="center", fontsize=5.0,
                            color="white" if v < (vmin + vmax) / 2 else "#222222")
        ax.set_xticks(range(len(KS)))
        ax.set_xticklabels([str(k) for k in KS])
        ax.set_yticks(range(len(HS)))
        ax.set_yticklabels([str(h) for h in HS])
        ax.set_xlabel("K (codes per lane)")
        ax.set_title(f"B={B}", fontsize=7.5)
        ax.grid(False)
    axes[0].set_ylabel("H (held rounds)")
    # Every cell carries its rate, so the bar orients the reader between dark and light rather
    # than being read off. Five ticks keep the ramp legible without competing with the numbers.
    cb = fig.colorbar(im, ax=axes, fraction=0.03, pad=0.015,
                      ticks=[round(vmin + (vmax - vmin) * f, -2) for f in (0, .25, .5, .75, 1)])
    cb.set_label("decode (GB/s)", fontsize=6.5)
    cb.ax.tick_params(labelsize=6)
    C.save(fig, "fig_hoist")

    for B in BS:
        for K in (6,):
            vals = [(H, grids[B][HS.index(H), KS.index(K)]) for H in HS
                    if not np.isnan(grids[B][HS.index(H), KS.index(K)])]
            print(f"B={B}, K={K}: " + "  ".join(f"H={h} {v:.0f}" for h, v in vals))


if __name__ == "__main__":
    main()
