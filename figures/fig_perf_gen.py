# /// script
# requires-python = ">=3.9"
# dependencies = ["matplotlib"]
# ///
"""Fig. perf_gen: decode rate per column across devices AND across SM clock.

The companion to fig_perf_real, which fixes the device and varies the codec. This varies the
device and the clock, and shows one kernel family covering the whole matrix.

LAYOUT. One slot per column. Inside a slot, one short VERTICAL LINE per GPU, packed side by side.
Each line carries that GPU's decode rate at every clock state it was measured at, so the line's
extent IS the clock sensitivity of that chip on that column. A horizontal BAR across the slot is
the B300 Decompression Engine's best configuration on that column.

DRAWN AT ITS PRINTED SIZE. This is a two-column float landing at about seven inches, so figsize
matches that. An earlier version was drawn ten inches wide and scaled down on the page, which
shrank every label by a third and made the figure unreadable in print.

ENCODING. Colour is the GPU, grouped by MEMORY TECHNOLOGY: the three HBM parts take a blue ramp
and the GDDR6 L40S green. That is the axis that separates these chips for this kernel, and it also
keeps every chip clear of the orange the DE bar uses. Marker shape is the CLOCK STATE, and it is
assigned by nominal state (boost, max, 75%, 55%, 40%) rather than by absolute MHz, because the
same nominal state lands on different frequencies per part -- 1905 MHz on the B300 is 'max', so is
1830 on the H100 and 2520 on the L40S. Shape therefore means the same experimental condition on
every chip, which is what the reader needs to compare.

WHY THE CLOCK ARM IS HERE AND NOT ITS OWN FIGURE. It is the falsification, not a curiosity: with
the memory clock pinned, decode rate that scales with the SM clock rules out DRAM bandwidth, DRAM
latency, and an L2 request-rate bound, because l1tex runs at the SM clock while L2 and DRAM are
separate domains. It does NOT separate L1 request rate from compute, issue, register file or
shared memory, and this figure does not claim it does.

BEST AGAINST BEST. The DE bar is its best codec AND chunk size for that column; our marks are the
best kernel. Both sides tuned, neither handicapped. Earlier drafts drew all twenty engine
configurations, which put a cloud of operating points nobody would ship behind every slot.

MISSING CHIPS KEEP THEIR SLOT AND THEIR LEGEND ENTRY. A leg that has not landed leaves a labelled
gap, so a reader sees three chips and a hole rather than assuming three was the design.

Source: results/suite-<id>/<chip>/sweep_summary_*_{boost,sm*}.json + b300/onpair_nvcomp_hw.json.
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

OUT = Path(__file__).resolve().parent / "out" / "fig_perf_gen.pdf"

# HBM parts take the blue ramp, the GDDR6 part green. Memory technology is the axis that
# actually separates these chips for this kernel, and keeping the non-HBM part out of the blues
# also keeps every chip clear of the orange the DE bars use.
CHIP_COLOR = {"b300": "#08519c", "h100": "#4292c6", "a100": "#9ecae1", "l40s": "#41ab5d"}
CHIP_MEM = {"b300": "HBM", "h100": "HBM", "a100": "HBM", "l40s": "GDDR6"}
CHIP_LABEL = {"b300": "B300", "h100": "H100", "a100": "A100", "l40s": "L40S"}
# Nominal clock state -> marker. Ordered as the campaign requests them.
STATE_MARK = [("boost", "*"), ("max", "o"), ("75%", "s"), ("55%", "^"), ("40%", "D")]
DE_COLOR = "#b0413e"
BITS = 12          # one preset; adding OnPair-16 would triple the marks per slot


def nominal_states(root, chip):
    """Map this chip's tags to nominal states. Pinned tags ascend 40% < 55% < 75% < max."""
    tags = S.clock_tags(root, chip)
    pinned = [t for t in tags if t != "boost"]
    names = ["40%", "55%", "75%", "max"][-len(pinned):] if pinned else []
    out = {t: n for t, n in zip(pinned, names)}
    if "boost" in tags:
        out["boost"] = "boost"
    return out


def best_rate(c):
    """Best kernel on this cell, GB/s -- the same basis the DE bar uses."""
    if not c:
        return None
    g = c.get("gpu") or {}
    best = g.get("best_kernel")
    for k in (g.get("kernels") or []):
        if k.get("kernel") == best and k.get("decode_ns_iters") and g.get("decoded_bytes"):
            return g["decoded_bytes"] / min(k["decode_ns_iters"])
    return ((g.get("best_decode_gib_s") or 0) * 1.073741824) or None


def de_best(root, ds, col, chip="b300"):
    """The engine's best for a column: best codec AND best chunk size, one bar.

    Best against best. Both sides are tuned, so neither is handicapped; drawing all twenty engine
    configurations instead put a cloud of operating points nobody would ship behind every slot."""
    for r in S.de_rows(root, chip):
        if r.get("dataset_id") == ds and r.get("column") == col and r.get("best_decode_gib_s"):
            return r["best_decode_gib_s"] * 1.073741824
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--suite-id", default=None)
    a = ap.parse_args()
    root = S.latest_root(a.suite_id)
    if root is None:
        sys.exit("no results/suite-* directory found")

    rows = [(lab, ds, col, "real") for lab, ds, col in S.REAL] + \
           [(lab, ds, col, "gen") for lab, ds, col in S.GEN]
    states = {c: nominal_states(root, c) for c in S.CHIPS}
    data = {c: {t: S.cells(root, c, t, "onpair") for t in S.clock_tags(root, c)} for c in S.CHIPS}

    # SIZED TO ITS RENDERED WIDTH. This is a two-column float, so it lands at about 7 inches. A
    # 10-inch figsize is scaled down by a third on the page and takes every font with it, which
    # is why the previous version could not be read at print size. Draw it the size it is shown.
    fig, ax = plt.subplots(figsize=(7.1, 4.6))
    slot = 1.0
    per_chip = (slot * 0.72) / len(S.CHIPS)
    absent, drawn = [], 0

    for i, (lab, ds, col, grp) in enumerate(rows):
        x0 = i * slot
        # ONE BAR: the engine's best configuration on this column.
        v = de_best(root, ds, col)
        if v is not None:
            ax.hlines(v, x0 - slot * 0.44, x0 + slot * 0.44, color=DE_COLOR, lw=1.6,
                      alpha=.95, zorder=2)

        for j, chip in enumerate(S.CHIPS):
            xc = x0 - slot * 0.39 + per_chip * (j + 0.5)
            tags = states.get(chip) or {}
            pts = []
            for tag, nominal in tags.items():
                c = data[chip].get(tag, {}).get((ds, col, BITS))
                v = best_rate(c)
                if v is not None:
                    pts.append((nominal, v))
            if not pts:
                absent.append(f"{chip}/{ds}/{col}")
                continue
            ys = [v for _, v in pts]
            ax.vlines(xc, min(ys), max(ys), color=CHIP_COLOR[chip], lw=1.2, alpha=.85, zorder=3)
            for nominal, v in pts:
                mk = dict(STATE_MARK).get(nominal, ".")
                ax.plot([xc], [v], marker=mk, ms=4.2 if mk != "*" else 6.0,
                        color=CHIP_COLOR[chip], mec="white", mew=.4, zorder=4, ls="")
                drawn += 1

    ax.set_xticks([i * slot for i in range(len(rows))])
    SHORT = {"FineWeb2 Mandarin": "FineWeb2", "Loghub \\texttt{Android}": "Android",
             "ClickBench \\texttt{URL}": "URL", "ClickBench \\texttt{Title}": "Title",
             "Loghub \\texttt{HDFS}": "HDFS", "Loghub \\texttt{Thunderbird}": "Thunderbird",
             "Loghub \\texttt{Spark}": "Spark", "Loghub \\texttt{Windows}": "Windows",
             "TPC-H \\texttt{c\\_address}": "c_address",
             "TPC-H \\texttt{l\\_comment}": "l_comment",
             "TPC-H \\texttt{o\\_clerk}": "o_clerk",
             "TPC-H \\texttt{l\\_shipinstruct}": "l_shipinstruct",
             "TPC-H \\texttt{ps\\_comment}": "ps_comment"}
    ax.set_xticklabels([SHORT.get(lab, lab) for lab, _, _, _ in rows],
                       rotation=40, ha="right", fontsize=7)
    # The rule between real and generated columns: they are never pooled into one claim.
    ax.axvline(len(S.REAL) * slot - slot * 0.5, color="#444444", lw=.9, ls=":")
    ax.text(len(S.REAL) * slot - slot * 0.45, ax.get_ylim()[1], " generated",
            fontsize=7, va="top", color="#444444")
    ax.set_ylabel("decode throughput (GB/s)")
    ax.grid(axis="y", alpha=.25, lw=.5)
    ax.set_axisbelow(True)

    chips = [Line2D([], [], color=CHIP_COLOR[c], lw=2,
                    label=f"{CHIP_LABEL[c]} ({CHIP_MEM[c]})"
                          + ("" if S.clock_tags(root, c) else " — not measured"))
             for c in S.CHIPS]
    marks = [Line2D([], [], color="#444444", marker=m, ls="", label=n) for n, m in STATE_MARK]
    de = [Line2D([], [], color=DE_COLOR, lw=1.6, label="DE (best codec + chunk)")]
    # ABOVE the axes. The x labels are rotated column names and take the whole lower margin, so a
    # legend placed below lands on top of them.
    leg = fig.legend(handles=chips + marks + de, fontsize=7, ncol=6, loc="lower center",
                     bbox_to_anchor=(0.5, 0.94), frameon=False)
    leg.set_title(f"OnPair-{BITS}, best kernel — marker = SM clock state", prop={"size": 7})

    OUT.parent.mkdir(exist_ok=True)
    fig.savefig(OUT, bbox_inches="tight")
    print(f"wrote {OUT.relative_to(Path(__file__).resolve().parent.parent)}")
    print(f"points drawn: {drawn}")
    if absent:
        print(f"ABSENT series: {len(absent)} (slot and legend entry kept)")
        for c in S.CHIPS:
            n = sum(1 for x in absent if x.startswith(c + "/"))
            if n:
                print(f"  {c}: {n} columns")


if __name__ == "__main__":
    main()
