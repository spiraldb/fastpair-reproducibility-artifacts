# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""Generate the LaTeX body of the paper's tab:datasets from results/.

tab:datasets was hand-maintained with no generator, which made it the one place in the paper
where a number could drift from results/ without `make verify` noticing. Every cell it prints
IS derivable, so this emits the table body and experiments/validate.py asserts the derived
values against the ones the paper prints.

    uv run figures/tab_datasets.py            # LaTeX rows to stdout
    uv run figures/tab_datasets.py --check    # diff against the committed values, exit 1 on drift

COLUMN DEFINITIONS, recovered from the committed data (the caption states them in words;
these are the reductions that reproduce every printed cell):

  Tokens  gpu.distinct_codes    -- distinct codes the trained dictionary actually uses, of
                                   the 4,096 / 65,536 available.
  Len     sample_bytes / (gpu.compressed_bytes / 2)
                                -- mean DECODED bytes per code, token-weighted. Codes are
                                   stored as u16, so compressed_bytes/2 is the code count.
                                   NOT gpu.dict_mean_len, which is the unweighted mean over
                                   dictionary entries and runs ~25% higher (FineWeb: 4.30 vs
                                   the printed 3.4). Mixing the two silently overstates Len.
  <=8B    gpu.frac_le8          -- fraction of decoded codes whose token is at most 8 bytes,
                                   the quantity the split dictionary exploits.
  Ratio   mem_ratio             -- includes the output-offset sidecar.

FSST-12's ratio is mem_ratio_container_matched, the basis that puts it through the same
container as OnPair's codes. FSST-12 has no Tokens/Len entry: its table is a fixed 4,096
entries and all its symbols are <=8 bytes, but the committed data records neither its used-token
count nor its mean code length, so those cells stay empty rather than being invented.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

# (printed label, onpair summary file, column, group). Order is the table's.
ROWS = [
    ("TPC-H \\texttt{l\\_comment}",      "tpch-sf10", "l_comment",      "Synthetic"),
    ("TPC-H \\texttt{ps\\_comment}",     "tpch-sf10", "ps_comment",     "Synthetic"),
    ("TPC-H \\texttt{l\\_shipinstruct}", "lship",     "l_shipinstruct", "Synthetic"),
    ("synthetic URL",                    "synthetic", "url",            "Synthetic"),
    ("ClickBench URL",                   "clickbench", "URL",           "Real"),
    ("FineWeb",                          "fineweb",   "text",           "Real"),
    ("Wikipedia",                        "wikipedia", "text",           "Real"),
    ("Amazon Books",                     "book-reviews", "text",        "Real"),
    ("Amazon Movies\\,\\&\\,TV",         "amazon-movies", "text",       "Real"),
    ("Amazon Electronics",               "amazon-electronics", "text",  "Real"),
]

# FSST-12 keys its l_shipinstruct cell under tpch-sf10, because `lship` does not resolve as a
# dataset alias in that job. Same column, different key.
FSST_KEY = {"lship": "tpch-sf10"}


def onpair_stats(fn, col, bits):
    c = C.cell("b300", fn, col, bits)
    if not c:
        return None
    g = c.get("gpu") or {}
    cb = g.get("compressed_bytes")
    sb = c.get("sample_bytes")
    return {
        "tokens": g.get("distinct_codes"),
        "len": (sb / (cb / 2)) if (sb and cb) else None,
        "le8": g.get("frac_le8"),
        "ratio": c.get("mem_ratio"),
    }


def fsst_ratio(fn, col):
    c = C.cell("b300", FSST_KEY.get(fn, fn), col, 12, C.FSST12)
    return c.get("mem_ratio_container_matched") if c else None


def emit():
    out, group = [], None
    for label, fn, col, grp in ROWS:
        if grp != group:
            group = grp
            out.append("\\multicolumn{12}{@{}l}{\\textit{%s}} \\\\" % grp)
        a, b = onpair_stats(fn, col, 12), onpair_stats(fn, col, 16)
        f = fsst_ratio(fn, col)
        if not a or not b:
            out.append("%% MISSING DATA: %s" % label)
            continue
        cells = []
        for s in (a, b):
            cells.append("%s & %.1f & %.0f\\%% & %.1f$\\times$" % (
                "{:,}".format(s["tokens"]).replace(",", "\\,"), s["len"], s["le8"] * 100, s["ratio"]))
        out.append("%s & %s & & %s & & %s \\\\" % (
            label, cells[0], cells[1], ("%.1f$\\times$" % f) if f else "--"))
    return "\n".join(out)


# What the paper currently prints, for --check. Keyed (fn, col, bits) -> (tokens, len, le8%, ratio),
# plus ("fsst", fn, col) -> ratio. Tolerances are half a printed unit in the last place.
PRINTED = {
    ("tpch-sf10", "l_comment", 12): (3859, 7.7, 58, 4.1),
    ("tpch-sf10", "l_comment", 16): (65305, 10.4, 33, 4.2),
    ("tpch-sf10", "ps_comment", 12): (3869, 10.1, 33, 6.2),
    ("tpch-sf10", "ps_comment", 16): (65243, 12.7, 16, 5.8),
    ("lship", "l_shipinstruct", 12): (5, 9.6, 40, 11.0),
    ("lship", "l_shipinstruct", 16): (5, 9.6, 40, 11.0),
    ("synthetic", "url", 12): (160, 12.1, 14, 9.6),
    ("synthetic", "url", 16): (158, 11.9, 18, 9.6),
    ("clickbench", "URL", 12): (4016, 4.7, 81, 2.9),
    ("clickbench", "URL", 16): (64624, 8.5, 51, 3.8),
    ("fineweb", "text", 12): (4042, 3.4, 99, 2.2),
    ("fineweb", "text", 16): (65457, 5.7, 82, 2.9),
    ("wikipedia", "text", 12): (4048, 3.3, 98, 2.2),
    ("wikipedia", "text", 16): (65389, 5.6, 82, 2.8),
    ("book-reviews", "text", 12): (4047, 3.9, 96, 2.6),
    ("book-reviews", "text", 16): (65466, 6.7, 72, 3.3),
    ("amazon-movies", "text", 12): (4043, 3.8, 96, 2.5),
    ("amazon-movies", "text", 16): (65464, 6.6, 73, 3.2),
    ("amazon-electronics", "text", 12): (4048, 4.2, 95, 2.7),
    ("amazon-electronics", "text", 16): (65471, 7.1, 68, 3.4),
}
PRINTED_FSST = {
    ("tpch-sf10", "l_comment"): 2.9, ("tpch-sf10", "ps_comment"): 3.8,
    ("lship", "l_shipinstruct"): 11.4, ("synthetic", "url"): 3.4,
    ("clickbench", "URL"): 2.1, ("fineweb", "text"): 1.8, ("wikipedia", "text"): 1.8,
    ("book-reviews", "text"): 1.9, ("amazon-movies", "text"): 1.9,
    ("amazon-electronics", "text"): 2.0,
}


def check():
    bad = []
    for (fn, col, bits), (tok, ln, le8, ratio) in PRINTED.items():
        s = onpair_stats(fn, col, bits)
        if not s:
            bad.append("%s/%s b%d: NO DATA" % (fn, col, bits))
            continue
        if s["tokens"] != tok:
            bad.append("%s/%s b%d tokens: table %s, data %s" % (fn, col, bits, tok, s["tokens"]))
        if abs(s["len"] - ln) > 0.05:
            bad.append("%s/%s b%d Len: table %.1f, data %.2f" % (fn, col, bits, ln, s["len"]))
        if abs(s["le8"] * 100 - le8) > 0.5:
            bad.append("%s/%s b%d <=8B: table %d%%, data %.1f%%" % (fn, col, bits, le8, s["le8"] * 100))
        if abs(s["ratio"] - ratio) > 0.05:
            bad.append("%s/%s b%d Ratio: table %.1f, data %.2f" % (fn, col, bits, ratio, s["ratio"]))
    for (fn, col), r in PRINTED_FSST.items():
        got = fsst_ratio(fn, col)
        if got is None:
            bad.append("%s/%s FSST-12: NO DATA" % (fn, col))
        elif abs(got - r) > 0.05:
            bad.append("%s/%s FSST-12 Ratio: table %.1f, data %.2f" % (fn, col, r, got))
    if bad:
        print("tab:datasets DRIFT -- %d cell(s) disagree with results/:" % len(bad))
        for b in bad:
            print("  " + b)
        return 1
    print("tab:datasets: all %d cells re-derive from results/ ✓" % (len(PRINTED) * 4 + len(PRINTED_FSST)))
    return 0


if __name__ == "__main__":
    sys.exit(check() if "--check" in sys.argv else (print(emit()) or 0))
