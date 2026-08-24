# /// script
# requires-python = ">=3.9"
# dependencies = ["matplotlib", "numpy"]
# ///
"""Fig. lenpredict: decode rate against mean token length, one device, both presets.

WHAT IT IS FOR. Section 4.2 claims that once the low plane is resident, mean token length alone
predicts the decode rate. That claim was carried by four correlation coefficients quoted in the
prose, which is a number a reader has to take on trust. This draws the relation instead, so the
subsection can point at it and stay short.

WHY MEAN TOKEN LENGTH IS THE X AXIS, and not compression ratio. fig_perf_real plots rate against
at-rest ratio because that is the positional claim against the baselines. It is deliberately NOT
the predictor: rate tracks length, not ratio, and a fit against the ratio axis would assert the
opposite. The two figures answer different questions on the same marks.

ONE DEVICE, matching fig_perf_real's discipline. Holding the chip fixed is what makes the fit a
statement about the data rather than a blend of four memory systems. The other three chips'
coefficients go in the caption; the L40S is the interesting one and is reported, not dropped --
see below.

LENGTH IS TOKEN-WEIGHTED, via suite.mean_len (sample_bytes / code count). On this campaign
gpu.dict_mean_len happens to carry the same quantity to four decimals, so the two agree, but
mean_len is the definition tab_datasets and the Len column use and is the one to depend on.

THE L40S IS THE BOUNDARY AND IS NOT HIDDEN. On the three HBM chips the coefficient is +0.95 to
+0.99; on the GDDR6 L40S it falls to +0.84 (OnPair-12) and +0.86 (OnPair-16). That is where the
paper says byte supply becomes the tighter limit, so a weaker length relation there is the
expected reading and belongs in the caption rather than being excluded from the range.

REAL COLUMNS ONLY. The five generated columns are degenerate by construction -- one has four
distinct values, another is random characters -- so including them would let the generator's
choices set the slope. They are excluded here exactly as they are excluded from every aggregate.

Source: results/suite-paper-20260821/<chip>/sweep_summary_*_boost.json.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402
import suite as S  # noqa: E402

# Colours come from tech-ours, the SAME family fig_perf_real and fig_teaser use, so a codec is
# one colour paper-wide. This figure used to draw from the four-member "codec" family instead,
# which put OnPair-16 at #24878e here and #440154 there -- same codec, two colours. FSST-12 is here because it is a THIRD codec the same
# kernels decode: at twelve bits its low plane is the same 32 KiB and is equally resident, so if
# the relation belongs to the decode rather than to OnPair it has to hold for FSST-12 too.
# Colour comes from common's codec family, so this figure changes with the palette rather
# than pinning its own hex. Marker shape carries the same identity for greyscale.
# Ordered as the tech-ours band is, so the legend reads darkest to lightest like the marks do.
PRESETS = [("onpair", 16, "OnPair-16", "o"),
           ("onpair", 12, "OnPair-12", "s"),
           ("fsst12", 12, "FSST-12", "D")]
CHIP = "b300"
REAL = {(ds, col) for _, ds, col in S.REAL}


def series(root, chip, bits, codec="onpair"):
    """[(mean token length, rate GB/s)] over the real columns, or [] if the leg is absent."""
    out = []
    for (ds, col, b), c in S.cells(root, chip, "boost", codec).items():
        if b != bits or (ds, col) not in REAL:
            continue
        rate, ln = S.rate_gb_s(c), S.mean_len(c)
        if rate and ln:
            out.append((ln, rate))
    return sorted(out)


def pearson(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    cx, cy = [x - mx for x in xs], [y - my for y in ys]
    den = (sum(x * x for x in cx) * sum(y * y for y in cy)) ** 0.5
    return sum(x * y for x, y in zip(cx, cy)) / den if den else None


def fit(xs, ys):
    """Least-squares slope and intercept, so the drawn line is the ordinary regression."""
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
    return slope, my - slope * mx


def main():
    root = S.latest_root(S.PAPER_SUITE)
    plt = C.apply_theme()
    fig, ax = plt.subplots(figsize=(3.3, 1.9))

    for codec, bits, label, marker in PRESETS:
        colour = C.colour("tech-ours", label)
        pts = series(root, CHIP, bits, codec)
        if len(pts) < 3:
            sys.stderr.write("fig_lenpredict: %s %s has %d columns, skipped\n"
                             % (CHIP, label, len(pts)))
            continue
        xs, ys = zip(*pts)
        r = pearson(xs, ys)
        slope, icpt = fit(xs, ys)
        lo, hi = min(xs), max(xs)
        ax.plot([lo, hi], [slope * lo + icpt, slope * hi + icpt],
                color=colour, linewidth=C.LW, zorder=1)
        ax.scatter(xs, ys, s=C.MS_SCATTER, color=colour, marker=marker, edgecolor="white",
                   linewidth=0.4, zorder=2,
                   label="%s\n$r=%+.2f$" % (label, r))
        sys.stderr.write("%s %-9s: n=%d r=%+.3f slope=%.1f GB/s per byte, len %.2f-%.2f\n"
                         % (CHIP, label, len(xs), r, slope, lo, hi))

    # Every other chip's coefficient, for the prose. Reported here rather than plotted so the
    # figure stays one column; the L40S is the one that departs and the reason it does is in §4.2.
    for chip in S.CHIPS_CORE:
        if chip == CHIP:
            continue
        for codec, bits, label, _ in PRESETS:
            pts = series(root, chip, bits, codec)
            if len(pts) >= 3:
                xs, ys = zip(*pts)
                sys.stderr.write("  prose: %-5s %-9s r=%+.3f\n"
                                 % (chip, label, pearson(xs, ys)))

    ax.set_xlabel("mean token length (bytes per code)")
    ax.set_ylabel("decode rate (GB/s)")
    # The y axis does not start at zero. What this figure asserts is a relation and the spacing
    # between two of them, not a ratio between rates, and every value is above 750 GB/s; a decade
    # of empty panel below the data would halve the visible slope for nothing. Magnitudes are read
    # off fig_perf_gen, which is zero-based.
    ax.set_ylim(700, 1600)
    fig.tight_layout(pad=0.3)
    # BELOW the axes, matching fig_perf_real and fig_perf_gen so every result figure carries its
    # key the same way. Three entries fit one row at column width. The anchor clears the x label,
    # and bbox_inches="tight" in C.save grows the canvas to include it.
    # Each entry is two lines, codec above its coefficient. labelspacing separates the entries
    # vertically; the anchor sits well below the x label rather than just under the axes.
    C.legend_below(fig, ncol=3, columnspacing=1.6, handlelength=1.0, handletextpad=0.4,
                   labelspacing=0.3)
    C.save(fig, "fig_lenpredict", width="column")


if __name__ == "__main__":
    main()
