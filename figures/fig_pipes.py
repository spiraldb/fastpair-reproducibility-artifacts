# /// script
# requires-python = ">=3.9"
# dependencies = ["matplotlib", "numpy"]
# ///
"""Fig. pipes: what fills the binding unit, one column across every device.

WHY THIS SHAPE. fig_costsurface draws the same decomposition across a cardinality gradient,
which answers "how does the mix shift with dictionary size". This fixes the column and varies the
DEVICE, which answers the question the evaluation actually asks: is the same unit binding, and
filled by the same work, on every architecture. One column, chips across, so the reader compares
like with like.

WHY IT IS POSITIVE EVIDENCE. A decoder that merely failed to reach memory bandwidth would show a
low number everywhere and explain nothing. On the three HBM devices this shows a unit SATURATED --
99.0 to 99.4% of its own peak -- decomposed into named work the design controls: the dictionary
gather (global read) and the staged emit (shared write), with the drain-out and the scratch
readback together under ten points. Device memory sits at 11.6 to 43.3% on the same cells. The
claim is therefore about which work is scarce, not about a bandwidth we did not reach.

THE EMIT, NOT THE GATHER, IS THE LARGEST SINGLE CONSUMER: at OnPair-12 about 62 points of the pipe
against the gather's 29 on the HBM parts. That is worth stating plainly because it explains the
staged-dictionary result -- shared traffic is already the pipe's biggest user, so moving the
dictionary into shared memory adds to the most contended path rather than relieving it.

THE GRADIENT IS THE POINT, AND IT IS MONOTONE IN MEMORY TECHNOLOGY. HBM saturates the L1 pipe with
device memory nearly idle (B300: 99.2 against 11.6); GDDR7 loads both (RTX PRO: 80.0 against 78.9);
GDDR6 puts device memory ABOVE the L1 pipe (L40S: 69.6 against 76.4). The B300 and the RTX PRO are
both Blackwell, so that pair moves memory technology with the SM architecture held fixed -- the
separation the L40S cannot provide, because there Ada and GDDR6 both differ from the HBM parts.

BEST VERSUS BEST, as everywhere else in this paper: each device runs the configuration its selector
picks for that column, which is what that device would deploy. The kernels are therefore not
identical across bars, and that is the intended comparison rather than a confound -- pinning one
kernel would profile a configuration no deployment would choose. Note the L40S's optimum sits at
K=2, consistent with fig_lenpredict's finding that coarsening buys less once byte supply binds.

CLOCKS ARE NOT LOCKED, and no capture in this repo's cost-surface family ever was: in
jobs/onpair-bench.sh the COSTSURFACE block runs at lines 267-391 and CLOCK_LOCK only at 513-599,
so the lock reaches the throughput sweep that follows and never the capture. These are
Speed-of-Light %-of-peak metrics from kernels NCU replays under its own serialization, so they do
not carry boost variance the way a timing would. Do not describe them as locked.

Source: results/ncu-costsurface-pipes.csv (2026-08-24, rev dd2325b3f, five devices, Loghub Windows
+ ClickBench URL at OnPair-12/-16). The older results/ncu-costsurface-v2.csv covers seven columns
of the pre-2026-08 corpus on four devices and still backs Section 5.2's corpus-wide ranges; the two
waves are kept in separate files because their shared URL cells would otherwise collide on
(arch, col, bits) and the lookup below would silently keep whichever row came last.
"""
import csv
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

CSV = Path(__file__).resolve().parent.parent / "results" / "ncu-costsurface-pipes.csv"
# Override only to inspect another wave; the committed default is the source of record.
if os.environ.get("COSTSURFACE_CSV"):
    CSV = Path(os.environ["COSTSURFACE_CSV"]).resolve()
# PREFERRED column first, then the fallback. Loghub Windows is the column the paper wants here --
# it is fig:grid's and fig:hoist's column, so the three figures agree on it -- and as of the
# 2026-08-24 capture it exists on all five devices. The fallback stays so that pointing this at an
# older wave degrades to a drawn figure with a stderr note rather than an exit.
COLUMNS = ["loghub-windows_line", "loghub_windows_line", "clickbench_URL"]
BITS = "12"
ORDER = C.DEVICE_ORDER   # paper-wide device order; see common.DEVICE_ORDER
LABEL = {"a100": "A100", "l40s": "L40S", "h100": "H100", "b300": "B300", "rtxpro": "RTX PRO"}
# L1 stack, bottom to top, with the two global directions dark and the two shared ones light so a
# reader can separate "dictionary and output" from "staging" at a glance.
# (csv field, palette member, legend label). Colour and hatch both come from common's
# pipe family, so a stacked bar stays readable in greyscale.
STACK = [("l1_gld", "gather", "dictionary gather (global read)"),
         ("l1_gst", "drain", "drain out (global write)"),
         ("l1_shld", "readback", "readback (shared read)"),
         ("l1_shst", "emit", "staged emit (shared write)")]


def main():
    if not CSV.exists():
        sys.exit("missing %s" % CSV)
    have = list(csv.DictReader(open(CSV)))
    for column in COLUMNS:
        rows = {r["arch"]: r for r in have if r["col"] == column and r["bits"] == BITS}
        if rows:
            break
    else:
        sys.exit("fig_pipes: none of %s present in %s" % (COLUMNS, CSV))
    if column != COLUMNS[0]:
        sys.stderr.write("fig_pipes: drawing %s; %s has no capture yet\n" % (column, COLUMNS[0]))
    present = [c for c in ORDER if c in rows]
    missing = [c for c in ORDER if c not in rows]
    if missing:
        sys.stderr.write("fig_pipes: no capture for %s on %s\n" % (column, ", ".join(missing)))
    if len(present) < 2:
        sys.exit("fig_pipes: need two devices, have %d" % len(present))

    import numpy as np
    plt = C.apply_theme()
    fig, ax = plt.subplots(figsize=(3.4, 2.2))
    x = np.arange(len(present))
    # Four bars per device now, so place them symmetrically about each tick and leave a fifth
    # bar's worth of air between groups: with w = 0.8/4 the group spans 0.8 of the unit spacing.
    w = 0.8 / 4
    off = [(i - 1.5) * w for i in range(4)]

    # The l1_* fields are SHARES OF THE L1 PIPE'S TRAFFIC and sum to 100, not points of peak.
    # Scale each by that device's l1tex utilisation so the stack totals the pipe's % of peak and
    # is therefore comparable with the L2 and device-memory bars beside it.
    bottom = np.zeros(len(present))
    for key, member, lab in STACK:
        colour = C.colour("mempath", member)
        v = np.array([float(rows[c][key]) * float(rows[c]["l1tex"]) / 100.0 for c in present])
        ax.bar(x + off[0], v, w, bottom=bottom, color=colour, edgecolor="white",
               linewidth=0.3, label=lab)
        bottom += v
    for i, c in enumerate(present):
        ax.text(i + off[0], bottom[i] + 1.5, "%.0f" % bottom[i],
                ha="center", va="bottom", fontsize=C.FS["annot"])
    # L2 and device memory continue the SAME progression as the four L1 segments -- they are the
    # next two steps out along the memory path -- but desaturated, so brightness carries the
    # order while hue marks which of them the figure is actually about. SM is not on that path at
    # all, so it is the outlined white bar rather than a seventh step.
    ax.bar(x + off[1], [float(rows[c]["l2"]) for c in present], w,
           color=C.desaturate(C.colour("mempath", "L2")), edgecolor="none", label="L2")
    ax.bar(x + off[2], [float(rows[c]["dram"]) for c in present], w,
           color=C.desaturate(C.colour("mempath", "device memory")),
           # A sparse dark rule over the palest bar in the figure. Device memory is the lightest
           # step of the progression, yet it is the bar carrying the result on the two GDDR parts,
           # where it reaches 76 and 79%. The hatch gives it weight without moving it off the
           # ramp: single density so it reads as texture rather than as a second fill.
           hatch="....", edgecolor=C.INK, linewidth=0.0,
           label="device memory")
    ax.bar(x + off[3], [float(rows[c]["sm"]) for c in present], w,
           color="white", edgecolor=C.INK, linewidth=0.5, hatch="xx", label="SM (compute)")

    ax.set_xticks(x)
    ax.set_xticklabels([LABEL.get(c, c) for c in present])
    ax.tick_params(axis="x", length=0, pad=1)
    ax.set_ylabel("throughput (% of that unit's peak)")
    ax.set_ylim(0, 100)
    fig.tight_layout(pad=0.3)
    # TWO COLUMNS of the full-length labels, four rows deep, at the paper's ordinary legend
    # size. The labels name each segment outright so the caption does not have to, and four per
    # row was what forced them down to 4.6pt -- the smallest type on any page. Four rows cost
    # about a quarter inch of height, which is the right trade for a readable key.
    # THE FIRST COLUMN IS REVERSED, so it reads top to bottom in the order the segments stack
    # bottom to top: the emit is the top of every bar and the top of the key. Handed to the
    # legend explicitly, because the axes hand back artists in the order they were drawn, which
    # is stacking order and therefore upside down here.
    h, lab = ax.get_legend_handles_labels()
    order = [3, 2, 1, 0] + list(range(4, len(h)))
    C.legend_below(fig, handles=[h[i] for i in order], labels=[lab[i] for i in order],
                   ncol=2, columnspacing=1.0,
                   handlelength=1.1, handletextpad=0.3, labelspacing=0.25)
    C.save(fig, "fig_pipes", width="column")

    for c in present:
        r = rows[c]
        t = float(r["l1tex"])
        pts = lambda k: float(r[k]) * t / 100.0
        sys.stderr.write("%-6s L1 %.1f of peak = gather %.1f + emit %.1f + readback %.1f + drain %.1f"
                         "   | shares %.0f/%.0f/%.0f/%.0f   L2 %.1f  DRAM %.1f\n"
                         % (c, t, pts("l1_gld"), pts("l1_shst"), pts("l1_shld"), pts("l1_gst"),
                            float(r["l1_gld"]), float(r["l1_shst"]), float(r["l1_shld"]),
                            float(r["l1_gst"]), float(r["l2"]), float(r["dram"])))


if __name__ == "__main__":
    main()
