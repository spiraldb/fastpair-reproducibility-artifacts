# /// script
# requires-python = ">=3.9"
# dependencies = ["matplotlib", "numpy"]
# ///
"""Fig. hoist: what H is worth once the launch bound stops confounding it.

H holds up to H-1 long-token requests across rounds rather than re-issuing them. Whether that
helps was previously unanswerable, because the H arm existed only at B in {2,4,8}, where
__launch_bounds__ forces ptxas to fit B blocks per SM and every extra register H costs comes
straight out of residency. A gain measured there mixes what the hoist covers with the occupancy
it costs, and a loss does too.

This campaign adds B=1 and B=6, where the minimum does not itself dictate the register target, so
the trade is not forced by construction. Those are the ISOLATING rungs and they are what this
figure is for.

WHAT IT SHOWS. For each (K,T,B) coordinate, the best H>1 rung against the H=1 baseline at the SAME
coordinate -- same kernel, same launch shape, one parameter changed. One strip per B, isolating
rungs marked. The 0.5% band is the run-to-run noise floor established elsewhere in this section.

THE RESULT IS NEGATIVE, AND THAT IS THE POINT. At the isolating rungs the median gain is about
zero and the 90th percentile is a couple of percent. The large gains are concentrated at B=8,
whose H=1 baseline has itself collapsed under the register cap, so they are recovery from a bad
launch bound rather than evidence that hoisting pays. Reporting the B=8 maximum as H's benefit is
the error this figure exists to prevent.

Source: results/suite-<id>/b300/sweep_summary_*_boost.json, dh family (270 kernels/cell) against
the dg family at the same coordinate.
"""
import argparse
import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402
import suite as S  # noqa: E402

BS = [1, 2, 4, 6, 8]
ISOLATING = {1, 6}
NOISE = 0.5     # percent; the run-to-run floor
DEV = "b300"


def gains(cells, real):
    """B -> [best-H>1 gain over H=1 at the same (K,T,B), percent]."""
    out = {b: [] for b in BS}
    for (ds, col, bits), c in cells.items():
        if (ds, col) not in real:
            continue
        g = c.get("gpu") or {}
        db = g.get("decoded_bytes")
        if not db:
            continue
        R = {k["kernel"]: db / min(k["decode_ns_iters"])
             for k in (g.get("kernels") or []) if k.get("decode_ns_iters")}
        for K in range(1, 9):
            for T in (64, 128, 256):
                for B in BS:
                    base = R.get(f"onpair_dg_k{K}_t{T}_b{B}")
                    if not base:
                        continue
                    hs = [R[n] for h in range(2, min(K, 4) + 1)
                          for n in [f"onpair_dh_k{K}_t{T}_b{B}_h{h}"] if n in R]
                    if hs:
                        out[B].append(100 * (max(hs) / base - 1))
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
    G = gains(cells, real)
    if not any(G.values()):
        sys.exit("no dh/dg pairs found; is this a full-grid pass?")

    plt = C.apply_theme()
    import numpy as np
    fig, ax = plt.subplots(figsize=(7.0, 2.1))
    rng = np.random.default_rng(20260819)      # jitter only; seeded so the figure is stable
    for i, B in enumerate(BS):
        v = G[B]
        if not v:
            continue
        iso = B in ISOLATING
        col = "#08519c" if iso else "#9ecae1"
        ax.scatter(i + rng.uniform(-0.16, 0.16, len(v)), v, s=3.0, alpha=.45,
                   color=col, linewidths=0, zorder=3)
        ax.hlines(st.median(v), i - 0.30, i + 0.30, color=C.INK, lw=1.3, zorder=5)
    ax.axhspan(-NOISE, NOISE, color="#bbbbbb", alpha=.30, lw=0, zorder=1)
    ax.axhline(0, color=C.INK, lw=.5, alpha=.6, zorder=2)
    ax.set_xticks(range(len(BS)))
    ax.set_xticklabels([f"B={b}" + ("\n(isolating)" if b in ISOLATING else "") for b in BS],
                       fontsize=7)
    ax.set_ylabel("best $H{>}1$ over $H{=}1$ (%)")
    ax.set_ylim(-8, 20)     # the B=8 tail runs to +75%; reported in text, not scaled for
    ax.grid(axis="y", alpha=.25, lw=.4)
    ax.set_axisbelow(True)
    from matplotlib.lines import Line2D
    ax.legend(handles=[
        Line2D([], [], color="#08519c", marker="o", ls="", ms=3.5, label="isolating rung"),
        Line2D([], [], color="#9ecae1", marker="o", ls="", ms=3.5, label="register-bound rung"),
        Line2D([], [], color=C.INK, lw=1.3, label="median"),
        Line2D([], [], color="#bbbbbb", lw=5, alpha=.5, label=f"±{NOISE}% noise"),
    ], fontsize=6.4, ncol=4, frameon=False, loc="upper center")
    fig.tight_layout()
    C.save(fig, "fig_hoist")

    print(f"{'B':>3}{'n':>6}{'median':>9}{'p90':>8}{'max':>8}{'>noise':>8}")
    for B in BS:
        v = sorted(G[B])
        if not v:
            continue
        p90 = v[max(0, -(-int(0.9 * len(v))) - 1)]      # nearest-rank
        print(f"{B:>3}{len(v):>6}{st.median(v):>8.2f}%{p90:>7.1f}%{max(v):>7.1f}%"
              f"{sum(1 for x in v if x > NOISE):>8}")
    iso = [x for B in ISOLATING for x in G[B]]
    bind = [x for B in BS if B not in ISOLATING for x in G[B]]
    print(f"isolating  B in {sorted(ISOLATING)}: n={len(iso)} median {st.median(iso):+.2f}% "
          f"max {max(iso):.1f}%")
    print(f"bound      B in {[b for b in BS if b not in ISOLATING]}: n={len(bind)} "
          f"median {st.median(bind):+.2f}% max {max(bind):.1f}%")


if __name__ == "__main__":
    main()
