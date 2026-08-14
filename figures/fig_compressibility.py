# /// script
# requires-python = ">=3.9"
# dependencies = ["matplotlib", "numpy"]
# ///
"""Fig. compressibility: geometric-mean compression ratio per technique, real vs
synthetic columns. OnPair (what FastPair decodes) matches the best byte-oriented
codecs on the real high-cardinality columns, so the throughput win comes at a
competitive ratio. Competitor ratios come from the committed CPU sweep
(results/cpu-sota/, a codec's ratio is device-independent so any leg serves);
OnPair's ratios are the GPU cells' mem_ratio at both presets.

SIDECAR ACCOUNTING (2026-07-18): FastPair stores the per-batch output offsets as
a small sidecar so decode positioning is free (the "store" arm of §3.1). That
sidecar is NOT part of the OnPair array mem_ratio measures, so we fold it into the
reported footprint here: stored_ratio = mem_ratio / (1 + sidecar_frac), where
sidecar_frac = compressed-sidecar-bytes / compressed-column-bytes. The sidecar is
~0.5% (0.37-1.08%), so the fold-in shifts each OnPair bar by well under the 0.1x
label resolution; it is done for honesty, not visible effect. OnPair still matches
Deflate-9/Zstd-3 on the real columns after the fold-in.

DATA + REGENERATION of the sidecar fractions:
  results/b300-campaign-0717/offset_cost.jsonl  (per column, per preset:
  offset_compressed_bytes, compressed_bytes). Regenerate with the fork branch
  mp/fastpair, CPU-only:
    ONPAIR_OFFSET_COST=offset_cost.jsonl target/release/onpair-chunk-bench run \\
      --parquet <col>.parquet --column <col> --dataset-id <id> \\
      --bits 12,16 --chunk-bytes 1048576000 --threshold 0.2 --out-dir /tmp/vx
  (same bench that produces results/offset-reshape-cost-laptop/; see its README).
  Columns absent from offset_cost.jsonl (the three Amazon categories) use
  DEFAULT_SIDECAR_FRAC, the measured median; the fold-in is below label resolution
  either way.
"""
import json
import math
import common as C

# Median stored-offset-sidecar fraction, for columns not in offset_cost.jsonl.
DEFAULT_SIDECAR_FRAC = 0.005
# dataset-id aliases: offset_cost uses the TPC-H bench id; COLMAP uses "lship".
_OFFSET_DID_ALIAS = {"lship": "tpch-sf10"}


def _load_sidecar_frac():
    """(dataset_id, column, bits) -> compressed-sidecar / compressed-column."""
    frac = {}
    path = C.RESULTS / "b300-campaign-0717" / "offset_cost.jsonl"
    if not path.exists():
        return frac
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        col_bytes = r.get("compressed_bytes") or 0
        if col_bytes:
            # offset_cost.jsonl keys the dataset as "dataset" (not "dataset_id").
            frac[(r["dataset"], r["column"], r["bits"])] = (
                r["offset_compressed_bytes"] / col_bytes
            )
    return frac


_SIDECAR = _load_sidecar_frac()


def sidecar_frac(did, gc, bits):
    f = _SIDECAR.get((did, gc, bits))
    if f is None:
        f = _SIDECAR.get((_OFFSET_DID_ALIAS.get(did, did), gc, bits))
    return DEFAULT_SIDECAR_FRAC if f is None else f

COLMAP = {  # cpu column -> (gpu dataset_id, gpu column, panel)
    "clickbench_url": ("clickbench", "URL", "R"), "fineweb": ("fineweb", "text", "R"),
    "wikipedia": ("wikipedia", "text", "R"), "book_reviews": ("book-reviews", "text", "R"),
    "amazon_movies": ("amazon-movies", "text", "R"), "amazon_electronics": ("amazon-electronics", "text", "R"),
    "l_comment": ("tpch-sf10", "l_comment", "S"), "ps_comment": ("tpch-sf10", "ps_comment", "S"),
    "l_shipinstruct": ("lship", "l_shipinstruct", "S"), "synthetic_url": ("synthetic", "url", "S"),
}
# technique -> color (matches fig_sota_cpu's palette). OnPair is the protagonist.
TECH = [
    ("OnPair-16", "#08519c"), ("OnPair-12", "#6baed6"), ("Deflate (9)", "#fdae61"), ("Zstd (3)", "#525252"),
    ("Zstd (1)", "#969696"), ("Deflate (1)", "#f16913"), ("LZ4", "#a63603"),
    ("FSST-8", C.GSST_RED), ("FSST-12", "#c994c7"), ("Zstd (-10)", "#cccccc"),
]
# The CPU sweep's "FSST" is the 8-bit dialect (fsst-rs), so it is labelled FSST-8 here now
# that the escape-free 12-bit dialect appears alongside it.
RENAME_CODEC = {"FSST": "FSST-8"}

# FSST-12 ratio basis. Native is the codec's own fixed 12-bit packing; container-matched
# measures the code stream through the instrument OnPair's codes go through (BtrBlocks over
# a u16 array). Container-matched is plotted because every other bar on the OnPair side of
# this figure is container-measured, so it is the like-for-like comparison; on the real
# columns the two agree to two decimals, so the choice is visible only on low-cardinality
# synthetic data. Flip to False to plot native.
FSST12_CONTAINER_MATCHED = True
# the bench labels Deflate by mode; relabel to the explicit zlib level for the figure.
RENAME = {"Deflate-hi": "Deflate (9)", "Deflate-fast": "Deflate (1)"}


def fsst12_ratio(col):
    """FSST-12's ratio for one column, from whichever chip measured it.

    A codec's compression ratio is device-independent, so the first chip that has the
    column serves, exactly as the competitor legs do.
    """
    did, gc, _ = COLMAP[col]
    for g in C.GPUS:
        c = C.cell(g, did, gc, 12, C.FSST12)
        if not c:
            continue
        if FSST12_CONTAINER_MATCHED and c.get("mem_ratio_container_matched"):
            return c["mem_ratio_container_matched"]
        if c.get("mem_ratio"):
            return c["mem_ratio"]
    return None


def onpair_ratio(col, bits=16):
    did, gc, _ = COLMAP[col]
    for g in C.GPUS:
        c = C.cell(g, did, gc, bits)
        if c and c.get("mem_ratio"):
            # Fold in the stored output-offset sidecar (§3.1): the footprint is the
            # OnPair array plus the sidecar mem_ratio does not count.
            return c["mem_ratio"] / (1.0 + sidecar_frac(did, gc, bits))
    return None


def geomean(xs):
    xs = [x for x in xs if x]
    return math.exp(sum(math.log(x) for x in xs) / len(xs)) if xs else None


def main():
    leg = json.load(open(C.RESULTS / "cpu-sota" / "intel-sapphire.json"))
    ratio = {}  # column -> {technique: ratio}
    for c in leg["competitors"]:
        name = RENAME.get(c["codec"], c["codec"])
        ratio.setdefault(c["column"], {})[RENAME_CODEC.get(name, name)] = c["ratio"]
    for col in COLMAP:
        ratio.setdefault(col, {})["OnPair-16"] = onpair_ratio(col, bits=16)
        ratio.setdefault(col, {})["OnPair-12"] = onpair_ratio(col, bits=12)
        ratio.setdefault(col, {})["FSST-12"] = fsst12_ratio(col)

    real = [c for c, m in COLMAP.items() if m[2] == "R"]
    syn = [c for c, m in COLMAP.items() if m[2] == "S"]
    gm_real = {t: geomean([ratio[c].get(t) for c in real]) for t, _ in TECH}
    gm_syn = {t: geomean([ratio[c].get(t) for c in syn]) for t, _ in TECH}

    import numpy as np
    plt = C.apply_theme()
    fig, ax = plt.subplots(figsize=(7.0, 1.75))  # shrunk further (shorter at \textwidth)
    x = np.arange(len(TECH)); w = 0.4
    labels = [t for t, _ in TECH]
    colors = [c for _, c in TECH]
    ax.bar(x - w / 2, [gm_real[t] or 0 for t in labels], w, color=colors, edgecolor="none", label="real")
    ax.bar(x + w / 2, [gm_syn[t] or 0 for t in labels], w, color=colors, edgecolor=C.INK,
           linewidth=0.7, alpha=0.55, label="synthetic", hatch="///")
    for i, t in enumerate(labels):
        if gm_real.get(t):
            ax.text(i - w / 2, gm_real[t] + 0.1, "%.1f" % gm_real[t], ha="center", va="bottom", fontsize=6)
        if gm_syn.get(t):
            ax.text(i + w / 2, gm_syn[t] + 0.1, "%.1f" % gm_syn[t], ha="center", va="bottom", fontsize=6)
    ax.set_xticks(x); ax.set_xticklabels(labels, rotation=20, ha="right", fontsize=7)
    ax.set_ylabel("compression ratio")
    ax.set_ylim(0, max(v for v in gm_syn.values() if v) * 1.15)
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(facecolor=C.INK, label="real columns"),
                       Patch(facecolor=C.INK, alpha=0.55, hatch="///", label="synthetic columns")],
              frameon=False, fontsize=7, loc="upper right")
    fig.tight_layout()  # fill the figure width (match fig_sota's rendered size at \textwidth)
    C.save(fig, "fig_compressibility")


if __name__ == "__main__":
    main()
