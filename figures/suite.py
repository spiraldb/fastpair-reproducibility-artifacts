"""Loader for a suite campaign under results/suite-<id>/<chip>/.

WHY A SEPARATE MODULE. common.py's load()/cell() encode the OLD corpus's directory and filename
conventions (results/<gpu>/onpair_summary_<dataset>.json, dataset ids like tpch-sf10 and lship).
A suite leg lands somewhere else entirely, with the clock state in the filename and fifteen
columns whose ids do not overlap the old ten. Teaching common.py both shapes would put a branch
in every existing figure; this keeps the new layout in one place and leaves those figures alone.

MISSING DATA IS REPORTED, NOT HIDDEN. A campaign is often partial -- a leg still running, a chip
that stocked out, a stage that skipped. Every accessor here returns None or an empty result for
absent data rather than raising, and `coverage()` says exactly what is present. Figures are
expected to draw the hole with a fixed legend, so a reader sees that the A100 is missing instead
of seeing a plot that silently has three chips in it.

DEFINITIONS, matched to figures/tab_datasets.py so a number means the same thing everywhere:

  tokens  gpu.distinct_codes
  len     sample_bytes / (gpu.compressed_bytes / 2)   token-weighted mean decoded bytes per code.
          NOT gpu.dict_mean_len, which is the unweighted mean over dictionary ENTRIES and runs
          about 25% higher.
  le8     gpu.frac_le8
  ratio   sample_bytes / on_disk_bytes -- AT REST: string bytes in against the stored .vortex
          file, which holds the bit-packed codes, the dictionary and the offset sidecar.
          CORRECTED 2026-08-22. This read gpu.compressed_bytes, which is the in-memory UNPACK
          (exactly 2.0001 B per code, 12-bit codes widened to u16), so it understated OnPair-12
          by 17-33% and overstated OnPair-16 by up to 12%. See ratio() for the measurements.
          The prior docstring rejected mem_ratio as "the flattering one" and kept the unpack.
          That was backwards: mem_ratio's denominator is within 0.001% of on_disk_bytes, so the
          number it rejected (FineWeb2 1.99) is the correct at-rest ratio and the one it kept
          (1.49) divides by an array that only exists after decode begins.
  rate    decoded_bytes / min(decode_ns_iters) for the SHIPPED selector (gpu.auto_kernel), in
          GB/s. bytes/ns is exactly GB/s. min-of-N per Lemire, matching every prior campaign.
"""
import glob
import json
import os
import re
import sys
from pathlib import Path


# ============================================================================================
# "EXPERIMENTAL" DOES NOT MEAN "IGNORE THIS". READ THIS BEFORE CHOOSING A RATE.
# ============================================================================================
# Every kernel the grid generator emits carries role: KernelRole::Experimental. That is a
# BUILD-SYSTEM DEFAULT -- gen_packed_grid.py stamps it on line 126 of every variant it writes --
# and it is not a judgement about validity, correctness or deployability. All 564 generated
# kernels (the dg, dw, dh and ds families) are byte-validated on every leg exactly like the
# production ones, and they are the entire evidence base for Section 4.
#
# The 20 kernels marked production are the older hand-written set (onpair_decompress_1tpt..8tpt,
# onpair_shmem_*). They expose K, and they do NOT expose T, B or S. So gpu.best_kernel and
# gpu.best_decode_gib_s, which range over production only, are the best rate reachable through
# the CURRENT SELECTOR -- not the best rate the codec achieves. On Wikipedia at OnPair-12 the
# difference is 916 against 985 GB/s, 7.5%, and the winner is onpair_ds_k6_t128_b4_s14.
#
# WHY THIS MATTERS FOR A COMPARISON. We hand every baseline its own parameter sweep and then
# quote its best: the Decompression Engine gets four codec families crossed with five chunk
# sizes and we report best_codec AND best_chunk_bytes; nvCOMP Zstd gets three levels; a
# dictionary codec gets its dictionary size. Varying K, T, B and S is the SAME KIND of tuning --
# a compile-time configuration of one decoder, chosen per column -- and excluding it while
# including theirs is not conservatism, it is an asymmetric handicap that understates this work
# against baselines we tuned freely.
#
# So: pick the basis deliberately and say which one, per figure.
#   - "best deployable"   -> production only. Honest for "what a user gets today", and it is
#                            what gpu.best_kernel gives you.
#   - "best configured"   -> max over all timed kernels. The right basis against a baseline
#                            whose own best configuration is being quoted.
# Neither is wrong. Silently taking best_kernel because it is the field that exists, while the
# other side of the plot gets its full sweep, IS wrong.
#
# There is a standing caution in this repo against quoting the fastest probe as "the codec's
# rate". It is worth knowing what it does and does not rest on: the two retractions in the
# paper's history are the 1.7x port-versus-GSST claim (cd70a94, our port got pre-staged offsets
# outside the timed region while GSST paid for positioning inside its own) and a revert of wrong
# DE corrections (064c8dc). Neither concerned quoting our own best probe. Treat the caution as a
# prompt to name the basis, not as a reason to discard 564 measurements.
# ============================================================================================

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"

# The corpus, in the paper's Table 1 order: real above the rule, generated below.
REAL = [
    ("FineWeb2 Mandarin",        "fineweb2-zh",        "text"),
    ("Wikipedia",                "wikipedia",          "text"),
    ("CodeParrot",               "codeparrot",         "content"),
    ("Loghub \\texttt{Android}", "loghub-android",     "line"),
    ("ClickBench \\texttt{URL}", "clickbench",         "URL"),
    ("ClickBench \\texttt{Title}", "clickbench",       "Title"),
    ("Loghub \\texttt{HDFS}",    "loghub-hdfs",        "line"),
    ("Loghub \\texttt{Thunderbird}", "loghub-thunderbird", "line"),
    ("Loghub \\texttt{Spark}",   "loghub-spark",       "line"),
    ("Loghub \\texttt{Windows}", "loghub-windows",     "line"),
]
GEN = [
    ("TPC-H \\texttt{c\\_address}",      "tpch-sf263", "c_address"),
    ("TPC-H \\texttt{l\\_comment}",      "tpch-sf15",  "l_comment"),
    ("TPC-H \\texttt{o\\_clerk}",        "tpch-sf45",  "o_clerk"),
    ("TPC-H \\texttt{l\\_shipinstruct}", "tpch-sf15",  "l_shipinstruct"),
    ("TPC-H \\texttt{ps\\_comment}",     "tpch-sf15",  "ps_comment"),
]
# THE LEG THE PAPER READS, DECLARED. Every figure that does not take an explicit --suite-id gets
# this one. It used to be "the newest results/suite-* by name", which made a directory name into
# a load-bearing decision: any leg whose id sorted after "paper-" silently re-pointed seven
# figures and the claims reducer at data the paper does not describe. The software-baseline leg
# was named "suite-baselines-*" to sort BEFORE this one, which is a workaround for the sort rather
# than a reason the sort is right. Name legs whatever describes them; change this line to move the
# paper.
PAPER_SUITE = "suite-paper-20260821"
# THE COMPARATOR LEG. Three baselines in PAPER_SUITE were measured over a narrower space than we
# gave ourselves: FSST-12 got 19 kernels against OnPair's 583, the Engine's chunk oracle sat at the
# largest of five sizes on 15 of 15 columns, and the Engine alone was fed a flat concatenation with
# no row structure. suite-comparators-20260827 remeasures those three on the same corpus and seed;
# it has no GRID arm, so OnPair still comes from PAPER_SUITE and the two legs are read together.
#
# THAT PAIRING IS LICENSED BY A CONTROL, NOT BY ASSERTION. Both legs ran FSST-12 at the identical 19
# production kernels on the identical fifteen columns, differing only in revision: -0.65% to +0.29%,
# median -0.15%, n=15, inside the 0.82% p99 split-half noise floor. See that leg's README. Re-run
# the control after any kernel change before trusting the pairing.
COMPARATOR_SUITE = "suite-comparators-20260827"
# THE THREE ZSTD LEVELS THE PAPER REPORTS: fast mode, the default, and the highest below the
# --ultra tier. The comparator leg measured five (-10, 1, 3, 9, 19); 1 and 3 are near-duplicates on
# this corpus -- 50.37x against 49.77x at the top, 183 against 179 GB/s -- so three points spanning
# 1.12x to 62.87x costs the same ink as three spanning 1.12x to 50.37x with a repeat in the middle.
# What was collected and what is plotted are separate decisions; this is the plotted set.
PAPER_ZSTD_LEVELS = (-10, 3, 19)


def comparator_root():
    """The comparator leg's directory, or None when it is not present."""
    d = RESULTS / COMPARATOR_SUITE
    return d if d.is_dir() else None

CHIPS_CORE = ["b300", "h100", "a100", "l40s"]   # legacy order; lay figures out with common.DEVICE_ORDER

# A chip that is being brought up appears ONLY once its leg has landed. The four above are the
# paper's committed set and always get a slot, because a labelled gap is the honest rendering of a
# leg that was meant to exist and did not. A fifth chip has no such promise attached yet, so an
# empty slot for it would advertise a hole nobody was told to expect -- and it would change every
# committed figure before there is anything to show. Listing it here instead means the figures
# light up by themselves when the data arrives, with no code change at that moment.
CHIPS_EMERGING = ["rtxpro"]


def _present(chip):
    return chip_root(chip) is not None


def candidate_roots(chip):
    """Every suite directory holding this chip, declared campaign first.

    For a figure that needs a specific arm rather than just any data for the chip: it can walk these
    and pick the leg that actually timed what it draws, instead of assuming one directory holds
    everything. The campaign comes first so a figure never silently prefers a side leg."""
    out = []
    declared = RESULTS / PAPER_SUITE
    if (declared / chip).is_dir():
        out.append(declared)
    for d in sorted(RESULTS.glob("suite-*"), key=lambda p: p.name):
        if d.is_dir() and (d / chip).is_dir() and d != declared:
            out.append(d)
    return out


def chip_root(chip, suite_id=None):
    """The suite directory that holds THIS chip, preferring the declared paper campaign.

    A campaign is no longer one directory. The paper suite carries four chips; a chip brought up
    later lands in its own leg, and fig:perf_gen has to draw all of them on one axis. Resolving the
    root per chip is what makes that possible, and it is the same merge fig_perf_real already does
    for the software-baseline leg.

    COMPARABILITY IS NOT ASSUMED HERE -- it is the caller's to state. The rtxpro leg qualifies
    because it shares the paper campaign's vortex_rev (94905b572), training seed (20260819), the
    fifteen-column corpus and the identical clock protocol (boost:full max:full 75%:prod 55%:prod
    40%:prod). A leg that differed in any of those would need saying so beside the figure."""
    if suite_id:
        r = latest_root(suite_id)
        return r if r is not None and (r / chip).is_dir() else None
    declared = RESULTS / PAPER_SUITE
    if (declared / chip).is_dir():
        return declared
    for d in sorted(RESULTS.glob("suite-*"), key=lambda p: p.name):
        if d.is_dir() and (d / chip).is_dir():
            return d
    return None


def chips():
    """The chips to draw: the committed four, plus any emerging chip whose data exists."""
    return CHIPS_CORE + [c for c in CHIPS_EMERGING if _present(c)]


CHIPS = chips()




def latest_root(suite_id=None):
    """The suite directory the paper reads. An explicit id always wins.

    Falls back to the newest suite-* by name only when PAPER_SUITE is absent, so a fresh clone or
    a renamed campaign still resolves to something rather than to None -- but it says so, because
    silently reading a different campaign than the declared one is the failure this replaced."""
    if suite_id:
        p = RESULTS / (suite_id if suite_id.startswith("suite-") else f"suite-{suite_id}")
        return p if p.is_dir() else None
    declared = RESULTS / PAPER_SUITE
    if declared.is_dir():
        return declared
    cands = sorted(RESULTS.glob("suite-*"), key=lambda p: p.name)
    if cands:
        print("suite: declared %s is absent; falling back to %s"
              % (PAPER_SUITE, cands[-1].name), file=sys.stderr)
    return cands[-1] if cands else None


def baselines_root(baselines_id=None):
    """The software-baseline leg (gANS, Bitcomp), which is SEPARATE from latest_root()'s leg.

    Its stages are MATERIALIZE SW, so it carries onpair_nvcomp_sw.json and nothing the paper suite
    already has. Verified comparable to suite-paper-20260821 before the two were put on one axis:
    same vortex_rev (94905b572), same training_seed (20260819), same fifteen columns, and
    raw_bytes agrees with sample_bytes per column on every real column.
    """
    if baselines_id:
        p = RESULTS / (baselines_id if baselines_id.startswith("suite-") else f"suite-{baselines_id}")
        return p if p.is_dir() else None
    cands = sorted(RESULTS.glob("suite-baselines-*"), key=lambda p: p.name)
    return cands[-1] if cands else None


def sw_root_for(chip):
    """Where a chip's gANS/Bitcomp cells come from, PER CHIP.

    suite-baselines-20260822 measured them on a FLAT concatenation with no separators -- the last
    techniques whose ratio came from a byte stream rows cannot be recovered from, once the engine
    was framed on 2026-08-27. The comparator leg re-measured them on the same u32-length-framed
    stream every other technique gets. But that leg ran on the **b300 only**, so h100 and l40s still
    have to come from the flat leg.

    Resolved per chip rather than per run, and deliberately not silently: a caller that wants one
    basis across chips must check `sw_is_framed`. The paper reports the b300, which is framed.
    """
    cr = comparator_root()
    if cr is not None and (cr / chip / "onpair_nvcomp_sw.json").exists():
        return cr
    return baselines_root()


def sw_is_framed(chip):
    """True when this chip's software baselines pay for row structure like everything else."""
    cr = comparator_root()
    return cr is not None and (cr / chip / "onpair_nvcomp_sw.json").exists()


def sw_rows(root, chip="b300"):
    """nvCOMP software-codec cells (gANS, Bitcomp-*), keyed by (dataset_id, column).

    Empty dict when the leg is absent, so a figure degrades to the baselines it does have rather
    than raising."""
    if root is None:
        return {}
    f = Path(root) / chip / "onpair_nvcomp_sw.json"
    try:
        rows = json.load(open(f))
    except (OSError, json.JSONDecodeError):
        return {}
    return {(r.get("dataset_id"), r.get("column")): r for r in rows}


def clock_tags(root, chip):
    """Clock tags present for a chip, boost first then ascending pinned MHz."""
    d = Path(root) / chip
    tags = set()
    for f in d.glob("sweep_summary_*.json"):
        m = re.search(r"_(boost|sm\d+)\.json$", f.name)
        if m:
            tags.add(m.group(1))
    pinned = sorted((t for t in tags if t.startswith("sm")), key=lambda t: int(t[2:]))
    return (["boost"] if "boost" in tags else []) + pinned


def tag_mhz(tag):
    return None if tag == "boost" else int(tag[2:])


def _cells(root, chip, prefix, tag):
    out = []
    for f in sorted((Path(root) / chip).glob(f"{prefix}_*_{tag}.json")):
        try:
            rows = json.load(open(f))
        except (OSError, json.JSONDecodeError):
            continue          # a partial leg is normal; report it via coverage(), never raise
        if isinstance(rows, list):
            out.extend(rows)
    return out


def cells(root, chip, tag="boost", codec="onpair"):
    """Every cell for a chip at one clock state, keyed by (dataset_id, column, bits).

    FSST-12 and Zstd come from COMPARATOR_SUITE where it exists: in PAPER_SUITE, FSST-12 was
    measured with `--gpu-kernels production` (19 kernels against OnPair's 583) and Zstd was measured
    at three levels that stop short of the ratios it reaches. Zstd is still REPORTED at three
    levels, PAPER_ZSTD_LEVELS, just not the same three. OnPair is never redirected: the comparator
    leg has no GRID arm.
    """
    prefix = {"onpair": "sweep_summary", "fsst12": "fsst12_summary",
              "zstd": "zstd_summary"}[codec]
    src = root
    if codec in ("fsst12", "zstd"):
        cr = comparator_root()
        if cr is not None and (cr / chip).is_dir() and any((cr / chip).glob(f"{prefix}_*_{tag}.json")):
            src = cr
    out = {}
    for c in _cells(src, chip, prefix, tag):
        out[(c.get("dataset_id"), c.get("column"), c.get("bits"))] = c
    return out


def rate_gb_s(c):
    """Shipped-selector decode rate in GB/s, or None if the cell did not time it."""
    if not c:
        return None
    g = c.get("gpu") or {}
    auto = g.get("auto_kernel")
    for k in (g.get("kernels") or []):
        if k.get("kernel") == auto:
            it = k.get("decode_ns_iters") or []
            if it and g.get("decoded_bytes"):
                return g["decoded_bytes"] / min(it)
    return None


def best_rate_gb_s(c):
    """Best decode rate over EVERY byte-validated kernel in the cell, in GB/s.

    THE PAPER'S BASIS (sec:evaluation states it): every technique is reported at its best
    configuration for the column. Use this, not rate_gb_s (the shipped selector) and not
    gpu.best_decode_gib_s (production kernels only, so K but never T, B or S).

    Why the widest set is the fair one, and it is not a close call. The Decompression Engine is
    reported at best_decode_gib_s, which maximises over FOUR codec families crossed with FIVE
    chunk sizes -- best of twenty, and its best_ratio moves with the choice too. nvCOMP Zstd gets
    its level range. Handing every baseline its own sweep and then restricting ourselves to the
    twenty hand-written production kernels, which cannot even express T, B or S, would report a
    handicap rather than a result. The generated kernels are byte-validated on every leg exactly
    as the production ones are, and they are the entire evidence base for Section 4.

    Returns None when the cell timed no kernel, so callers can distinguish a gap from a zero.
    """
    g = (c or {}).get("gpu") or {}
    db = g.get("decoded_bytes")
    if not db:
        return None
    best = None
    for k in (g.get("kernels") or []):
        # VERIFIED AND APPLICABLE, both required. Every kernel entry carries these two flags and
        # this loop used to ignore them. On the paper's suite legs that changes nothing -- across
        # all 797 cells the unfiltered maximum never exceeds the filtered one, because the entries
        # that fail either flag carry no timings. On results/b300-campaign-0717's chunk sweep it
        # inflates by up to 3.5x, which is how it was found: 3844 GB/s on a column whose real best
        # is 1087. A rate that is not byte-exact is not a rate.
        if not (k.get("verified") and k.get("applicable")):
            continue
        it = k.get("decode_ns_iters") or []
        if it:
            v = db / min(it)
            if best is None or v > best:
                best = v
    return best


def tokens(c):
    return ((c or {}).get("gpu") or {}).get("distinct_codes")


def mean_len(c):
    """Token-weighted mean decoded bytes per code.

    The /2 is deliberate and stays on gpu.compressed_bytes: that array is exactly 2 B per code
    (the unpack), so dividing by 2 recovers the CODE COUNT. Do not "fix" this to on_disk_bytes
    the way ratio() was fixed -- on_disk_bytes includes the dictionary and sidecar and is
    bit-packed, so it does not carry a clean bytes-per-code factor."""
    if not c:
        return None
    comp = ((c.get("gpu") or {}).get("compressed_bytes")) or 0
    sb = c.get("sample_bytes")
    return (sb / (comp / 2)) if (comp and sb) else None


def frac_le8(c):
    return ((c or {}).get("gpu") or {}).get("frac_le8")


def ratio(c):
    """At-rest compression ratio: sample_bytes / on_disk_bytes.

    THE DENOMINATOR IS THE .vortex FILE, not gpu.compressed_bytes. Corrected 2026-08-22 after
    the field names misled an earlier version of this file. Measured on the B300, ClickBench URL
    at OnPair-12:

        on_disk_bytes         346,042,804   the file: bit-packed codes + dictionary + sidecar
        in_memory_bytes       346,039,324   the same arrays, less ~3.5 KB of file framing
        gpu.compressed_bytes  426,552,691   exactly 2.0001 B per code -- the in-memory UNPACK

    gpu.compressed_bytes widens 12-bit codes to u16 for the decode path, so dividing by it
    understated OnPair-12 by 17-33% (exactly 4/3 where codes dominate: 1.5 B at rest against
    2 B read) and overstated OnPair-16 by up to 12%, since it excludes the dictionary and
    sidecar that on_disk_bytes includes. A compression ratio is about data at rest.

    This matters beyond the table: fig_perf_real's dominance test puts these points against
    Zstd's raw_bytes/compressed_bytes and the DE's best_ratio, both of which ARE stored ratios.
    Using the unpack here compared us against baselines on a denominator we alone paid.

        CONTAINER-MATCHED WHERE THE CODEC AND ITS CONTAINER DIFFER. FSST-12 stores codes in its own
    fixed 12-bit packing, while OnPair's go through the same integer compressor as the rest of the
    Vortex array, which bit-packs to about log2(cardinality). Dividing by each technique's own
    stored size therefore compares FSST-12's CONTAINER against OnPair's CODEC: on a column with
    five distinct values it charged FSST-12 twelve bits per code and OnPair three. The cells carry
    mem_ratio_container_matched for exactly this, measured through OnPair's instrument, and no
    figure read it -- the decision was taken on 2026-08-12, applied to the ten-column generator,
    and lost when the fifteen-column one replaced it with this codec-agnostic helper. Effect on the
    real columns is 0-10%; on TPC-H l_shipinstruct it is 3.37x to 11.37x.
    """
    if not c:
        return None
    cm = c.get("mem_ratio_container_matched")
    if cm:
        return cm
    sb = c.get("sample_bytes")
    return (sb / at_rest_bytes(c)) if (at_rest_bytes(c) and sb) else None


def at_rest_bytes(c):
    """The stored size: on_disk_bytes, falling back to in_memory_bytes when nothing was written.

    The FSST-12 leg keeps its output in memory and reports on_disk_bytes = 0 and
    disk_ratio = 0.0, so on_disk_bytes alone would blank that codec's whole column. The fallback
    is sound because the two are the same arrays: across the OnPair cells, where both exist,
    on_disk_bytes exceeds in_memory_bytes by 3.3-5.0 KB of file framing, i.e. 0.001%. Both are
    the packed form; neither is gpu.compressed_bytes."""
    if not c:
        return 0
    return (c.get("on_disk_bytes") or 0) or (c.get("in_memory_bytes") or 0)


def offset_cost_rows(root, chip="b300", leg_chunk_bytes=None):
    """Rows of onpair_offset_cost.jsonl: the sidecar sweep, one record per chunk per granularity.

    Written by the ONPAIR_OFFSET_COST path during MATERIALIZE. Fields that matter here:
    dataset, column, bits, chunk, tok_per_batch, n_batches, total_tokens, decoded_bytes,
    compressed_bytes (the chunk's stored OnPair array) and offset_compressed_bytes (the sidecar
    through compress_offsets, the same delta-or-plain path the OnPair children take).

    SMOKE ROWS ARE DROPPED. Before 2026-08-26 the sink was exported ahead of phase 0, so
    onpair-bench.sh's 50 MB build smoke on tpch-sf10/l_comment appended fifteen records describing
    a cell no figure reads. They are separable by chunk size -- the smoke runs at 10 MB against the
    leg's 1000 -- and `leg_chunk_bytes` drops them; pass None to keep everything.
    """
    f = Path(root) / chip / "onpair_offset_cost.jsonl"
    if not f.exists():
        return []
    out = []
    for line in f.read_text().splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        out.append(r)
    if leg_chunk_bytes is not None:
        # The offset-cost record carries no chunk_bytes of its own; the smoke's signature is a
        # dataset id from the OLD ten-column corpus, which this suite does not contain.
        ids = {ds for _l, ds, _c in REAL + GEN}
        out = [r for r in out if r.get("dataset") in ids]
    return out


def sidecar_bytes(root, chip="b300", tok_per_batch=192):
    """{(dataset, column, bits): (sidecar_bytes, stored_bytes)} summed over chunks.

    Summed, not last-wins: a column is many chunks and each writes its own record. Keyed on the
    granularity because the footprint is not linear in it -- measured on this corpus, the sidecar
    runs about 0.44% of stored at 192, 0.53% at 128 and 1.85% at 32.
    """
    acc = {}
    for r in offset_cost_rows(root, chip, leg_chunk_bytes=True):
        if r.get("tok_per_batch") != tok_per_batch:
            continue
        k = (r["dataset"], r["column"], r["bits"])
        side, tot = acc.get(k, (0, 0))
        acc[k] = (side + r["offset_compressed_bytes"], tot + r["compressed_bytes"])
    return acc


def child_bytes(root, chip="b300"):
    """{(dataset, column, bits): {child: bytes}} summed over chunks, plus 'total'.

    From onpair_child_bytes.jsonl. This is what answers "what does the string part cost without
    the offsets" without guessing: `codes_offsets` is the row-to-code offset child, a separate
    Vortex array with its own integer encoding, and on short-row columns it is a large enough
    share of the total that a string-codec comparison including it is measuring offset compression.
    """
    acc = {}
    f = Path(root) / chip / "onpair_child_bytes.jsonl"
    if not f.exists():
        return acc
    ids = {ds for _l, ds, _c in REAL + GEN}
    for line in f.read_text().splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if r.get("dataset") not in ids:
            continue          # build-smoke row; see offset_cost_rows
        d = acc.setdefault((r["dataset"], r["column"], r["bits"]),
                           {k: 0 for k in ("codes", "codes_offsets", "dict_offsets",
                                           "lengths", "dict", "total")})
        for k in d:
            d[k] += r[k]
    return acc


def de_rows(root, chip="b300"):
    """Decompression-Engine cells, one per column, each with its chunk sweep and codec families.

    From COMPARATOR_SUITE where it exists: seven chunk sizes instead of five, on a u32-length-framed
    input rather than a flat concatenation with no row structure. Both changes move the Engine UP
    against us, and the second is the one that matters -- it was the only technique whose ratio was
    measured on a byte stream rows cannot be recovered from.
    """
    cr = comparator_root()
    if cr is not None and (cr / chip / "onpair_nvcomp_hw.json").exists():
        root = cr
    f = Path(root) / chip / "onpair_nvcomp_hw.json"
    try:
        return json.load(open(f))
    except (OSError, json.JSONDecodeError):
        return []


def coverage(root):
    """What actually landed. Figures print this so a gap is visible rather than inferred."""
    rep = {}
    for chip in CHIPS:
        d = Path(root) / chip
        if not d.is_dir():
            rep[chip] = {"present": False}
            continue
        tags = clock_tags(root, chip)
        rep[chip] = {
            "present": True,
            "clocks": tags,
            "onpair_cells": len(cells(root, chip, "boost", "onpair")),
            "fsst12_cells": len(cells(root, chip, "boost", "fsst12")),
            "de": len(de_rows(root, chip)),
            "complete": (Path(root) / chip / "suite-complete.txt").exists(),
        }
    return rep


# ============================================================================================
# BASELINE POINT SETS. One definition, shared by fig_perf_real (which plots them and asserts
# per-column dominance) and experiments/paper_claims.py (which derives the numbers the prose
# cites). They used to live only in the figure, so the reducer would have needed a second copy
# of the same extraction -- and two copies of one rule drifting apart is this repository's
# recurring defect, not a hypothetical one.
#
# Every point is (ratio, GB/s, label). Rate is raw min-of-N where the per-iteration timings
# survive, matching rate_gb_s() on our own side of the comparison, and falls back to the
# harness's decode_gib_s only when they do not. The two agree to a tenth of a GB/s wherever
# both exist, so the fallback is a completeness measure rather than a second basis.
# ============================================================================================
GIB_TO_GB = (2 ** 30) / 1e9

DE_NAME = {"DEFLATE-hi": "DE Deflate (5)", "DEFLATE-fast": "DE Deflate (0)",
           "LZ4": "DE LZ4", "Snappy": "DE Snappy"}


def _rate(entry, raw_bytes):
    """Decode rate in GB/s, over the STRING PAYLOAD rather than the file.

    The Decompression Engine used to be handed a flat concatenation of values with no separators,
    so its file and its payload were the same bytes and `raw_bytes` was an unambiguous numerator.
    It is now fed a u32-length-framed record stream -- the row structure every other technique
    already stored and it alone did not -- so the file is payload plus four bytes per row. Dividing
    by the file counts framing as decoded output: on a twelve-byte column that is a third of the
    reported rate, invented.

    `basis_bytes` is the numerator the producer itself used, per codec, and is preferred where
    present; `payload_bytes` is the same quantity at the top of the record. `raw_bytes` remains the
    file size and is the fallback for producers that predate the distinction -- for which the two
    coincide, because nothing was framed."""
    it = entry.get("decode_ns_iters") or []
    basis = entry.get("basis_bytes") or raw_bytes
    if it and basis:
        return basis / min(it)
    return (entry.get("decode_gib_s") or 0) * GIB_TO_GB or None


def _payload(row):
    """The string bytes in a producer record, whatever the file around them cost. See `_rate`."""
    return row.get("payload_bytes") or row.get("raw_bytes")


def _pareto(pts):
    """Drop points another point of the SAME baseline beats on both axes.

    A dominated configuration cannot move the frontier or the dominance verdict, and dropping it
    keeps the engine's twenty cells per column from becoming a cloud nobody would ship. This is
    the rule already applied by hand to the Zstd levels."""
    return [p for p in pts
            if not any(q[0] >= p[0] and q[1] >= p[1] and (q[0], q[1]) != (p[0], p[1])
                       for q in pts)]


def de_points(root, chip, ds, col):
    """The Decompression Engine's whole sweep for a column: four codecs by five chunk sizes.

    NOT best_codec/best_chunk_bytes alone. Those name the engine's FASTEST setting, so quoting
    only that mark drops its high-ratio half -- and that half is the interesting one. On Loghub
    Thunderbird, DEFLATE-hi at 512 KB stores 18.8x against OnPair-16's 5.2x, at 629 GB/s. It
    loses on rate, which is the claim; a test that never saw it was not testing the claim."""
    raw = []
    for r in de_rows(root, chip):
        if r.get("dataset_id") != ds or r.get("column") != col:
            continue
        passes = [(r.get("chunk_bytes"), r.get("codecs") or {})]
        passes += [(p.get("chunk_bytes"), p.get("codecs") or {})
                   for p in (r.get("chunk_sweep") or [])]
        seen = set()
        for chunk, codecs in passes:
            for name, e in codecs.items():
                if (name, chunk) in seen:
                    continue
                seen.add((name, chunk))
                if not e.get("valid") or e.get("validation_failed") or not e.get("ratio"):
                    continue
                rate = _rate(e, _payload(r))
                if rate:
                    raw.append((e["ratio"], rate, DE_NAME.get(name, "DE %s" % name)))
    return _pareto(raw)


def de_by_codec(root, chip, ds, col):
    """{raw codec name: best rate over that codec's chunk sweep, GB/s} for one column.

    The per-CODEC counterpart to de_points, which pools all four and returns the frontier. A
    figure drawing one line per codec needs them kept apart, and it wants each codec's own best
    chunk size rather than a chunk held fixed across four codecs whose optima differ. Keyed on the
    RAW harness name (DEFLATE-hi, DEFLATE-fast, LZ4, Snappy), not DE_NAME's display string, so a
    caller can look up its own colour and label without a reverse map."""
    out = {}
    for r in de_rows(root, chip):
        if r.get("dataset_id") != ds or r.get("column") != col:
            continue
        passes = [(r.get("chunk_bytes"), r.get("codecs") or {})]
        passes += [(p.get("chunk_bytes"), p.get("codecs") or {})
                   for p in (r.get("chunk_sweep") or [])]
        seen = set()
        for chunk, codecs in passes:
            for name, e in codecs.items():
                if (name, chunk) in seen:
                    continue
                seen.add((name, chunk))
                if not e.get("valid") or e.get("validation_failed"):
                    continue
                rate = _rate(e, _payload(r))
                if rate and rate > out.get(name, 0):
                    out[name] = rate
    return out


def zstd_points(zcells, ds, col):
    """The three nvCOMP Zstd levels for one column, from the OnPair-12 cell that carries them.

    The fields are decode_gib_s and compression_ratio. An earlier reader asked for
    decompress_gib_s and ratio, got None for both, and concluded the data had never been
    collected. It had."""
    c = zcells.get((ds, col, 12))
    out = []
    for e in (((c or {}).get("gpu") or {}).get("nvcomp_zstd") or []):
        # Only the reported levels. A leg may measure more; plotting whatever a leg happens to hold
        # would let the figure's baseline set change with the data rather than with a decision.
        if e.get("zstd_level") not in PAPER_ZSTD_LEVELS:
            continue
        if e.get("supported") and e.get("decode_gib_s") and e.get("compression_ratio"):
            out.append((e["compression_ratio"], e["decode_gib_s"] * GIB_TO_GB,
                        "Zstd (%s)" % e.get("zstd_level")))
    return _pareto(out)


def sw_points(sw, ds, col):
    """gANS and both Bitcomp variants for one column, from the MATERIALIZE+SW leg.

    NOT Pareto-filtered across the three. They are three distinct codecs -- an entropy coder
    and two Bitcomp modes -- so each is its own baseline, unlike the Engine's four codecs, which
    are four settings of one fixed-function unit and are pooled accordingly. Pooling these
    dropped Bitcomp-default from the figure entirely on every column, since gANS beats it on both
    axes, which left a legend entry with no mark behind it.

    EVERY CHUNK SIZE, not just the 256 KiB cell. This read only the top-level `codecs` block and
    its docstring asserted "each codec contributes one measured configuration per column, so there
    is nothing to filter within one" -- which was simply false: the producer records a five-size
    `chunk_sweep`, and de_points has always iterated the Engine's. So the fixed-function unit was
    plotted at its best of twenty configurations while the three software codecs were pinned to one
    of five, in a figure whose stated basis is "every technique at its best configuration on each
    column". It cost the baselines 4.4 to 13.9% and it cost them in our favour. Each codec is still
    reduced to its own best rather than pooled across the three, for the reason above.
    """
    row = sw.get((ds, col)) or {}
    passes = [row.get("codecs") or {}] + [p.get("codecs") or {}
                                          for p in (row.get("chunk_sweep") or [])]
    best = {}
    for codecs in passes:
        for name, e in codecs.items():
            if not e.get("supported") or not e.get("valid") or not e.get("ratio"):
                continue
            rate = _rate(e, _payload(row))
            if rate and rate > best.get(name, (0, 0))[1]:
                best[name] = (e["ratio"], rate)
    return [(r, rate, name) for name, (r, rate) in best.items()]


def baseline_points(root, chip, ds, col, zcells=None, sw=None):
    """Every baseline configuration measured for one column on one chip."""
    pts = de_points(root, chip, ds, col)
    if zcells is not None:
        pts += zstd_points(zcells, ds, col)
    if sw is not None:
        pts += sw_points(sw, ds, col)
    return pts
