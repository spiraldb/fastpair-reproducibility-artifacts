# /// script
# requires-python = ">=3.9"
# dependencies = ["matplotlib", "numpy"]
# ///
"""Fig. tokendist: the rank-frequency curve of every column's dictionary reads.

WHY A DISTRIBUTION AND NOT A STATISTIC. An earlier version of this material summarised each
column to one number, the entropy of its code-reference distribution over the maximum. That
number does not separate the groups: at OnPair-12 the generated columns span 0.79 to 1.00 and the
real ones 0.55 to 0.93, and Loghub Windows, a real column, reads lower than either of the two
generated columns the codec inverts. A summary that overlaps cannot carry the claim, so this
draws the shape it was computed from and lets the reader see whether the groups differ.

WHAT ONE PANEL IS. Every distinct code the column uses, sorted by how often it is referenced,
descending, on a log frequency axis. A uniform distribution is a flat line; a Zipfian one falls
away. Panels are independent: each autoscales to its own column, because the columns differ by
four orders of magnitude in both code count and reference count, and a shared axis would flatten
every panel but the largest into a line.

NO SHARED SCALE MEANS NO CROSS-PANEL MAGNITUDE CLAIM. The comparison this figure supports is of
SHAPE. A reader cannot read "more references" off it, and nothing in the paper asks them to.

Source: results/token-freqdist-corpus/<column>.op12.txt, one count per line, sorted descending,
emitted by encodings/onpair-sys/examples/onpair_skew.rs under FREQ_OUT. OnPair-12 only: at twenty
panels this size three overlaid curves are not legible, and the codec changes how far the tail
runs rather than the shape of its head.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

SRC = Path(__file__).resolve().parent.parent / "results" / "token-freqdist-corpus"

# (file stem, display label, group). A leading * on the label means the paper sets that name in
# \texttt, so the panel label is drawn monospace to match; the star is stripped before drawing. Order is the reading order of the grid. The groups do not
# divide evenly into four columns, so they straddle rows; colour carries the grouping instead.
PANELS = [
    ("FineWeb2", "FineWeb2", "real"), ("Wikipedia", "Wikipedia", "real"),
    ("CodeParrot", "CodeParrot", "real"), ("Android", "*Android", "real"),
    ("URL", "*URL", "real"), ("Title", "*Title", "real"),
    ("HDFS", "*HDFS", "real"), ("Thunderbird", "*Thunderbird", "real"),
    ("Spark", "*Spark", "real"), ("Windows", "*Windows", "real"),
    ("hn_by", "*hn_by", "real-short"), ("amz_product_id", "*amz_product_id", "real-short"),
    ("cb_PageCharset", "*PageCharset", "real-short"), ("ghgit_author", "*ghgit_author", "real-short"),
    ("amz_review_id", "*amz_review_id", "real-short"),
    ("c_address", "*c_address", "generated"), ("l_comment", "*l_comment", "generated"),
    ("o_clerk", "*o_clerk", "generated"), ("l_shipinstruct", "*l_shipinstruct", "generated"),
    ("ps_comment", "*ps_comment", "generated"),
]
NCOL, NROW = 4, 5


def counts(stem):
    f = SRC / ("%s.op12.txt" % stem)
    if not f.exists():
        return None
    return [int(x) for x in f.read_text().split()]


def main():
    plt = C.apply_theme()
    fig, axes = plt.subplots(NROW, NCOL, figsize=(7.0, 4.6))
    missing = []
    for ax, (stem, label, group) in zip(axes.ravel(), PANELS):
        v = counts(stem)
        if not v:
            missing.append(stem)
            ax.set_axis_off()
            continue
        colour = C.colour("corpus", group)
        # NORMALISED BY THE PANEL'S OWN MAXIMUM, on a fixed decade range. Autoscaling each panel
        # to its own counts inverts the figure's meaning on exactly the column it exists to
        # show: l_shipinstruct's five codes are referenced 20.84 million times each, differing by
        # 0.06%, and a log axis fitted to that span magnifies the difference into a full-height
        # staircase -- the one perfectly uniform column drawn as the most skewed one. Dividing by
        # the maximum puts a uniform column flat along the top and lets a Zipfian one fall away,
        # which is the comparison, and a fixed range keeps that reading the same in every panel.
        top = v[0]
        ax.bar(range(len(v)), [c / top for c in v], width=0.85, linewidth=0, color=colour)
        ax.set_yscale("log")
        ax.set_ylim(1e-6, 2.0)
        ax.set_xlim(-0.5, len(v) - 0.5)
        # No ticks, no numbers, no grid: twenty panels of shape, identified by name alone.
        # Minor ticks have to go explicitly -- a log axis re-adds them after set_yticks([]),
        # which is what leaked a column of numbers into the l_shipinstruct panel.
        ax.set_xticks([])
        ax.set_yticks([])
        ax.tick_params(which="both", left=False, right=False, top=False, bottom=False,
                       labelleft=False, labelbottom=False)
        ax.yaxis.set_minor_locator(plt.NullLocator())
        ax.grid(False)
        for side in ("top", "right", "left", "bottom"):
            ax.spines[side].set_visible(True)
            ax.spines[side].set_linewidth(0.4)
            ax.spines[side].set_color("#bbbbbb")
        mono = label.startswith("*")
        ax.set_xlabel(label.lstrip("*"), fontsize=C.FS["tick"], labelpad=2,
                      fontfamily="monospace" if mono else None)
    for ax in axes.ravel()[len(PANELS):]:
        ax.set_axis_off()
    if missing:
        sys.stderr.write("fig_tokendist: no dump for %s\n" % ", ".join(missing))
    fig.tight_layout(pad=0.3, h_pad=0.9, w_pad=0.7)
    C.save(fig, "fig_tokendist", width="text")

    for stem, label, group in PANELS:
        label = label.lstrip("*")
        v = counts(stem)
        if v:
            top = v[0] / sum(v)
            sys.stderr.write("%-16s %-11s codes %6d  top-1 %5.1f%%  top-10 %5.1f%%\n"
                             % (label, group, len(v), 100 * top,
                                100 * sum(v[:10]) / sum(v)))


if __name__ == "__main__":
    main()
