# /// script
# requires-python = ">=3.9"
# dependencies = ["matplotlib", "numpy"]
# ///
"""Fig. gatherwidth: the gather-width lever (split8read / split4read) vs stride-16.

At the dict-12 preset, the best decode rate of the split8read and split4read kernel
families divided by the best stride-16 (full-width) family, plotted against the
fraction of tokens <= 8 bytes. split8read crosses above the stride-16 baseline only
once short tokens dominate (~0.8), reaching 1.25x on the natural-text columns; the
narrower split4read overshoots and sits below the baseline throughout.

We restrict to dict-12: at dict-16 the half-width table doubles and the residency
benefit evaporates, so the gain is a property of that preset and pooling the two
presets is what muddied the trend. Real columns are filled, synthetic open.
Source: results/b300/onpair_summary_*.json (per-kernel gpu.kernels[]).
"""
import numpy as np
import common as C

S16 = {
    "onpair_shmem_4tpt", "onpair_shmem_4tpt_b128", "onpair_shmem_4tpt_b128o12",
    "onpair_shmem_4tpt_b64", "onpair_shmem_4tpt_b64o24", "onpair_shmem_4tpt_b512o3",
    "onpair_shmem_4tpt_o6",
}
# (file label, column, origin) -- file label differs from dataset_id for lship.
COLS = [
    ("lship", "l_shipinstruct", "synth"), ("synthetic", "url", "synth"),
    ("tpch-sf10", "l_comment", "synth"), ("tpch-sf10", "ps_comment", "synth"),
    ("clickbench", "URL", "real"), ("fineweb", "text", "real"),
    ("wikipedia", "text", "real"), ("book-reviews", "text", "real"),
]


def best_family(kmap, pred):
    vals = [v for k, v in kmap.items() if v and pred(k)]
    return max(vals) if vals else None


def main():
    plt = C.apply_theme()
    fig, ax = plt.subplots(figsize=(3.4, 2.3))
    pts = {"s8": {"real": ([], []), "synth": ([], [])},
           "s4": {"real": ([], []), "synth": ([], [])}}
    for ds, col, origin in COLS:
        c = C.cell("b300", ds, col, 12)
        if not c:
            continue
        km = C.kernel_map(c)
        frac = (c.get("gpu") or {}).get("frac_le8")
        s16 = best_family(km, lambda k: k in S16)
        if frac is None or not s16:
            continue
        s8 = best_family(km, lambda k: "split8read" in k)
        s4 = best_family(km, lambda k: "split4read" in k)
        if s8:
            pts["s8"][origin][0].append(frac); pts["s8"][origin][1].append(s8 / s16)
        if s4:
            pts["s4"][origin][0].append(frac); pts["s4"][origin][1].append(s4 / s16)

    ax.axhline(1.0, color=C.INK, lw=0.7, ls="--", zorder=1)
    ax.text(0.02, 1.008, "stride-16 baseline", transform=ax.get_yaxis_transform(),
            fontsize=6, color=C.INK, va="bottom")
    style = {"real": dict(facecolors="full"), "synth": dict(facecolors="none")}
    # split8read (blue circles), split4read (orange triangles); filled=real, open=synthetic
    for origin, fc in (("real", None), ("synth", "none")):
        xs, ys = pts["s8"][origin]
        ax.scatter(xs, ys, s=30, marker="o", zorder=3,
                   facecolors=(C.PRIMARY if fc is None else "none"), edgecolors=C.PRIMARY,
                   linewidths=1.1)
        xs, ys = pts["s4"][origin]
        ax.scatter(xs, ys, s=30, marker="^", zorder=3,
                   facecolors=(C.WARM if fc is None else "none"), edgecolors=C.WARM,
                   linewidths=1.1)
    # legend: kernel by color/marker, origin by fill
    from matplotlib.lines import Line2D
    leg = [
        Line2D([], [], marker="o", color=C.PRIMARY, ls="", label="split8read"),
        Line2D([], [], marker="^", color=C.WARM, ls="", label="split4read"),
        Line2D([], [], marker="o", color=C.INK, ls="", markerfacecolor=C.INK, label="real"),
        Line2D([], [], marker="o", color=C.INK, ls="", markerfacecolor="none", label="synthetic"),
    ]
    ax.legend(handles=leg, frameon=False, fontsize=6.5, loc="upper left", ncol=2,
              handletextpad=0.2, columnspacing=0.8)
    ax.set_xlabel(r"fraction of tokens $\leq$ 8 bytes (dict-12)")
    ax.set_ylabel("decode rate / stride-16")
    fig.tight_layout()
    C.save(fig, "fig_gatherwidth")


if __name__ == "__main__":
    main()
