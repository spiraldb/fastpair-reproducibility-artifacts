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
low number everywhere and explain nothing. This shows a unit at 85-96% of its own peak, decomposed
into named work the design controls: the dictionary gather (global read) and the staged emit
(shared write) in roughly equal parts, with the drain-out and the scratch readback small. DRAM sits
far below peak on the same cells. The claim is therefore about which work is scarce, not about a
bandwidth we did not reach.

THE EMIT, NOT THE GATHER, IS THE LARGEST SINGLE CONSUMER at OnPair-12: about 40-44% of the pipe
against the gather's 35-37%. That is worth stating plainly because it explains the staged-dictionary
result -- shared traffic is already the pipe's biggest user, so moving the dictionary into shared
memory adds to the most contended path rather than relieving it. At OnPair-16 the gather rises to
44-46% and the pipe reaches 92-96%, which is the residency effect in this instrument.

THE L40S IS THE CONTROL. Its L1 reaches only 66% while DRAM runs at 50%, so nothing saturates on
the SM side and the byte term is what binds. Same boundary the length relation and the SM-clock
sweep find.

Source: results/ncu-costsurface-v2.csv (shipped-kernel locked recapture). Column choice is
COLUMN below; the capture covers seven columns of the pre-2026-08 corpus, so Loghub Windows and
the RTX PRO are not available here and would need a fresh capture.
"""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

CSV = Path(__file__).resolve().parent.parent / "results" / "ncu-costsurface-v2.csv"
COLUMN = "clickbench_URL"   # the paper's headline column, and the highest-cardinality real one here
BITS = "12"
ORDER = ["a100", "l40s", "h100", "b300", "rtxpro"]
LABEL = {"a100": "A100", "l40s": "L40S", "h100": "H100", "b300": "B300", "rtxpro": "RTX PRO"}
# L1 stack, bottom to top, with the two global directions dark and the two shared ones light so a
# reader can separate "dictionary and output" from "staging" at a glance.
STACK = [("l1_gld", "#08519c", "dictionary gather (global read)"),
         ("l1_gst", "#6baed6", "drain out (global write)"),
         ("l1_shld", "#fdae61", "readback (shared read)"),
         ("l1_shst", "#f16913", "staged emit (shared write)")]


def main():
    if not CSV.exists():
        sys.exit("missing %s" % CSV)
    rows = {r["arch"]: r for r in csv.DictReader(open(CSV))
            if r["col"] == COLUMN and r["bits"] == BITS}
    present = [c for c in ORDER if c in rows]
    missing = [c for c in ORDER if c not in rows]
    if missing:
        sys.stderr.write("fig_pipes: no capture for %s on %s\n" % (COLUMN, ", ".join(missing)))
    if len(present) < 2:
        sys.exit("fig_pipes: need two devices, have %d" % len(present))

    import numpy as np
    plt = C.apply_theme()
    fig, ax = plt.subplots(figsize=(3.4, 2.1))
    x = np.arange(len(present))
    w = 0.26

    # The l1_* fields are SHARES OF THE L1 PIPE'S TRAFFIC and sum to 100, not points of peak.
    # Scale each by that device's l1tex utilisation so the stack totals the pipe's % of peak and
    # is therefore comparable with the L2 and device-memory bars beside it.
    bottom = np.zeros(len(present))
    for key, colour, lab in STACK:
        v = np.array([float(rows[c][key]) * float(rows[c]["l1tex"]) / 100.0 for c in present])
        ax.bar(x - w * 0.62, v, w, bottom=bottom, color=colour, edgecolor="none", label=lab)
        bottom += v
    for i, c in enumerate(present):
        ax.text(i - w * 0.62, bottom[i] + 1.5, "%.0f" % bottom[i],
                ha="center", va="bottom", fontsize=5.6)
    ax.bar(x + w * 0.62, [float(rows[c]["l2"]) for c in present], w,
           color="#bdbdbd", edgecolor="none", label="L2")
    ax.bar(x + w * 1.68, [float(rows[c]["dram"]) for c in present], w,
           color="#636363", edgecolor="none", label="device memory")

    ax.set_xticks(x + w * 0.5)
    ax.set_xticklabels([LABEL.get(c, c) for c in present], fontsize=7)
    ax.tick_params(axis="x", length=0, pad=1)
    ax.set_ylabel("throughput (% of that unit's peak)")
    ax.set_ylim(0, 100)
    fig.tight_layout(pad=0.25, rect=(0, 0.20, 1, 1))
    ax.legend(fontsize=5.6, ncol=2, loc="upper center", bbox_to_anchor=(0.5, -0.16),
              frameon=False, columnspacing=0.9, handlelength=1.0, handletextpad=0.35)
    C.save(fig, "fig_pipes")

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
