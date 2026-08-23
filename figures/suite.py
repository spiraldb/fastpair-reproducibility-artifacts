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
CHIPS = ["b300", "h100", "a100", "l40s"]     # fixed order; absent chips still get a legend slot


def latest_root(suite_id=None):
    """The suite directory to read. Explicit id wins; otherwise the newest results/suite-*."""
    if suite_id:
        p = RESULTS / (suite_id if suite_id.startswith("suite-") else f"suite-{suite_id}")
        return p if p.is_dir() else None
    cands = sorted(RESULTS.glob("suite-*"), key=lambda p: p.name)
    return cands[-1] if cands else None


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
    """Every cell for a chip at one clock state, keyed by (dataset_id, column, bits)."""
    prefix = {"onpair": "sweep_summary", "fsst12": "fsst12_summary",
              "zstd": "zstd_summary"}[codec]
    out = {}
    for c in _cells(root, chip, prefix, tag):
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
    Using the unpack here compared us against baselines on a denominator we alone paid."""
    if not c:
        return None
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


def de_rows(root, chip="b300"):
    """Decompression-Engine cells, one per column, each with its chunk sweep and codec families."""
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
