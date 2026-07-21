# /// script
# requires-python = ">=3.9"
# dependencies = ["matplotlib", "numpy"]
# ///
"""Fig. teaser: the page-1 hook. Raw B300 decode throughput, FastPair vs the
fixed-function hardware Decompression Engine vs software nvCOMP-Zstd, on three
representative columns spanning the cardinality range. One-column figure with the
raw GiB/s printed on each bar.
Source: results/b300/onpair_summary_*.json + results/b300/onpair_nvcomp_hw.json.
"""
import numpy as np
import common as C

COLS = [
    ("clickbench", "URL", "ClickBench\nURL"),
    ("tpch-sf10", "l_comment", "TPC-H\nl_comment"),
    ("wikipedia", "text", "Wikipedia"),
]
# Own both presets on the page-1 hook: dict-16 is the balanced (higher-ratio)
# configuration, dict-12 the speed-optimized one. On ClickBench URL the two
# collapse (dict-16 is both smaller and faster); on text they separate.
FP16 = C.PRIMARY        # balanced, the protagonist
FP12 = "#92c5de"        # speed-optimized, a lighter tint of the same blue
SERIES = [("FastPair-16", FP16),
          ("FastPair-12", FP12),
          ("hardware DE", C.TECH["de"]),
          ("software Zstd", C.TECH["software"])]


def main():
    de = C.de_map()
    plt = C.apply_theme()
    fig, ax = plt.subplots(figsize=(3.3, 2.05))
    x = np.arange(len(COLS))
    w = 0.2
    vals = [[], [], [], []]
    for d, c, _ in COLS:
        cl = C.cell("b300", d, c)
        ds_id = (cl or {}).get("dataset_id", d)
        fp16 = C.best_shipped(C.cell("b300", d, c, 16)) or 0
        fp12 = C.best_shipped(C.cell("b300", d, c, 12)) or 0
        sw = max((C.software_best(C.cell("b300", d, c, b)) or 0) for b in (12, 16))
        vals[0].append(fp16 or np.nan)
        vals[1].append(fp12 or np.nan)
        vals[2].append(de.get((ds_id, c)) or np.nan)
        vals[3].append(sw or np.nan)
    for j, (lab, color) in enumerate(SERIES):
        xs = x + (j - 1.5) * w
        ax.bar(xs, vals[j], w, label=lab, color=color, zorder=3)
        for xi, v in zip(xs, vals[j]):
            ax.text(xi, v + 18, ("%.0f" % v), ha="center", va="bottom",
                    fontsize=4.8, color=C.INK, rotation=45)
    ax.set_ylim(0, 1550)
    ax.set_yticks([0, 250, 500, 750, 1000, 1250, 1500])
    ax.tick_params(axis="y", labelsize=6)
    ax.set_ylabel("decode (GB/s)", fontsize=7)
    ax.set_xticks(x)
    ax.set_xticklabels([lbl for _, _, lbl in COLS], fontsize=6.5)
    ax.legend(frameon=False, fontsize=5.6, loc="upper center", ncol=2,
              bbox_to_anchor=(0.5, 1.26), handlelength=0.9, columnspacing=0.9,
              handletextpad=0.4)
    ax.grid(axis="y", color="#e6e6e6", lw=0.6, zorder=0)
    ax.set_axisbelow(True)
    fig.tight_layout()
    C.save(fig, "fig_teaser")


if __name__ == "__main__":
    main()
