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

# (dataset, column, label, origin) with origin S = synthetic, R = real, matching fig_sota's
# panel split and tab:datasets' grouping.
COLS = [
    ("tpch-sf10", "l_comment", "TPC-H l_comment", "S"),
    ("tpch-sf10", "ps_comment", "TPC-H ps_comment", "S"),
    ("lship", "l_shipinstruct", "l_shipinstruct", "S"),
    ("synthetic", "url", "synthetic URL", "S"),
    ("clickbench", "URL", "ClickBench URL", "R"),
    ("fineweb", "text", "FineWeb text", "R"),
    ("wikipedia", "text", "Wikipedia text", "R"),
    ("book-reviews", "text", "book-reviews", "R"),
    ("amazon-movies", "text", "amazon-movies", "R"),
    ("amazon-electronics", "text", "amazon-electronics", "R"),
]

# Which engine codec actually wins varies by column: Deflate-hi on the synthetics and
# ClickBench URL, LZ4 or Snappy on the long-text columns. So the rule is drawn in that
# codec's own shade, reusing fig_sota's DE ramp verbatim, and the legend names the three
# winners instead of an anonymous "engine". Shades must track fig_sota.CFG.
# Short tick labels. At 0.75x height the rotated label block is a fixed cost that competes
# directly with the plot area: full names squeezed the panels to ~0.8 in, where the L40S/A100
# and H100/B300 dots merged. The dataset family stays recoverable from the group label plus
# tab:datasets, so the abbreviation costs less than the lost vertical resolution.
SHORT = {
    "TPC-H l_comment": "l_comment", "TPC-H ps_comment": "ps_comment",
    "l_shipinstruct": "l_shipinstr.", "synthetic URL": "synth. URL",
    "ClickBench URL": "ClickBench", "FineWeb text": "FineWeb",
    "Wikipedia text": "Wikipedia", "book-reviews": "book-rev.",
    "amazon-movies": "amz-movies", "amazon-electronics": "amz-electr.",
}

DE_CODEC_NAME = {"DEFLATE-hi": "Deflate (5)", "DEFLATE-fast": "Deflate (0)",
                 "LZ4": "LZ4", "Snappy": "Snappy"}
DE_CODEC_COLOR = {"Deflate (5)": "#e08214", "Deflate (0)": "#fdd0a2",
                  "LZ4": "#e6550d", "Snappy": "#a63603"}


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
    for dataset, column, _, _ in COLS:
        did = "tpch-sf10" if dataset in ("tpch-sf10", "lship") else dataset
        e = de.get((did, column))
        if not e:
            continue
        best = [(v["decode_gib_s"] * C.GIB_TO_GB, DE_CODEC_NAME.get(n, n))
                for n, v in (e.get("codecs") or {}).items()
                if v.get("decode_gib_s") and v.get("ratio")]
        if best:
            out[(dataset, column)] = max(best)   # (rate, winning codec name)
    return out


def panel(ax, bits, order, de, show_ylabel, ylim, split):
    # No 1 TB/s rule: the 1000 tick and its gridline already mark that line exactly, so the
    # dashed overlay was drawing the same fact twice and needed a legend row to explain it.
    for x, (dataset, column, label, _) in enumerate(order):
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
            rate, codec = d
            ax.plot([x - 0.30, x + 0.30], [rate, rate], color=DE_CODEC_COLOR.get(codec, C.WARM),
                    lw=1.9, solid_capstyle="butt", zorder=3)
    # Divide synthetic from real. The two groups answer different questions (low-cardinality
    # dictionaries versus dictionaries that fill), and the engine's own behaviour differs
    # sharply across the boundary, so leaving it implicit in the ordering hid a real seam.
    if split:
        ax.axvline(split - 0.5, color="#b9bdc2", lw=0.7, zorder=1)
        for lo, hi, name in ((0, split, "synthetic"), (split, len(order), "real")):
            ax.text((lo + hi - 1) / 2.0, 1.015, name, fontsize=6.0, style="italic",
                    color=C.INK, ha="center", va="bottom", zorder=6,
                    transform=ax.get_xaxis_transform())
    ax.set_xticks(range(len(order)))
    ax.set_xticklabels([SHORT.get(l, l) for _, _, l, _ in order], fontsize=5.4, rotation=47,
                       ha="right", rotation_mode="anchor")
    ax.set_xlim(-0.6, len(order) - 0.4)
    ax.set_yscale("log")
    ax.set_ylim(*ylim)
    from matplotlib.ticker import FixedLocator, FuncFormatter, NullFormatter
    ax.yaxis.set_major_locator(FixedLocator([200, 500, 1000, 2000]))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: "%d" % v))
    ax.yaxis.set_minor_locator(FixedLocator([]))
    ax.yaxis.set_minor_formatter(NullFormatter())
    ax.set_title("FastPair-%d" % bits, fontsize=8, pad=10)
    if show_ylabel:
        ax.set_ylabel("decode (GB/s, log)")


def main():
    de = de_rates()
    # One x order for both panels, by B300 FastPair-12 rate descending, so a column keeps
    # its position between the panels and the profile reads as a descent.
    # Synthetic first, then real, each by B300 FastPair-12 rate descending.
    def key(c):
        return (0 if c[3] == "S" else 1, -(rates(c[0], c[1], 12).get("b300") or 0))
    order = sorted(COLS, key=key)
    split = sum(1 for c in order if c[3] == "S")
    ylim = (170, 2300)
    plt = C.apply_theme()
    fig, (ax12, ax16) = plt.subplots(1, 2, figsize=(7.0, 1.95), sharey=True)
    panel(ax12, 12, order, de, True, ylim, split)
    panel(ax16, 16, order, de, False, ylim, split)
    from matplotlib.lines import Line2D
    handles = [Line2D([], [], color=GPU_COLOR[g], marker="o", ls="", ms=4.5,
                      label=C.GPU_LABEL[g] + (" (GDDR6)" if g == "l40s" else ""))
               for g in ORDER]
    # Name the engine codecs that actually win a column, in the order they first appear
    # left to right, rather than an anonymous "engine" swatch.
    winners = []
    for dataset, column, _, _ in order:
        d = de.get((dataset, column))
        if d and d[1] not in winners:
            winners.append(d[1])
    handles += [Line2D([], [], color=DE_CODEC_COLOR.get(w, C.WARM), lw=1.9,
                       label="B300 DE: %s" % w) for w in winners]
    fig.legend(handles=handles, frameon=False, fontsize=6.3, ncol=7, loc="lower center",
               bbox_to_anchor=(0.0, -0.01, 1.0, 0.09), mode="expand",
               columnspacing=0.8, handlelength=1.3, handletextpad=0.5, borderaxespad=0.0)
    fig.tight_layout(rect=(0, 0.11, 1, 1))
    C.save(fig, "fig_crossarch")

    # Report what the figure asserts so the prose quotes derived numbers, not eyeballed ones.
    for bits in (12, 16):
        clean = 0
        for dataset, column, label, _ in COLS:
            d = de.get((dataset, column))
            rs = rates(dataset, column, bits)
            if not d or not rs:
                continue
            rate, codec = d
            below = [C.GPU_LABEL[g] for g, t in rs.items() if t <= rate]
            if below:
                print("FastPair-%d %-22s engine=%4.0f (%-11s)  below: %s"
                      % (bits, label, rate, codec, ",".join(below)))
            else:
                clean += 1
        print("FastPair-%d: %d of %d columns where all four GPUs clear the engine"
              % (bits, clean, len([1 for c in COLS if (c[0], c[1]) in de])))


if __name__ == "__main__":
    main()
