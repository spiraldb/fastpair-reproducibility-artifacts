# /// script
# requires-python = ">=3.9"
# dependencies = ["matplotlib", "numpy"]
# ///
"""Fig. crossarch: per-column decode rate on all four GPUs against that column's engine rate.

The companion to fig_sota, which fixes the device and varies the codec; this fixes the codec
and varies the device. One strip per column: four dots, one per GPU, shaded so the chip is
readable without a leader, joined by a thin rule to group them, plus an orange tick at THAT
column's B300 Decompression Engine rate. Two panels, one per preset.

This replaced a slopegraph (GPUs on x, one line per column). That form could not work on this
data: at the L40S the eight real columns span just 30%, about 0.11 decades, so ten lines
entered the panel almost coincident, needed decluttered labels with leaders to be identified
at all, and crossed a fan of engine connectors on the way out. The strip form removes the
demand that a reader track a line, because neither of the figure's jobs needs it:

- Absolute rates across four architectures, so 1,689 GB/s and the 1 TB/s line stay readable.
- Whether a column's whole strip clears its own engine tick. That is the paper's cross-device
  result, and it is now a single local comparison repeated ten times rather than something
  recovered from a fan.

Ordering is by B300 FastPair-12 rate, descending, and the SAME order is used in both panels so
a column sits at one x position throughout. The L40S keeps a separate hue because it is the one
GDDR6 part; the three HBM chips take a light-to-dark blue ramp in bandwidth order. A dot below
its neighbours breaks the ramp visibly, which is the honest rendering of a non-monotonicity
(ClickBench URL is faster on the L40S than on the A100 at FastPair-12).
Source: results/{a100,l40s,h100,b300}/onpair_summary_*.json + b300/onpair_nvcomp_hw.json
+ b300-campaign-0717/onpair_nvcomp_hw.json (the DE Snappy overlay).
"""
import json

import numpy as np

import common as C

# Ordered by vendor peak bandwidth: L40S 0.86, A100 1.56, H100 3.35, B300 8.0 TB/s.
ORDER = ["l40s", "a100", "h100", "b300"]
# The L40S is the one GDDR6 part and the paper leans on that; give it its own hue and put the
# three HBM chips on a light-to-dark blue ramp so their order reads as a ramp.
GPU_COLOR = {"l40s": "#74c476", "a100": "#9ecae1", "h100": "#3182bd", "b300": "#08519c"}
# x offsets within a column slot, in ORDER (bandwidth) order.
DODGE = [-0.20, -0.067, 0.067, 0.20]

COLS = [
    ("tpch-sf10", "l_comment", "TPC-H l_comment"),
    ("tpch-sf10", "ps_comment", "TPC-H ps_comment"),
    ("lship", "l_shipinstruct", "l_shipinstruct"),
    ("synthetic", "url", "synthetic URL"),
    ("clickbench", "URL", "ClickBench URL"),
    ("fineweb", "text", "FineWeb text"),
    ("wikipedia", "text", "Wikipedia text"),
    ("book-reviews", "text", "book-reviews"),
    ("amazon-movies", "text", "amazon-movies"),
    ("amazon-electronics", "text", "amazon-electronics"),
]


def rates(dataset, column, bits):
    """{gpu: GB/s} for one column and preset, omitting GPUs with no cell."""
    out = {}
    for g in ORDER:
        t = C.best_shipped(C.cell(g, dataset, column, bits))
        if t:
            out[g] = t
    return out


def de_rates():
    """{(dataset, column): best valid B300 engine codec rate in GB/s}, Snappy included.

    Mirrors fig_sota: canonical b300 carries Deflate/LZ4 and the all-codec campaign run adds
    Snappy on the same B300 class. Best-over-codecs is the strong reading of the baseline and
    matches how the paper reports the engine. Per column is the only fair form: the engine
    spans 202 to 662 GB/s here, so one line for all columns would compare one column's
    software against another column's hardware.
    """
    de = {(e["dataset_id"], e["column"]): e
          for e in json.load(open(C.RESULTS / "b300" / "onpair_nvcomp_hw.json"))}
    try:
        snap = {(e["dataset_id"], e["column"]): e
                for e in json.load(open(C.RESULTS / "b300-campaign-0717" / "onpair_nvcomp_hw.json"))}
        for k, e in de.items():
            s = snap.get(k, {}).get("codecs", {}).get("Snappy")
            if s and s.get("valid"):
                e["codecs"]["Snappy"] = s
    except FileNotFoundError:
        pass
    out = {}
    for dataset, column, _ in COLS:
        did = "tpch-sf10" if dataset in ("tpch-sf10", "lship") else dataset
        e = de.get((did, column))
        if not e:
            continue
        best = [v["decode_gib_s"] * C.GIB_TO_GB for v in (e.get("codecs") or {}).values()
                if v.get("decode_gib_s") and v.get("ratio")]
        if best:
            out[(dataset, column)] = max(best)
    return out


def panel(ax, bits, order, de, show_ylabel, ylim):
    ax.axhline(1000.0, color=C.INK, lw=0.5, ls=(0, (4, 3)), alpha=0.5, zorder=1)
    for x, (dataset, column, label) in enumerate(order):
        rs = rates(dataset, column, bits)
        if not rs:
            continue
        # Dodge the four chips along x, in bandwidth order. Two purposes: the L40S and A100
        # land within a few percent on several columns (425 against 413 on amazon-electronics)
        # and would overplot at a single x; and once dodged, the connected dots read left to
        # right as chip order, so each column carries its own scaling shape while no line ever
        # crosses into a neighbouring column.
        xs = [x + d for d, g in zip(DODGE, ORDER) if g in rs]
        ys = [rs[g] for g in ORDER if g in rs]
        ax.plot(xs, ys, color="#c8ccd0", lw=0.8, zorder=2)
        for xi, g in zip(xs, [g for g in ORDER if g in rs]):
            ax.scatter([xi], [rs[g]], s=17, color=GPU_COLOR[g], zorder=4,
                       edgecolors="white", linewidths=0.3)
        d = de.get((dataset, column))
        if d:
            ax.plot([x - 0.30, x + 0.30], [d, d], color=C.WARM, lw=1.5,
                    solid_capstyle="butt", zorder=3)
    ax.set_xticks(range(len(order)))
    ax.set_xticklabels([l for _, _, l in order], fontsize=5.4, rotation=38,
                       ha="right", rotation_mode="anchor")
    ax.set_xlim(-0.6, len(order) - 0.4)
    ax.set_yscale("log")
    ax.set_ylim(*ylim)
    from matplotlib.ticker import FixedLocator, FuncFormatter, NullFormatter
    ax.yaxis.set_major_locator(FixedLocator([200, 500, 1000, 2000]))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: "%d" % v))
    ax.yaxis.set_minor_locator(FixedLocator([]))
    ax.yaxis.set_minor_formatter(NullFormatter())
    ax.set_title("FastPair-%d" % bits, fontsize=8)
    if show_ylabel:
        ax.set_ylabel("decode (GB/s, log)")


def main():
    de = de_rates()
    # One x order for both panels, by B300 FastPair-12 rate descending, so a column keeps
    # its position between the panels and the profile reads as a descent.
    order = sorted(COLS, key=lambda c: -(rates(c[0], c[1], 12).get("b300") or 0))
    plt = C.apply_theme()
    fig, (ax12, ax16) = plt.subplots(1, 2, figsize=(7.0, 2.6), sharey=True)
    panel(ax12, 12, order, de, True, (170, 2300))
    panel(ax16, 16, order, de, False, (170, 2300))
    from matplotlib.lines import Line2D
    handles = [Line2D([], [], color=GPU_COLOR[g], marker="o", ls="", ms=4.5,
                      label=C.GPU_LABEL[g] + (" (GDDR6)" if g == "l40s" else ""))
               for g in ORDER]
    handles += [
        Line2D([], [], color=C.WARM, lw=1.5, label="same column, B300 engine"),
        Line2D([], [], color=C.INK, lw=0.5, ls=(0, (4, 3)), alpha=0.5, label="1 TB/s"),
    ]
    fig.legend(handles=handles, frameon=False, fontsize=6.3, ncol=6, loc="lower center",
               bbox_to_anchor=(0.0, -0.01, 1.0, 0.09), mode="expand",
               columnspacing=0.8, handlelength=1.3, handletextpad=0.5, borderaxespad=0.0)
    fig.tight_layout(rect=(0, 0.11, 1, 1))
    C.save(fig, "fig_crossarch")

    # Report what the figure asserts so the prose quotes derived numbers, not eyeballed ones.
    for bits in (12, 16):
        clean = 0
        for dataset, column, label in COLS:
            d = de.get((dataset, column))
            rs = rates(dataset, column, bits)
            if not d or not rs:
                continue
            below = [C.GPU_LABEL[g] for g, t in rs.items() if t <= d]
            if below:
                print("FastPair-%d %-22s engine=%4.0f  below: %s" % (bits, label, d, ",".join(below)))
            else:
                clean += 1
        print("FastPair-%d: %d of %d columns where all four GPUs clear the engine"
              % (bits, clean, len([1 for c in COLS if (c[0], c[1]) in de])))


if __name__ == "__main__":
    main()
