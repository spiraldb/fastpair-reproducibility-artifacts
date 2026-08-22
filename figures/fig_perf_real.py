# /// script
# requires-python = ">=3.9"
# dependencies = ["matplotlib", "numpy"]
# ///
"""Fig. perf_real: the result space on ONE device as throughput vs compression ratio.

Every mark is a B300 measurement from one suite leg. Holding the device fixed is the point: an
earlier form drew our codec spanning four GPUs while the Blackwell-only DE and nvCOMP codecs were
single B300 points, which set our four-generation spread against each baseline's best chip and
understated the same-device margin the prose claims. Varying the device is fig_perf_gen's job.

This deliberately reuses fig_sota's look -- theme, palette, family shapes, log axes, expanded
legend, panel proportions -- because it IS fig_sota rebuilt on the fifteen-column corpus. The
styling is not re-derived here; where they differ, fig_sota is right.

BEST AGAINST BEST. One mark per column per technique, each the best that technique reaches on
that column: the DE's best codec AND chunk size, our best kernel. This is a head-to-head of
tuned configurations, and tuning only one side of it would be the sandbag. Per-column
shipped-selector rates, which are what a deployment gets, are reported in the prose.

THE STAIRCASE IS THE BASELINE PARETO FRONTIER, and the claim is asserted PER COLUMN. A codec's
ratio is a property of the data, so a pooled frontier can put us on one column against a baseline
on another; with c_address in the corpus that produces false violations. Like for like, 0 of 45
cells are dominated.

MISSING BASELINES KEEP THEIR LEGEND ENTRIES. Zstd, gANS and both Bitcomp variants are absent from
this leg -- Zstd's decode rates are null and the nvCOMP software codecs were never collected --
and their swatches stay so the gap is legible as a gap. They are collection bugs to fix, not
considered exclusions.

Source: results/suite-<id>/b300/{sweep,fsst12}_summary_*_boost.json + onpair_nvcomp_hw.json.
"""
import argparse
import itertools
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402
import suite as S  # noqa: E402

YLO, YHI = 0, 1800

# Configuration -> shade, in technique families, copied from fig_sota so a colour means the same
# thing in both figures. OnPair replaces the FastPair label; the hues are unchanged.
CFG = {
    "OnPair-12": "#6baed6", "OnPair-16": "#08519c",
    "FSST-12": "#c994c7",
    "DE Deflate (5)": "#fd8d3c", "DE Deflate (0)": "#fdd0a2", "DE LZ4": "#d94801",
    "DE Snappy": "#7f2704",
    "Zstd (-10)": "#cccccc", "Zstd (1)": "#969696", "Zstd (3)": "#525252",
    "gANS": "#41ab5d", "Bitcomp-default": "#a1d99b", "Bitcomp-sparse": "#006d2c",
}
DE_NAME = {"DEFLATE-hi": "DE Deflate (5)", "DEFLATE-fast": "DE Deflate (0)", "LZ4": "DE LZ4",
           "Snappy": "DE Snappy"}
FAMILY_MARKER = {"OnPair": "o", "DE": "s", "Zstd": "^", "nvCOMP-sw": "D"}
FAMILY = {
    "OnPair-12": "OnPair", "OnPair-16": "OnPair", "FSST-12": "OnPair",
    "DE Deflate (5)": "DE", "DE Deflate (0)": "DE", "DE LZ4": "DE", "DE Snappy": "DE",
    "Zstd (-10)": "Zstd", "Zstd (1)": "Zstd", "Zstd (3)": "Zstd",
    "gANS": "nvCOMP-sw", "Bitcomp-default": "nvCOMP-sw", "Bitcomp-sparse": "nvCOMP-sw",
}
MARKER = {k: FAMILY_MARKER[v] for k, v in FAMILY.items()}
DEV = "b300"
OFFSCALE = []


def oracle_rate(c):
    """Best kernel on this column, GB/s. The oracle side of an oracle-vs-oracle comparison."""
    if not c:
        return None
    g = c.get("gpu") or {}
    best = g.get("best_kernel")
    for k in (g.get("kernels") or []):
        if k.get("kernel") == best and k.get("decode_ns_iters") and g.get("decoded_bytes"):
            return g["decoded_bytes"] / min(k["decode_ns_iters"])
    return (g.get("best_decode_gib_s") or 0) * C.GIB_TO_GB or None


def de_best(root, ds, col):
    """The engine's declared best for a column: best codec AND chunk size. One mark, shaded by
    whichever codec won, so the four DE swatches still carry meaning across the figure."""
    for r in S.de_rows(root, DEV):
        if r.get("dataset_id") == ds and r.get("column") == col \
                and r.get("best_ratio") and r.get("best_decode_gib_s"):
            return (r["best_ratio"], r["best_decode_gib_s"] * C.GIB_TO_GB,
                    DE_NAME.get(r.get("best_codec"), "DE %s" % r.get("best_codec")))
    return None


def frontier(pts, xlo=None):
    """Best baseline rate available at each ratio or better, as a staircase."""
    if not pts:
        return [], []
    xs, ys, best = [], [], 0.0
    for x, y in sorted(pts, reverse=True):
        best = max(best, y)
        xs.append(x); ys.append(best)
    xs, ys = list(reversed(xs)), list(reversed(ys))
    if xlo is not None and xs:
        xs, ys = [xlo] + xs, [ys[0]] + ys
    return xs, ys


def frontier_at(pts, ratio):
    vals = [y for x, y in pts if x >= ratio]
    return max(vals) if vals else None


def mark(ax, r, t, color, marker="o", s=20):
    """Off-scale marks are drawn open at the floor rather than dropped, so a reader can see that
    a family exists below the axis instead of inferring it never ran."""
    if t < YLO:
        OFFSCALE.append((None, t))
        ax.scatter([r], [YLO * 1.04], s=s * 0.8, facecolors="none", marker=marker,
                   edgecolors=color, linewidths=0.7, zorder=5)
        return
    ax.scatter([r], [t], s=s, color=color, marker=marker, zorder=5, linewidths=0)


def collect(root, rows):
    """(ours, baselines) for one panel. ours: (ratio, rate, cfg, column). baselines: (r, t, cfg)."""
    op = S.cells(root, DEV, "boost", "onpair")
    fs = S.cells(root, DEV, "boost", "fsst12")
    ours, bases = [], []
    for _, ds, col in rows:
        for cfg, store, bits in (("OnPair-12", op, 12), ("OnPair-16", op, 16),
                                 ("FSST-12", fs, 12)):
            c = store.get((ds, col, bits))
            r, t = S.ratio(c), oracle_rate(c)
            if r and t:
                ours.append((r, t, cfg, col))
        d = de_best(root, ds, col)
        if d:
            bases.append(d)
    return ours, bases


def panel(ax, root, rows, title):
    from matplotlib.ticker import FixedLocator, ScalarFormatter, NullFormatter
    ours, bases = collect(root, rows)
    bp = [(r, t) for r, t, _ in bases]
    lo = min([r for r, _, _, _ in ours] + [r for r, _ in bp] or [1.0]) * 0.92
    xs, ys = frontier(bp, xlo=lo)
    if xs:
        ax.step(xs, ys, where="pre", color=C.INK, lw=0.8, alpha=0.55, zorder=3)
        ax.fill_between(xs, 1e-3, ys, step="pre", color=C.INK, alpha=0.055, lw=0, zorder=1)
    for r, t, cfg in bases:
        mark(ax, r, t, CFG[cfg], marker=MARKER.get(cfg, "s"), s=26)
    for r, t, cfg, _ in ours:
        mark(ax, r, t, CFG[cfg], marker=MARKER[cfg], s=22)
    ax.set_xscale("log")
    ticks = [1, 1.5, 2, 3, 5, 7, 10, 20]
    ax.xaxis.set_major_locator(FixedLocator(ticks))
    ax.xaxis.set_major_formatter(ScalarFormatter())
    ax.xaxis.set_minor_locator(FixedLocator([]))
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.set_xlabel("compression ratio (log)")
    ax.set_title(title, fontsize=8)
    return ours, bp


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--suite-id", default=None)
    a = ap.parse_args()
    root = S.latest_root(a.suite_id)
    if root is None:
        sys.exit("no results/suite-* directory found")

    plt = C.apply_theme()
    fig, (axR, axS) = plt.subplots(1, 2, figsize=(7.0, 2.03), sharey=True)
    oR, bR = panel(axR, root, S.REAL, "Real-world columns")
    oS, bS = panel(axS, root, S.GEN, "Synthetic columns")

    # ASSERTED PER COLUMN, not against the pooled staircase. The staircase is drawn for
    # orientation, but a pooled test compares us on one column against a baseline measured on
    # ANOTHER, and a codec's ratio is a property of the data. c_address is the live example:
    # OnPair-16 reaches 1.09x there, below a 697 GB/s baseline that belongs to l_comment or
    # ps_comment -- different data, not a counterexample. On its own column the DE manages 0.99x,
    # and we are not dominated.
    violations, n = [], 0
    for rows in (S.REAL, S.GEN):
        ours, _ = collect(root, rows)
        by_col = {}
        for _, ds, col in rows:
            d = de_best(root, ds, col)
            if d:
                by_col[col] = (d[0], d[1])
        for r, t, cfg, col in ours:
            n += 1
            b = by_col.get(col)
            if b and b[0] >= r and b[1] > t:
                violations.append("%s %s: %.0f GB/s at ratio %.2f, DE %.0f at %.2f"
                                  % (col, cfg, t, r, b[1], b[0]))
    if violations:
        raise SystemExit("fig_perf_real: per-column dominance VIOLATED on %s:\n  %s"
                         % (DEV, "\n  ".join(violations)))
    print("per-column dominance holds on %s: %d of %d marks clear the DE on their own column"
          % (DEV, n, n))

    axR.set_ylim(0, YHI)
    axR.set_ylabel("decode throughput (GB/s)")

    from matplotlib.lines import Line2D

    def flip(items, ncol):
        return list(itertools.chain(*[items[i::ncol] for i in range(ncol)]))

    codec_handles = [Line2D([], [], color=CFG[k], marker=MARKER.get(k, "o"), ls="", ms=5.5,
                            label=k) for k in CFG]
    gsst = Line2D([], [], marker="*", color=C.GSST_RED, ls="", ms=9, label="GSST (A100)")
    extra = [Line2D([], [], color=C.INK, lw=0.8, alpha=0.55, label="baseline envelope"),
             Line2D([], [], color=C.INK, marker="^", ls="", ms=5, markerfacecolor="none",
                    label="off-scale (open)")]
    leg = codec_handles[:6] + [gsst] + codec_handles[6:] + extra
    fig.legend(handles=flip(leg, 8), frameon=False, fontsize=6.3, ncol=8, loc="lower center",
               bbox_to_anchor=(0.0, -0.01, 1.0, 0.13), mode="expand",
               columnspacing=0.6, handlelength=1.1, handletextpad=0.45, borderaxespad=0.0)
    fig.tight_layout(rect=(0, 0.155, 1, 1))
    C.save(fig, "fig_perf_real")

    print("\nBASELINES ABSENT FROM THIS LEG -- collection gaps, not findings:")
    print("  Zstd -10/1/3   : ratios recorded, decompress_gib_s null on all 15 columns")
    print("  gANS, Bitcomp-{default,sparse}: never collected; the DE stage runs only "
          "DEFLATE/LZ4/Snappy")
    print("  GSST           : published A100 number, cross-paper; not drawn on a B300 panel")


if __name__ == "__main__":
    main()
