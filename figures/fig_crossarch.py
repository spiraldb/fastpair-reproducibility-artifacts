# /// script
# requires-python = ">=3.9"
# dependencies = ["matplotlib", "numpy"]
# ///
"""Fig. crossarch: decode throughput across the four GPUs, one labeled line per column.

The companion to fig_sota, which fixes the device and varies the codec; this fixes the
codec and varies the device. Two panels, one per preset (FastPair-12 | FastPair-16). x is
the four GPUs ordered by VENDOR-RATED peak memory bandwidth (L40S 0.86 -> A100 1.56 ->
H100 3.35 -> B300 8.0 TB/s, Sec. 2's architecture table), a spec ordering independent of
anything we measured; y is absolute decode rate, log, so the 1 TB/s crossing is readable.
Every column is named at the right edge, which the range-bar form could not do.

A fifth x slot, set off by a gap, carries THAT COLUMN'S B300 Decompression Engine rate
(best valid engine codec, Snappy overlay included), joined to the B300 FastPair point by a
dotted segment. Per-column is the only fair way to draw the engine: its rate varies 202 to
662 GB/s across these columns, so a single band would compare one column's software
against another column's hardware. With the endpoint drawn per column, a FastPair marker
sitting above its own dotted endpoint at the L40S or A100 position is the cross-device
result: decode on an older or GDDR6 part beating Blackwell's dedicated decompression
silicon on the same data. That comparison is across devices, and the caption says so.

Launch-bound columns (C.LAUNCH_BOUND: the 1-6 MB dbtext set and TPC-H s_comment) are
absent, as in fig_sota: their cells are launch- and latency-bound, not throughput.
Source: results/{a100,l40s,h100,b300}/onpair_summary_*.json + b300/onpair_nvcomp_hw.json
+ b300-campaign-0717/onpair_nvcomp_hw.json (the DE Snappy overlay).
"""
import json

import numpy as np

import common as C

# Chips left to right by vendor peak bandwidth (TB/s), NOT by our measurements.
ORDER = ["l40s", "a100", "h100", "b300"]
PEAK_TBS = {"l40s": 0.86, "a100": 1.56, "h100": 3.35, "b300": 8.0}
DE_X = len(ORDER) + 0.55          # the engine slot, set off by a gap
# Names go in a LEFT margin, anchored to each column's L40S rate. The right side is
# occupied by the engine connectors, and ten labels among them was unreadable.
LABEL_X = -0.45

# (dataset, column, right-edge label). Same 10 columns as fig_sota.
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
# Synthetic columns (low cardinality) vs real text columns: one hue each, so the two
# families stay separable among ten lines without a ten-entry color legend.
SYNTH = {("lship", "l_shipinstruct"), ("synthetic", "url")}


def series(dataset, column, bits):
    """(x indices, GB/s) across ORDER, skipping chips with no cell for this column."""
    xs, ys = [], []
    for i, g in enumerate(ORDER):
        t = C.best_shipped(C.cell(g, dataset, column, bits))
        if t:
            xs.append(i)
            ys.append(t)
    return xs, ys


def de_rates():
    """{(dataset, column): best valid B300 engine codec rate in GB/s}, Snappy included.

    Mirrors fig_sota's treatment: canonical b300 carries Deflate/LZ4, and the all-codec
    campaign run adds Snappy on the same B300 class. Taking the best over codecs is the
    strong reading of the baseline, matching how the paper reports the engine.
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


def _declutter(ys, lo, hi, gap=0.050):
    """Nudge right-edge label positions apart in log space, preserving their order.

    The long-text columns land within ~10% of each other on the B300, so their labels
    would overlap at 5.4 pt. Sweep up then down enforcing a minimum log10 separation.
    """
    idx = sorted(range(len(ys)), key=lambda i: ys[i])
    pos = {i: np.log10(ys[i]) for i in idx}
    for a, b in zip(idx, idx[1:]):
        if pos[b] - pos[a] < gap:
            pos[b] = pos[a] + gap
    for a, b in zip(idx[::-1], idx[::-1][1:]):
        if pos[a] - pos[b] < gap:
            pos[b] = pos[a] - gap
    return {i: float(np.clip(10 ** p, lo, hi)) for i, p in pos.items()}


def panel(ax, bits, de, show_ylabel, ylim):
    ax.axhline(1000.0, color=C.INK, lw=0.5, ls=(0, (4, 3)), alpha=0.55, zorder=2)
    ends, drawn = {}, []
    for k, (dataset, column, label) in enumerate(COLS):
        xs, ys = series(dataset, column, bits)
        if len(xs) < 2:
            continue
        color = "#74c476" if (dataset, column) in SYNTH else C.PRIMARY
        ax.plot(xs, ys, color=color, lw=1.0, marker="o", ms=2.6, alpha=0.9, zorder=4)
        d = de.get((dataset, column))
        if d:
            # This column's own engine rate, joined to its own B300 point. Kept faint:
            # ten connectors at full weight read as a solid fan and buried the data.
            ax.plot([xs[-1], DE_X], [ys[-1], d], color=C.WARM, lw=0.4, ls=":",
                    alpha=0.45, zorder=3)
            ax.plot([DE_X], [d], color=C.WARM, marker="_", ms=7, mew=1.4, zorder=5)
        ends[k] = ys[0]
        drawn.append((k, label, color))
    at = _declutter(ends, ylim[0] * 1.02, ylim[1] * 0.98)
    for k, label, color in drawn:
        # Decluttering moves a label off its line's height, so a leader restores the
        # mapping: without it the stack order is the only cue, and the L40S rates are close.
        ax.plot([LABEL_X + 0.06, 0.0], [at[k], ends[k]], color=color, lw=0.35,
                alpha=0.45, zorder=3, clip_on=False)
        ax.annotate(label, (LABEL_X, at[k]), xytext=(0, 0), textcoords="offset points",
                    fontsize=5.4, color=color, va="center", ha="right", zorder=6)
    ax.set_xticks(list(range(len(ORDER))) + [DE_X])
    ax.set_xticklabels(["%s\n%.2f TB/s" % (C.GPU_LABEL[g], PEAK_TBS[g]) for g in ORDER]
                       + ["B300\nengine"], fontsize=5.8)
    ax.set_xlim(LABEL_X - 2.05, DE_X + 0.3)
    ax.set_yscale("log")
    ax.set_ylim(*ylim)
    ax.set_title("FastPair-%d" % bits, fontsize=8)
    if show_ylabel:
        ax.set_ylabel("decode (GB/s, log)")


def main():
    de = de_rates()
    ylim = (150, 2600)
    plt = C.apply_theme()
    fig, (ax12, ax16) = plt.subplots(1, 2, figsize=(7.0, 2.8), sharey=True)
    panel(ax12, 12, de, True, ylim)
    panel(ax16, 16, de, False, ylim)
    from matplotlib.lines import Line2D
    handles = [
        Line2D([], [], color=C.PRIMARY, lw=1.0, marker="o", ms=3, label="real column"),
        Line2D([], [], color="#74c476", lw=1.0, marker="o", ms=3, label="synthetic (low cardinality)"),
        Line2D([], [], color=C.WARM, lw=0.6, ls=":", marker="_", ms=6, mew=1.4,
               label="same column on the B300 Decompression Engine"),
        Line2D([], [], color=C.INK, lw=0.5, ls=(0, (4, 3)), alpha=0.55, label="1 TB/s"),
    ]
    fig.legend(handles=handles, frameon=False, fontsize=6.3, ncol=4, loc="lower center",
               bbox_to_anchor=(0.0, -0.03, 1.0, 0.1), mode="expand",
               columnspacing=1.0, handlelength=1.8, handletextpad=0.6, borderaxespad=0.0)
    fig.tight_layout(rect=(0, 0.1, 1, 1))
    C.save(fig, "fig_crossarch")

    # Report what the figure asserts, so the prose quotes derived numbers rather than eyeballed ones.
    for bits in (12, 16):
        n_all = 0
        for dataset, column, label in COLS:
            d = de.get((dataset, column))
            xs, ys = series(dataset, column, bits)
            if not d or not xs:
                continue
            short = [C.GPU_LABEL[ORDER[i]] for i, y in zip(xs, ys) if y <= d]
            if not short:
                n_all += 1
            else:
                print("FastPair-%d %-22s DE=%4.0f  below-DE: %s" % (bits, label, d, ",".join(short)))
        print("FastPair-%d: %d of %d columns where ALL FOUR GPUs beat the B300 engine"
              % (bits, n_all, len([1 for c in COLS if (c[0], c[1]) in de])))


if __name__ == "__main__":
    main()
