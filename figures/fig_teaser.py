# /// script
# requires-python = ">=3.9"
# dependencies = ["matplotlib", "numpy"]
# ///
"""Fig. teaser: the page-1 hook. B300 decode throughput for the three techniques the
paper decodes (OnPair-16, OnPair-12, FSST-12) against the alternatives a reader would
otherwise reach for: the fixed-function Decompression Engine at its best codec, and
software nvCOMP-Zstd at both ends of its level range.

Linear y-axis. The Zstd bars on Wikipedia (1-2 GB/s) are therefore near-invisible
against OnPair's ~870; their printed values carry the number.

Sources: results/b300/onpair_summary_*.json (OnPair, nvCOMP-Zstd),
results/b300-fsst12/fsst12_summary_*.json (FSST-12),
results/b300/onpair_nvcomp_hw.json (engine, via common.de_map()).
"""
import numpy as np
import common as C

COLS = [
    ("clickbench", "URL", "ClickBench\nURL"),
    ("tpch-sf10", "l_comment", "TPC-H\nl_comment"),
    ("wikipedia", "text", "Wikipedia"),
]

FP16, FP12, FSST = C.PRIMARY, "#92c5de", "#c994c7"
# Zstd at both ends of the level range it was run at: -10 is its fastest setting and
# 3 its highest-ratio one, so the pair brackets what software Zstd offers on this GPU.
SERIES = [("OnPair-16", FP16), ("OnPair-12", FP12), ("FSST-12", FSST),
          ("DE (best)", C.TECH["de"]), ("Zstd (-10)", C.TECH["software"]),
          ("Zstd (3)", "#5b616b")]


def zstd_at(cell, level):
    """Best nvCOMP-Zstd decode GB/s at one compression level for a cell, or None."""
    best = None
    for e in ((cell or {}).get("gpu") or {}).get("nvcomp_zstd") or []:
        if not isinstance(e, dict) or e.get("zstd_level") != level:
            continue
        v = C.zstd_gb_s(e)
        if v and (best is None or v > best):
            best = v
    return best


def main():
    de = C.de_map()
    plt = C.apply_theme()
    fig, ax = plt.subplots(figsize=(3.3, 2.15))
    x = np.arange(len(COLS))
    w = 0.14
    vals = [[] for _ in SERIES]
    for d, c, _ in COLS:
        cl = C.cell("b300", d, c)
        ds_id = (cl or {}).get("dataset_id", d)
        vals[0].append(C.best_shipped(C.cell("b300", d, c, 16)) or np.nan)
        vals[1].append(C.best_shipped(C.cell("b300", d, c, 12)) or np.nan)
        vals[2].append(C.best_shipped(C.cell("b300", d, c, 12, codec=C.FSST12)) or np.nan)
        vals[3].append(de.get((ds_id, c)) or np.nan)
        vals[4].append(max((zstd_at(C.cell("b300", d, c, b), -10) or 0) for b in (12, 16)) or np.nan)
        vals[5].append(max((zstd_at(C.cell("b300", d, c, b), 3) or 0) for b in (12, 16)) or np.nan)

    for j, (lab, color) in enumerate(SERIES):
        xs = x + (j - (len(SERIES) - 1) / 2.0) * w
        ax.bar(xs, vals[j], w, label=lab, color=color, zorder=3)
        for xi, v in zip(xs, vals[j]):
            if not np.isnan(v):
                ax.text(xi, v + 25, ("%.0f" % v) if v >= 10 else ("%.1f" % v),
                        ha="center", va="bottom", fontsize=4.0, color=C.INK, rotation=90)

    ax.set_ylim(0, 1500)
    ax.set_yticks([0, 250, 500, 750, 1000, 1250, 1500])
    ax.tick_params(axis="y", labelsize=6)
    ax.set_ylabel("decode (GB/s)", fontsize=7)
    ax.set_xticks(x)
    ax.set_xticklabels([lbl for _, _, lbl in COLS], fontsize=6.5)
    ax.set_xlim(-0.55, len(COLS) - 0.45)
    ax.legend(frameon=False, fontsize=5.2, loc="upper center", ncol=3,
              bbox_to_anchor=(0.5, 1.30), handlelength=0.9, columnspacing=0.7,
              handletextpad=0.35)
    ax.grid(axis="y", color="#e6e6e6", lw=0.6, zorder=0)
    ax.set_axisbelow(True)
    fig.tight_layout()
    C.save(fig, "fig_teaser")

    for j, (lab, _) in enumerate(SERIES):
        print(f"{lab:16s} " + "  ".join(f"{v:8.1f}" for v in vals[j]))


if __name__ == "__main__":
    main()
