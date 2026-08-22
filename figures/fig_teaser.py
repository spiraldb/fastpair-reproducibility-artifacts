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

THREE REAL COLUMNS. The previous form put TPC-H l_comment on page one, which is generated data,
and the paper quarantines generated columns everywhere else precisely because they decode faster.
Leading with one undercut that discipline before the reader reached Section 5.

Source: results/suite-<id>/b300/{sweep,fsst12}_summary_*_boost.json and onpair_nvcomp_hw.json.
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402
import suite as S  # noqa: E402

COLS = [
    ("loghub-windows", "line", "Loghub\nWindows"),
    ("clickbench", "URL", "ClickBench\nURL"),
    ("wikipedia", "text", "Wikipedia"),
]

FP16, FP12, FSST = C.PRIMARY, "#92c5de", "#c994c7"
# Zstd at both ends of the level range it was run at: -10 is its fastest setting and
# 3 its highest-ratio one, so the pair brackets what software Zstd offers on this GPU.
SERIES = [("OnPair-16", FP16), ("OnPair-12", FP12), ("FSST-12", FSST),
          ("DE (best)", C.TECH["de"]), ("Zstd (-10)", C.TECH["software"]),
          ("Zstd (3)", "#5b616b")]


# BASIS: production-only (see the "EXPERIMENTAL DOES NOT MEAN IGNORE" block in suite.py).
# The generated grid reaches ~7.5% higher on some columns and is excluded here only
# because this figure reports what the shipped selector can choose. If a baseline on
# this plot is quoted at ITS best configuration, revisit that choice.
def zstd_at(cell, level):
    """Best nvCOMP-Zstd decode GB/s at one compression level for a cell, or None."""
    best = None
    for e in ((cell or {}).get("gpu") or {}).get("nvcomp_zstd") or []:
        if not isinstance(e, dict) or e.get("zstd_level") != level:
            continue
        v = (e.get("decode_gib_s") or 0) * C.GIB_TO_GB
        if v and (best is None or v > best):
            best = v
    return best


def main():
    root = S.latest_root()
    if root is None:
        sys.exit("no results/suite-* directory found")
    op = S.cells(root, "b300", "boost", "onpair")
    fs = S.cells(root, "b300", "boost", "fsst12")
    zs = S.cells(root, "b300", "boost", "zstd")
    de = {(r.get("dataset_id"), r.get("column")): r.get("best_decode_gib_s", 0) * C.GIB_TO_GB
          for r in S.de_rows(root, "b300")}
    plt = C.apply_theme()
    fig, ax = plt.subplots(figsize=(3.3, 2.15))
    x = np.arange(len(COLS))
    w = 0.14
    vals = [[] for _ in SERIES]
    for d, c, _ in COLS:
        vals[0].append(S.rate_gb_s(op.get((d, c, 16))) or np.nan)
        vals[1].append(S.rate_gb_s(op.get((d, c, 12))) or np.nan)
        vals[2].append(S.rate_gb_s(fs.get((d, c, 12))) or np.nan)
        vals[3].append(de.get((d, c)) or np.nan)
        vals[4].append(zstd_at(zs.get((d, c, 12)), -10) or np.nan)
        vals[5].append(zstd_at(zs.get((d, c, 12)), 3) or np.nan)

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
