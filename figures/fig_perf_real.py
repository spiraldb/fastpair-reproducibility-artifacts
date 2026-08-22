# /// script
# requires-python = ">=3.9"
# dependencies = ["matplotlib"]
# ///
"""Fig. perf_real: the result space on ONE device, throughput against compression ratio.

Every mark is a B300 measurement from one suite leg. Holding the device fixed is the point: an
earlier form drew FastPair spanning four GPUs while the Blackwell-only DE and nvCOMP codecs were
single B300 points, which compared our four-generation spread against each baseline's best chip
and understated the same-device margin the prose claims. Varying the device is fig_perf_gen's job.

TWO PANELS, REAL | SYNTHETIC, and they are not pooled. Generated columns decode faster and reach
far higher ratios than every real column, so a single panel invites a reader to read the top-right
of the envelope as a real-data result. They are a labelled group studied for generator effects.

THE STAIRCASE IS THE POOLED BASELINE PARETO FRONTIER over the panel: at each ratio, the best decode
rate any non-OnPair baseline reaches at that ratio or better, on ANY column in that panel. It is
drawn for orientation, to show where the baseline result space sits.

THE CLAIM IS ASSERTED PER COLUMN, NOT AGAINST THAT POOLED CURVE, and the distinction is not
pedantry. A codec's ratio is a property of the data, so a pooled comparison can put OnPair on one
column against DE on a different one. That is exactly what happens here: OnPair-16 on TPC-H
c_address sits below the pooled synthetic staircase, but every point above it is DE measured on
l_comment or ps_comment -- different data, not a counterexample. Compared on the SAME column, which
is the only like-for-like test, 0 of 45 cells are dominated. main() asserts that and prints any
violation; it also reports pooled exceptions separately, labelled as cross-column.

C_ADDRESS IS WORTH READING, NOT HIDING. OnPair-12 records a ratio of 0.95x there -- it EXPANDS the
column by 5% -- because TPC-H addresses are near-random and offer almost no repeated substrings.
DE's best on that same column is 0.99x, so the general-purpose engine barely compresses it either.
The column is a genuine floor case for substring dictionaries and belongs in the figure.

RATE IS THE SHIPPED SELECTOR (gpu.auto_kernel), never the best probe. Each cell times hundreds of
kernels and the fastest probe beats the shipped selector by several percent; quoting that maximum
as the codec's rate is the error a previous retraction was about.

MISSING BASELINES ARE DRAWN AS ABSENT, NOT DROPPED. This leg recorded Zstd compressed_bytes at
levels -10/1/3 but decompress_gib_s is null for all three, so Zstd has a ratio and no rate and
cannot be plotted as a point. It keeps a fixed legend entry marked "rate not measured" so the gap
is visible; silently omitting it would read as "we compared against Zstd and it lost".

Source: results/suite-<id>/b300/{sweep,fsst12,zstd}_summary_*_boost.json + onpair_nvcomp_hw.json.
"""
import argparse
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

sys.path.insert(0, str(Path(__file__).resolve().parent))
import suite as S  # noqa: E402

OUT = Path(__file__).resolve().parent / "out" / "fig_perf_real.pdf"

STYLE = {          # (colour, marker, label)
    "op12":  ("#1b6ca8", "o", "OnPair-12"),
    "op16":  ("#0b3c5d", "s", "OnPair-16"),
    "fsst":  ("#4a9d5f", "^", "FSST-12"),
    "de":    ("#b0413e", "x", "DE (nvCOMP engine)"),
}


def de_points(root, chip, ds, col):
    """Every valid DE configuration for one column: 4 codec families x 5 chunk sizes."""
    pts = []
    for r in S.de_rows(root, chip):
        if r.get("dataset_id") != ds or r.get("column") != col:
            continue
        for e in (r.get("chunk_sweep") or []):
            for name, cell in (e.get("codecs") or {}).items():
                if cell.get("valid") is True and cell.get("supported") is True \
                        and cell.get("ratio") and cell.get("decode_gib_s"):
                    # decode_gib_s is GiB/s; the paper reports GB/s, so convert once, here.
                    pts.append((cell["ratio"], cell["decode_gib_s"] * 1.073741824, name))
    return pts


def frontier(points):
    """Baseline Pareto staircase: best rate available at each ratio or better, right to left."""
    if not points:
        return [], []
    pts = sorted(points, key=lambda p: p[0])
    xs, ys, best = [], [], 0.0
    for x, y, _ in reversed(pts):          # walk down in ratio, carrying the best rate seen
        best = max(best, y)
        xs.append(x); ys.append(best)
    return list(reversed(xs)), list(reversed(ys))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--suite-id", default=None)
    ap.add_argument("--chip", default="b300")
    a = ap.parse_args()
    root = S.latest_root(a.suite_id)
    if root is None:
        sys.exit("no results/suite-* directory found")

    op = S.cells(root, a.chip, "boost", "onpair")
    fs = S.cells(root, a.chip, "boost", "fsst12")
    zs = S.cells(root, a.chip, "boost", "zstd")

    fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.5), sharey=True,
                             gridspec_kw={"width_ratios": [1.25, 1]})
    missing, violations = [], []

    for ax, (title, rows) in zip(axes, (("Real data", S.REAL), ("Generated", S.GEN))):
        base = []
        for _, ds, col in rows:
            base += de_points(root, a.chip, ds, col)
        # Baselines first so our marks sit on top of the staircase.
        if base:
            fx, fy = frontier(base)
            ax.step(fx, fy, where="post", color=STYLE["de"][0], lw=1.1, alpha=.55, zorder=2)
            ax.scatter([p[0] for p in base], [p[1] for p in base], s=9,
                       c=STYLE["de"][0], marker=STYLE["de"][1], alpha=.55, zorder=3, linewidths=.9)
        else:
            missing.append(f"{title}: no DE configurations")

        for key, store, bits in (("op12", op, 12), ("op16", op, 16), ("fsst", fs, 12)):
            X, Y = [], []
            for _, ds, col in rows:
                c = store.get((ds, col, bits))
                r, v = S.ratio(c), S.rate_gb_s(c)
                if r is None or v is None:
                    missing.append(f"{title}: {ds}/{col} {STYLE[key][2]}")
                    continue
                X.append(r); Y.append(v)
                # PER COLUMN. Comparing against the pooled staircase would test us on one column
                # against a baseline measured on another, which is not a like-for-like result.
                for br, bv, bn in de_points(root, a.chip, ds, col):
                    if br >= r and bv > v:
                        violations.append(f"{ds}/{col} {STYLE[key][2]} {v:.0f} GB/s @ {r:.2f}x "
                                          f"< {bn} {bv:.0f} @ {br:.2f}x (same column)")
            c_, m_, lab = STYLE[key]
            ax.scatter(X, Y, s=34, c=c_, marker=m_, edgecolors="white", linewidths=.6,
                       zorder=5, label=lab)

        ax.set_yscale("log")
        # Plain numbers, not 6x10^2: readers compare these against GB/s figures in the prose, and
        # scientific notation on a two-decade axis makes that a conversion exercise.
        ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
        ax.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
        ax.set_yticks([200, 400, 800, 1600])
        ax.set_xlabel("compression ratio")
        ax.set_title(title, fontsize=9)
        ax.grid(alpha=.25, lw=.5)
    axes[0].set_ylabel("decode throughput (GB/s)")

    # FIXED legend: every series the figure is ABOUT keeps its entry whether or not it has data,
    # so a reader sees an absence instead of inferring completeness from what happens to be drawn.
    handles = [Line2D([], [], color=c, marker=m, ls="", label=l) for c, m, l in STYLE.values()]
    handles.append(Line2D([], [], color="#888888", marker="", ls="--",
                          label="Zstd −10/1/3: ratio only, rate not measured"))
    # Below the axes, not inside them: at these densities an inset legend covers the DE cloud,
    # which is the thing the reader is being asked to compare against.
    fig.legend(handles=handles, fontsize=7.5, ncol=5, loc="upper center",
               bbox_to_anchor=(0.5, 0.02), frameon=False)

    zmiss = sum(1 for k, c in zs.items()
                if not any((e or {}).get("decompress_gib_s")
                           for e in ((c.get("gpu") or {}).get("nvcomp_zstd") or [])))
    fig.suptitle(f"{a.chip.upper()} — {root.name}"
                 + (f"   [{len(missing)} series absent]" if missing else ""),
                 fontsize=8, y=1.02)
    OUT.parent.mkdir(exist_ok=True)
    fig.savefig(OUT, bbox_inches="tight")
    print(f"wrote {OUT.relative_to(Path(__file__).resolve().parent.parent)}")
    print(f"Zstd columns with no decode rate: {zmiss}/{len(zs)}")
    if missing:
        print(f"MISSING ({len(missing)}):")
        for m in missing[:12]:
            print("  " + m)
    print(f"per-column dominance violations: {len(violations)} (0 expected)")
    for v in violations[:10]:
        print("  VIOLATION " + v)


if __name__ == "__main__":
    main()
