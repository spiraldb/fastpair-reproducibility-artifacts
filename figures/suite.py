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
  ratio   sample_bytes / gpu.compressed_bytes -- the string bytes in against the bytes the GPU
          reads. This is the basis the committed tab:datasets already prints (FineWeb2 1.5x
          reproduces exactly) and the one its caption claims.
          NOT mem_ratio, which divides the in-memory Arrow representation -- data PLUS the
          offset array -- by the same denominator and so runs 15-25% HIGHER (FineWeb2 1.99 vs
          1.49), reaching +57% on l_shipinstruct, whose five distinct values make the offsets
          dominate. mem_ratio is defensible for a different question, but it is the flattering
          one here, so a table that mixes the two would overstate compression.
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
    """Token-weighted mean decoded bytes per code. Codes are u16, so compressed/2 is the count."""
    if not c:
        return None
    comp = ((c.get("gpu") or {}).get("compressed_bytes")) or 0
    sb = c.get("sample_bytes")
    return (sb / (comp / 2)) if (comp and sb) else None


def frac_le8(c):
    return ((c or {}).get("gpu") or {}).get("frac_le8")


def ratio(c):
    """sample_bytes / compressed_bytes. See the module docstring on why not mem_ratio."""
    if not c:
        return None
    comp = ((c.get("gpu") or {}).get("compressed_bytes")) or 0
    sb = c.get("sample_bytes")
    return (sb / comp) if (comp and sb) else None


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
