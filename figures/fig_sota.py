# /// script
# requires-python = ">=3.9"
# dependencies = ["matplotlib", "numpy"]
# ///
"""Fig. sota: the whole result space as throughput vs compression ratio.

Each (column, *configuration*) is a thin vertical range bar at the column's compression
ratio, spanning that config's best-to-worst decode over the four GPUs (A100->B300); single-
GPU configs (the Blackwell DE) are a tick. Color = configuration, in technique-family
shades (FastPair dict-12/-16; the DE's Deflate algo 5/0 and LZ4; Zstd's levels), so the
within-family split stays visible while the per-GPU marker cloud and its shape legend are
gone. Throughput is LOG here: FastPair (TB/s), the hardware DE (hundreds of GB/s), and
software Zstd (sub-GB/s) span ~4 orders, so a log axis keeps every family visible. Two
panels (real | synthetic) share the throughput axis; the synthetic columns reach far
higher ratios, so the x-axes differ.
Source: results/{a100,l40s,h100,b300}/onpair_summary_*.json + b300/onpair_nvcomp_hw.json
(DE Deflate/LZ4) + b300-campaign-0717/onpair_nvcomp_hw.json (DE Snappy overlay).
"""
import json

import numpy as np

import common as C

COLS = [
    ("tpch-sf10", "l_comment", "tpch-sf10", "S"),
    ("tpch-sf10", "ps_comment", "tpch-sf10", "S"),
    ("lship", "l_shipinstruct", "tpch-sf10", "S"),
    ("synthetic", "url", "synthetic", "S"),
    ("clickbench", "URL", "clickbench", "R"),
    ("fineweb", "text", "fineweb", "R"),
    ("wikipedia", "text", "wikipedia", "R"),
    ("book-reviews", "text", "book-reviews", "R"),
    ("amazon-movies", "text", "amazon-movies", "R"),
    ("amazon-electronics", "text", "amazon-electronics", "R"),
]
# configuration -> shade, in technique-family families (FastPair blues / DE oranges / Zstd grays).
CFG = {
    "FastPair-12": "#6baed6", "FastPair-16": "#08519c",
    "DE Deflate (5)": "#fdae61", "DE Deflate (0)": "#f16913", "DE LZ4": "#a63603",
    "DE Snappy": "#fd8d3c",
    "Zstd (-10)": "#cccccc", "Zstd (1)": "#969696", "Zstd (3)": "#525252",
    # nvCOMP's speed-first software codecs (B300, campaign run): they reach FastPair-class
    # decode rate only by nearly abandoning compression (Bitcomp-sparse ~1.0x, gANS ~1.4-2x).
    # Green family, light->dark: Bitcomp-default, gANS, Bitcomp-sparse.
    "gANS": "#41ab5d", "Bitcomp-default": "#a1d99b", "Bitcomp-sparse": "#006d2c",
}
DE_NAME = {"DEFLATE-hi": "DE Deflate (5)", "DEFLATE-fast": "DE Deflate (0)", "LZ4": "DE LZ4",
           "Snappy": "DE Snappy"}
# Single-GPU configs (B300-only: the hardware DE + nvCOMP speed-first software codecs) are one
# point each, not a per-GPU range, so give each a distinct marker shape. Multi-GPU configs
# (FastPair, Zstd) stay as circle clouds behind a range bar.
MARKER = {
    "DE Deflate (5)": "s", "DE Deflate (0)": "D", "DE LZ4": "^", "DE Snappy": "v",
    "gANS": "P", "Bitcomp-default": "X", "Bitcomp-sparse": "h",
}


def fp_cfg(fn, col, bits):
    # OnPair re-trains its dictionary per box, so mem_ratio jitters slightly across GPUs
    # (≤1.3% on real columns, ~4% on the far-from-cap synthetic ones). The ratio is a column
    # property, reported canonically from the B300 (tab:datasets), so pin x to the B300 value
    # and keep only the per-GPU throughput on y -- no cosmetic x-jitter.
    ts = [t for t in (C.best_shipped(C.cell(g, fn, col, bits)) for g in C.GPUS) if t]
    r = (C.cell("b300", fn, col, bits) or {}).get("mem_ratio")
    if r is None:
        r = next((c.get("mem_ratio") for g in C.GPUS
                  for c in [C.cell(g, fn, col, bits)] if c and c.get("mem_ratio")), None)
    return ([r] * len(ts) if r else []), ts


def zstd_cfg(fn, col, level):
    rs, ts = [], []
    for g in C.GPUS:
        c = C.cell(g, fn, col, 12) or C.cell(g, fn, col, 16)
        for e in ((c or {}).get("gpu") or {}).get("nvcomp_zstd") or []:
            if isinstance(e, dict) and str(e.get("zstd_level")) == level and e.get("compression_ratio") and C.zstd_gb_s(e):
                rs.append(e["compression_ratio"]); ts.append(C.zstd_gb_s(e))
    return rs, ts


def _edge(color, f=0.7):
    """A faint outline keyed to the marker's own color (a darker shade), so overlapping
    points stay distinct without a stark white halo."""
    import matplotlib.colors as mc
    r, g, b = mc.to_rgb(color)
    return (r * f, g * f, b * f)


def range_bar(ax, rs, ts, color, marker="o", s=13):
    """Multi-GPU configs (>=3 points across the GPUs) draw a box over their decode spread,
    matching fig_sota_cpu; single-GPU configs (one point: the hardware DE and nvCOMP software
    codecs) draw a distinct marker (see MARKER). Box width scales with x for the log axis."""
    if not rs or not ts:
        return
    x = float(np.median(rs))
    if len(ts) >= 3:
        ax.boxplot([ts], positions=[x], widths=[x * 0.06], patch_artist=True,
                   whis=(0, 100), showfliers=False, manage_ticks=False, zorder=3,
                   medianprops=dict(lw=0),   # whiskers span full min..max (no hidden fliers); median line off
                   whiskerprops=dict(color=color, lw=0.6), capprops=dict(color=color, lw=0.6),
                   boxprops=dict(facecolor=color, edgecolor=_edge(color), alpha=0.6, lw=0.6))
    else:
        ax.scatter(rs, ts, s=s, color=color, marker=marker, zorder=4,
                   edgecolors=_edge(color), linewidths=0.3, alpha=0.95)


def panel(ax, origin, title, de, gb):
    cols = [t for t in COLS if t[3] == origin]
    for fn, col, did, _ in cols:
        for bits in (12, 16):
            range_bar(ax, *fp_cfg(fn, col, bits), CFG["FastPair-%d" % bits])
        d = de.get((did, col))
        if d:
            for name, eng in d["codecs"].items():
                lbl = DE_NAME.get(name, "DE %s" % name)
                if lbl in CFG and eng.get("ratio") and eng.get("decode_gib_s"):
                    range_bar(ax, [eng["ratio"]], [eng["decode_gib_s"] * C.GIB_TO_GB], CFG[lbl],
                              marker=MARKER.get(lbl, "o"), s=26)
        for lvl in ("-10", "1", "3"):
            range_bar(ax, *zstd_cfg(fn, col, lvl), CFG["Zstd (%s)" % lvl])
        # nvCOMP speed-first software codecs (B300 single points, like the DE)
        cod = gb.get((did, col))
        if cod:
            for name in ("gANS", "Bitcomp-default", "Bitcomp-sparse"):
                e = cod.get(name) or {}
                if e.get("ratio") and e.get("decode_gib_s"):
                    range_bar(ax, [e["ratio"]], [e["decode_gib_s"] * C.GIB_TO_GB], CFG[name],
                              marker=MARKER.get(name, "o"), s=26)
    if origin == "S":
        ax.scatter([2.74], [C.GSST_GBS], s=80, marker="*", color=C.GSST_RED, zorder=5)
    from matplotlib.ticker import FixedLocator, ScalarFormatter, NullFormatter
    ax.set_xscale("log")
    xticks = [1.5, 2, 3, 5, 7, 10, 20] if origin == "S" else [1.5, 2, 3, 5, 7]
    ax.xaxis.set_major_locator(FixedLocator(xticks))
    ax.xaxis.set_major_formatter(ScalarFormatter()); ax.xaxis.set_minor_locator(FixedLocator([]))
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.set_xlabel("compression ratio (log)"); ax.set_title(title, fontsize=8)


def main():
    de = {(e["dataset_id"], e["column"]): e
          for e in json.load(open(C.RESULTS / "b300" / "onpair_nvcomp_hw.json"))}
    # Overlay the DE Snappy codec from the all-codec campaign run (b300-campaign-0717, same B300
    # class, reproduces the canonical b300 Deflate/LZ4). Canonical b300 has no Snappy; this ADDS
    # Snappy points without touching the existing Deflate/LZ4 points. Snappy edges LZ4 only on the
    # long-text columns (~5%); on every throughput-bound headline column Deflate-hi still leads.
    try:
        snap = {(e["dataset_id"], e["column"]): e
                for e in json.load(open(C.RESULTS / "b300-campaign-0717" / "onpair_nvcomp_hw.json"))}
        for k, e in de.items():
            s = snap.get(k, {}).get("codecs", {}).get("Snappy")
            if s and s.get("valid"):
                e["codecs"]["Snappy"] = s
    except FileNotFoundError:
        pass
    gb = {}
    try:
        for line in (C.RESULTS / "b300-campaign-0717" / "gans_bitcomp.jsonl").read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                gb[(r["dataset_id"], r["column"])] = (r.get("sw") or {}).get("codecs", {})
    except FileNotFoundError:
        pass
    plt = C.apply_theme()
    fig, (axR, axS) = plt.subplots(1, 2, figsize=(7.0, 1.9), sharey=True)  # matched height with fig8/fig10
    panel(axR, "R", "Real-world columns", de, gb)
    panel(axS, "S", "Synthetic columns", de, gb)
    # LOG throughput: FastPair (TB/s) and software Zstd (sub-GB/s) span ~4 orders; linear buried
    # the low end. Log keeps every family visible on one axis.
    axR.set_yscale("log")
    axR.set_ylim(0.3, 2500)
    axR.set_ylabel("decode (GB/s, log)")
    from matplotlib.lines import Line2D
    import itertools

    def flip(items, ncol):
        return list(itertools.chain(*[items[i::ncol] for i in range(ncol)]))

    # single-GPU configs show their marker shape; multi-GPU (range) configs show a line swatch
    codec_handles = [
        (Line2D([], [], color=CFG[k], marker=MARKER[k], ls="", ms=6, label=k)
         if k in MARKER else Line2D([], [], color=CFG[k], lw=5, label=k))
        for k in CFG
    ]
    gsst = Line2D([], [], marker="*", color=C.GSST_RED, ls="", ms=9, label="GSST")
    # Place GSST (a GPU decoder) right after the DE marks so row 1 groups the fast
    # decoders (FastPair + DE + GSST) and Zstd(-10) falls to row 2 with the software field.
    leg = codec_handles[:6] + [gsst] + codec_handles[6:]
    # Span the full figure width: a 4-tuple bbox (x0, y0, w, h) with mode="expand"
    # stretches the legend columns edge to edge rather than clustering them centered.
    # Short handles (handlelength) keep each entry narrow so all 13 fit in 2 rows (ncol=7).
    fig.legend(handles=flip(leg, 7), frameon=False, fontsize=6.3, ncol=7, loc="lower center",
               bbox_to_anchor=(0.0, -0.04, 1.0, 0.12), mode="expand",
               columnspacing=1.0, handlelength=1.0, handletextpad=0.7, borderaxespad=0.0)
    fig.tight_layout(rect=(0, 0.12, 1, 1))
    C.save(fig, "fig_sota")


if __name__ == "__main__":
    main()
