# /// script
# requires-python = ">=3.9"
# dependencies = ["matplotlib", "numpy"]
# ///
"""Fig. perf_real: the result space on ONE device as throughput vs compression ratio.

Every mark is a B300 measurement from one suite leg. Holding the device fixed is the point: an
earlier form drew our codec spanning four GPUs while the Blackwell-only DE and nvCOMP codecs were
single B300 points, which set our four-generation spread against each baseline's best chip and
understated the same-device margin the prose claims. Varying the device is fig_perf_gen's job.

This deliberately reuses fig_sota's look -- theme, palette, family shapes, log axes, expanded
legend, panel proportions -- because it IS fig_sota rebuilt on the fifteen-column corpus. The
styling is not re-derived here; where they differ, fig_sota is right.

BEST AGAINST BEST, AND EVERY CONFIGURATION OF THEIRS. Our mark is the best kernel. A baseline
gets its whole sweep -- the engine's four codecs crossed with five chunk sizes, three Zstd
levels, three nvCOMP software codecs -- reduced per column to the configurations nothing else of
that baseline beats on both axes. Tuning only one side would be the sandbag, and quoting only
the engine's fastest setting would have hidden its high-ratio half, which is the interesting
one. Per-column shipped-selector rates, what a deployment gets, are reported in the prose.

THE STAIRCASE IS THE BASELINE PARETO FRONTIER, and the claim is asserted PER COLUMN. A codec's
ratio is a property of the data, so a pooled frontier can put us on one column against a baseline
on another; with c_address in the corpus that produces false violations. Like for like, 26
baseline configurations per column: 30 of 30 real-column marks clear all of them, and the
generated panel has exactly one exception, pinned by name in main().

ZSTD IS A REAL COMPETITOR ON LOG-STRUCTURED COLUMNS, not the floor-dwelling series it first looks
like. Its GPU rate tracks the FRAME COUNT a column yields, not the codec: Loghub Windows gives
2022 frames and decodes at 165-200 GB/s with a 25-50x ratio, while Wikipedia's long documents give
115 frames and 1.7-3.1 GB/s. It is therefore in the per-column dominance test, not just the plot.

gANS AND BOTH BITCOMP VARIANTS COME FROM A SECOND LEG. The paper suite's DE stage runs only
DEFLATE, LZ4 and Snappy, so these three are measured by the MATERIALIZE+SW leg
(results/suite-baselines-*) and merged here. The two legs share a vortex_rev, a training seed, the
fifteen columns and raw_bytes per column, which is what makes one axis legitimate; see
suite.baselines_root(). None of the three reaches our compression ratio on any real column, so
they sit left of every OnPair mark rather than under it -- Bitcomp-sparse is the fastest thing on
the panel on four of the ten, and stores 1.00 to 1.10x while doing it. The one place a software
codec dominates us is gANS on c_address, generated random characters where a pair-merging
dictionary has nothing to merge and an entropy coder still has a character distribution.



Source: results/suite-<id>/b300/{sweep,fsst12}_summary_*_boost.json + onpair_nvcomp_hw.json.
"""
import argparse
import itertools
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402
import suite as S  # noqa: E402

YLO, YHI = 0, 2000

# Configuration -> shade, in technique families, copied from fig_sota so a colour means the same
# thing in both figures. OnPair replaces the FastPair label; the hues are unchanged.
# Each technique GROUP takes its own band of viridis, so the band says which family a mark
# belongs to and the step within it says which member. Zstd stays on the neutral greys: it is
# the context the positional claim is made against, not a family being compared. Group identity
# is also carried by FAMILY_MARKER below, which is what keeps the narrow bands readable -- a band
# has little luminance to divide, so shape does the work colour cannot.
# ORDER IS THE LEGEND ORDER, and it follows each band's own order so the legend reads as the
# ramp does: OnPair-16, OnPair-12, FSST-12 for ours, and Bitcomp-default, Bitcomp-sparse, gANS
# for nvCOMP. A legend that lists members in a different order from the colours it explains
# makes the reader re-derive the mapping entry by entry.
CFG = {
    "OnPair-16": C.colour("tech-ours", "OnPair-16"),
    "OnPair-12": C.colour("tech-ours", "OnPair-12"),
    "FSST-12": C.colour("tech-ours", "FSST-12"),
    "DE Deflate (5)": C.colour("tech-engine", "DE Deflate (5)"),
    "DE Deflate (0)": C.colour("tech-engine", "DE Deflate (0)"),
    "DE LZ4": C.colour("tech-engine", "DE LZ4"),
    "DE Snappy": C.colour("tech-engine", "DE Snappy"),
    # The DARK three of the neutral ramp, not the light three. Every Zstd mark falls inside the
    # envelope wash, so the lightest grey (#d9d9d9) was a mark you had to already know was there.
    "Zstd (-10)": C.neutral(1), "Zstd (3)": C.neutral(2), "Zstd (19)": C.neutral(3),
    "Bitcomp-default": C.colour("tech-nvcomp", "Bitcomp-default"),
    "Bitcomp-sparse": C.colour("tech-nvcomp", "Bitcomp-sparse"),
    "gANS": C.colour("tech-nvcomp", "gANS"),
}
FAMILY_MARKER = {"OnPair": "o", "DE": "s", "Zstd": "^", "nvCOMP-sw": "D"}
FAMILY = {
    "OnPair-12": "OnPair", "OnPair-16": "OnPair", "FSST-12": "OnPair",
    "DE Deflate (5)": "DE", "DE Deflate (0)": "DE", "DE LZ4": "DE", "DE Snappy": "DE",
    "Zstd (-10)": "Zstd", "Zstd (3)": "Zstd", "Zstd (19)": "Zstd",
    "gANS": "nvCOMP-sw", "Bitcomp-default": "nvCOMP-sw", "Bitcomp-sparse": "nvCOMP-sw",
}
MARKER = {k: FAMILY_MARKER[v] for k, v in FAMILY.items()}
DEV = "b300"
OFFSCALE = []


# BASIS: every byte-validated kernel, via suite.best_rate_gb_s -- the basis sec:evaluation
# declares and the one the baselines already get. The condition the old comment here set for
# revisiting was met: the DE on this plot IS quoted at its best configuration, best of four codec
# families crossed with five chunk sizes, with its ratio moving with the choice.
def oracle_rate(c):
    """Best kernel on this column, GB/s. The oracle side of an oracle-vs-oracle comparison."""
    return S.best_rate_gb_s(c)



def frontier(pts, xlo=None):
    """Best baseline rate available at each ratio or better, as a staircase."""
    if not pts:
        return [], []
    xs, ys, best = [], [], 0.0
    for x, y in sorted(pts, reverse=True):
        best = max(best, y)
        xs.append(x); ys.append(best)
    xs, ys = list(reversed(xs)), list(reversed(ys))
    if xlo is not None and xs:
        xs, ys = [xlo] + xs, [ys[0]] + ys
    return xs, ys


def frontier_at(pts, ratio):
    vals = [y for x, y in pts if x >= ratio]
    return max(vals) if vals else None


def mark(ax, r, t, color, marker="o", s=None, alpha=1.0):
    """Off-scale marks are drawn open at the floor rather than dropped, so a reader can see that
    a family exists below the axis instead of inferring it never ran."""
    s = C.MS_SCATTER if s is None else s
    if t < YLO:
        OFFSCALE.append((None, t))
        ax.scatter([r], [YLO * 1.04], s=s * 0.8, facecolors="none", marker=marker,
                   edgecolors=color, linewidths=0.7, zorder=5, alpha=alpha)
        return
    ax.scatter([r], [t], s=s, color=color, marker=marker, zorder=5, linewidths=0, alpha=alpha)


def collect(root, rows):
    """(ours, baselines) for one panel. ours: (ratio, rate, cfg, column). baselines: (r, t, cfg)."""
    op = S.cells(root, DEV, "boost", "onpair")
    fs = S.cells(root, DEV, "boost", "fsst12")
    zs = S.cells(root, DEV, "boost", "zstd")
    sw = S.sw_rows(S.sw_root_for(DEV), DEV)
    ours, bases, faded = [], [], []
    for _, ds, col in rows:
        # ZSTD IS DRAWN TWICE, and Section 5 says why: its frame size trades ratio against rate
        # rather than admitting a best setting, so there is no oracle to report. The vendor default
        # (64 KiB, nvCOMP's documented starting chunk) is drawn as-is; every other non-dominated
        # (frame, level) is drawn faded. Falls back to the old single-frame cells when the frame
        # sweep is absent, so this file still runs against an older results tree.
        zd = S.zstd_default_points(ds, col)
        if zd:
            bases += zd
            faded += [p for p in S.zstd_best_points(ds, col) if p not in zd]
        else:
            bases += S.zstd_points(zs, ds, col)
        bases += S.sw_points(sw, ds, col)
        for cfg, store, bits in (("OnPair-12", op, 12), ("OnPair-16", op, 16),
                                 ("FSST-12", fs, 12)):
            c = store.get((ds, col, bits))
            r, t = S.ratio(c), oracle_rate(c)
            if r and t:
                ours.append((r, t, cfg, col))
        bases += S.de_points(root, DEV, ds, col)
    return ours, bases, faded


# Fill alpha PER LEVEL, not one constant. The three levels are drawn from the neutral ramp, which
# has little luminance to divide, and their regions overlap over most of the panel; at a shared
# alpha they resolved into a single grey slab. Alpha rising with the level spreads them in the
# one dimension the ramp cannot. The frontier lines carry the identity where the fills still
# overlap, so they are drawn at full opacity rather than washed like the region.
ZSTD_FILL_ALPHA = {-10: 0.13, 3: 0.21, 19: 0.30}


def zstd_regions(ax, rows, xlo):
    """Shade what each Zstd level reaches, with that level's own Pareto frontier drawn over it.

    THREE REGIONS, NOT ONE, because the levels do not nest. Level -10 owns the high-rate corner
    and 19 the high-ratio one, so a single Zstd region would assert a reach no single setting
    has, and the compression level is the one Zstd knob a user actually sets.

    THE REGION IS THE WHOLE SWEEP, not the pruned faded set: every frame measured at that level
    goes in, and the staircase over them is the best rate the level reaches at each ratio or
    better. Drawing the frontier of an already-pruned set would draw the frontier of a previous
    decision rather than of the measurement.

    POOLED ACROSS THE PANEL'S COLUMNS, exactly like the baseline staircase it sits inside, and
    for the same reason: this is orientation. A codec's ratio is a property of the data, so the
    dominance claim is asserted per column in main() and never read off this shading.

    Returns the per-level reach for the caller to report, since some of it falls outside xlim.
    """
    out = []
    for i, lv in enumerate(S.PAPER_ZSTD_LEVELS):
        pts = []
        for _, ds, col in rows:
            pts += S.zstd_level_points(ds, col, lv)
        if not pts:
            continue
        colour = CFG["Zstd (%s)" % lv]
        zx, zy = frontier(pts, xlo=xlo)
        ax.fill_between(zx, 1e-3, zy, step="pre", color=colour,
                        alpha=ZSTD_FILL_ALPHA.get(lv, 0.2), lw=0, zorder=2)
        ax.step(zx, zy, where="pre", color=colour, lw=0.9, zorder=2)
        out.append((lv, len(pts), max(x for x, _ in pts), max(y for _, y in pts)))
    return out


def panel(ax, root, rows, title):
    from matplotlib.ticker import FixedLocator, ScalarFormatter, NullFormatter
    ours, bases, faded = collect(root, rows)
    bp = [(r, t) for r, t, _ in bases]
    allr = [r for r, _, _, _ in ours] + [r for r, _ in bp] or [1.0]
    allr += [r for r, _, _ in faded]
    xmin, xmax = min(allr) * 0.88, max(allr) * 1.14
    xs, ys = frontier(bp, xlo=xmin)
    if xs:
        # DO NOT CARRY THE LAST STEP TO THE RIGHT EDGE. It used to, back when xmax sat a few
        # percent past the highest baseline ratio and the carry was a cosmetic gap-filler. With
        # the Zstd tails on the panel, xmax is 157 against a best baseline ratio of 19, and the
        # carry drew the envelope flat across eight times the measured range -- reading as the
        # engine holding 630 GB/s at a ratio it never reaches. The envelope now stops where the
        # baselines stop.
        ax.step(xs, ys, where="pre", color=C.INK, lw=0.8, alpha=0.55, zorder=3)
        # C.WASH, not a grey at low alpha: the three Zstd levels are drawn from C.NEUTRAL and
        # sit inside this region, so a grey ground swallowed them. See common.WASH.
        ax.fill_between(xs, 1e-3, ys, step="pre", color=C.WASH, lw=0, zorder=1)
    zstd_regions(ax, rows, xmin)
    ax.set_xlim(xmin, xmax)
    # Faded first, so the vendor default and our marks draw over them rather than under.
    for r, t, cfg in faded:
        mark(ax, r, t, CFG[cfg], marker=MARKER.get(cfg, "s"), alpha=0.28)
    for r, t, cfg in bases:
        mark(ax, r, t, CFG[cfg], marker=MARKER.get(cfg, "s"))
    for r, t, cfg, _ in ours:
        mark(ax, r, t, CFG[cfg], marker=MARKER[cfg])
    ax.set_xscale("log")
    # FILTERED TO THE LIMITS, and carried past 20. The list was fixed at a 20x ceiling from when
    # the Zstd tails were clipped off the panel; with them drawn, the right third of the real
    # panel had no label under it.
    ticks = [t for t in (1, 1.5, 2, 3, 5, 7, 10, 20, 50, 100) if xmin <= t <= xmax]
    ax.xaxis.set_major_locator(FixedLocator(ticks))
    ax.xaxis.set_major_formatter(ScalarFormatter())
    ax.xaxis.set_minor_locator(FixedLocator([]))
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.set_xlabel("compression ratio (log)")
    ax.set_title(title)
    return ours, bp


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--suite-id", default=None)
    a = ap.parse_args()
    root = S.latest_root(a.suite_id)
    if root is None:
        sys.exit("no results/suite-* directory found")

    plt = C.apply_theme()
    fig, (axR, axS) = plt.subplots(1, 2, figsize=(7.0, 2.05), sharey=True)
    oR, bR = panel(axR, root, S.REAL, "Real-world columns")
    oS, bS = panel(axS, root, S.GEN, "Generated columns")
    # GSST reports one number: 191 GB/s on an A100, TPC-H l_comment. That is generated data, so it
    # goes on the synthetic panel, and it is another device, so it is drawn but never enters the
    # baseline frontier or the dominance test.
    axS.scatter([2.74], [C.GSST_GBS], s=C.MS_STAR ** 2, marker="*", color=C.GSST_RED, zorder=6)

    # ASSERTED PER COLUMN, not against the pooled staircase. The staircase is drawn for
    # orientation, but a pooled test compares us on one column against a baseline measured on
    # ANOTHER, and a codec's ratio is a property of the data. c_address is the live example:
    # OnPair-16 reaches 1.09x there, below a 697 GB/s baseline that belongs to l_comment or
    # ps_comment -- different data, not a counterexample. On its own column the DE manages 0.99x,
    # and we are not dominated.
    # EVERY PLOTTED BASELINE IS IN THE TEST. gANS and both Bitcomp variants were drawn and
    # folded into the staircase but left out of this loop, which is the wrong way round: they
    # are the FAST baselines. Bitcomp-sparse reaches 1319 GB/s on FineWeb2, above every OnPair
    # mark on the panel, so a test that skipped it asserted less than the paper's sentence does.
    # It clears the test because it stores 1.00x against our 1.99x, and that is the reason to
    # test it rather than a reason to omit it.
    # ONE KNOWN EXCEPTION, PINNED BY NAME so that a NEW one still fails this build. gANS
    # dominates OnPair-16 on c_address: 1.33x at 653 GB/s against 1.02x at 393. c_address is
    # random characters, so a pair-merging dictionary finds nothing to merge while an entropy
    # coder still finds a character distribution. It is a generated column, and the paper pools
    # generated columns into no real-data claim. It is listed rather than skipped because the
    # scope belongs in the sentence that makes the claim, not in a filter here.
    #
    # Note what is NOT dominated on that column: OnPair-12 reaches 1.19x at 783 GB/s, and
    # gANS's better ratio comes with a lower rate. OnPair-16 is worse than OnPair-12 on BOTH
    # axes there, so the dominated point is a preset no per-column selection would choose.
    KNOWN = {("c_address", "OnPair-16")}
    violations, n, excepted = [], 0, []
    for rows in (S.REAL, S.GEN):
        ours, _, _ = collect(root, rows)
        zc = S.cells(root, DEV, "boost", "zstd")
        sw = S.sw_rows(S.sw_root_for(DEV), DEV)
        by_col = {}
        for _, ds, col in rows:
            by_col[col] = S.baseline_points(root, DEV, ds, col, zc, sw)
        for r, t, cfg, col in ours:
            n += 1
            dom = [b for b in by_col.get(col, []) if b[0] >= r and b[1] > t]
            if dom:
                b = max(dom, key=lambda p: p[1])
                msg = ("%s %s: %.0f GB/s at ratio %.2f, %s %.0f at %.2f"
                       % (col, cfg, t, r, b[2], b[1], b[0]))
                (excepted if (col, cfg) in KNOWN else violations).append(msg)
    if violations:
        raise SystemExit("fig_perf_real: per-column dominance VIOLATED on %s:\n  %s"
                         % (DEV, "\n  ".join(violations)))
    print("per-column dominance holds on %s: %d of %d marks clear every baseline on their own "
          "column, against %d pinned exception(s)" % (DEV, n - len(excepted), n, len(excepted)))
    for m in excepted:
        print("  pinned exception (generated column, in no real-data claim): %s" % m)
    for k in sorted(KNOWN):
        if not any(m.startswith("%s %s:" % k) for m in excepted):
            raise SystemExit("fig_perf_real: pinned exception %s no longer occurs. Remove it "
                             "from KNOWN and strengthen the claim." % (k,))

    from matplotlib.ticker import FixedLocator
    axR.set_ylim(YLO, YHI)
    axR.yaxis.set_major_locator(FixedLocator([0, 500, 1000, 1500, 2000]))
    axR.set_ylabel("decode throughput (GB/s)")

    from matplotlib.lines import Line2D

    def flip(items, ncol):
        return list(itertools.chain(*[items[i::ncol] for i in range(ncol)]))

    codec_handles = [Line2D([], [], color=CFG[k], marker=MARKER.get(k, "o"), ls="", ms=C.MS_LEGEND,
                            label=k) for k in CFG]
    gsst = Line2D([], [], marker="*", color=C.GSST_RED, ls="", ms=C.MS_STAR * 1.2, label="GSST (A100)")
    # No off-scale entry. YLO is 0, so mark()'s t < YLO branch needs a negative decode rate and
    # never fires; the legend was advertising a convention that never appears on the page. The
    # branch stays as a guard in case the floor is ever raised.
    # NO ENVELOPE ENTRY EITHER, for the same reason one step further: the caption already says
    # what the step line is, and a key that repeats the caption spends a slot to say nothing.
    # SEVEN COLUMNS, so the two rows fall where the reader wants them without a filler: our
    # three codecs and the Engine's four on the first, the whole software side -- three Zstd
    # levels, two Bitcomp variants, gANS -- on the second, and GSST last, since it is the one
    # mark measured on another device.
    leg = codec_handles + [gsst]
    fig.tight_layout(pad=0.3)
    # Fourteen entries over seven columns at full width. mode="expand" spreads them across the
    # whole canvas rather than centring a block, so the two rows align; anchored by their top
    # edge C.LEGEND_GAP under the figure, as every other below-axes key is.
    C.legend_below(fig, handles=flip(leg, 7), expand=True, ncol=7,
                   columnspacing=0.6, handlelength=1.1, handletextpad=0.45)
    C.save(fig, "fig_perf_real", width="text")

    zcells = S.cells(root, DEV, "boost", "zstd")
    nz = sum(len(S.zstd_points(zcells, ds, col)) for _, ds, col in S.REAL + S.GEN)
    print(f"\nZstd points plotted: {nz}")
    print("BASELINE PROVENANCE, so a reader of this output knows what came from where:")
    print("  gANS, Bitcomp-{default,sparse}: the MATERIALIZE+SW leg, not the paper suite, whose")
    print("                 DE stage runs only DEFLATE/LZ4/Snappy. Same rev, seed and columns.")
    print("  GSST           : drawn on the synthetic panel as a cross-device reference (A100, l_comment)")


if __name__ == "__main__":
    main()
