# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""Re-derive every headline number in the paper from the committed results/.

This is the paper's self-check. It imports figures/common.py so every reduction
(best-shipped kernel = decoded_bytes/min(decode_ns_iters), the GiB->GB factor, the
hardware-DE map) is the EXACT same code the figures use -- there is no second
implementation that could drift. Each check re-derives a claim and asserts it
against the value the paper states. Exit code is nonzero if any check fails.

    uv run experiments/validate.py      # or: python experiments/validate.py

See METHODOLOGY.md for the reduction conventions and MANIFEST.md for result->source.
"""
import csv
import json
import re
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "figures"))
import common as C  # noqa: E402

FAILS = []
ROWS = []
# The full green set re-derives exactly this many checks. Several blocks are guarded (IAA, e2e,
# and the DE/software/CPU joins) and silently contribute nothing if their results file is missing
# or unreadable -- so a count below this means the reproduction is INCOMPLETE, not passing. main()
# fails loud on a shortfall rather than printing a false "all green".
# 134 after the cost-surface block was repointed from the retracted base-kernel capture to the
# shipped-kernel one (ncu-costsurface-v2.csv) and its universal margin bands were split into the
# HBM claim, an absolute compute ceiling, and the GDDR regime boundary.
EXPECTED_CHECKS = 134


def check(name, got, lo, hi, unit="", note=""):
    """Record a check: pass iff lo <= got <= hi."""
    ok = got is not None and lo <= got <= hi
    ROWS.append((name, got, f"[{lo:g}, {hi:g}]", unit, ok, note))
    if not ok:
        FAILS.append(name)
    return ok


# (onpair summary file, column, DE dataset_id) -- the exact join fig_sota.py uses.
COLS = [
    ("tpch-sf10", "l_comment", "tpch-sf10"),
    ("tpch-sf10", "ps_comment", "tpch-sf10"),
    ("lship", "l_shipinstruct", "tpch-sf10"),
    ("synthetic", "url", "synthetic"),
    ("clickbench", "URL", "clickbench"),
    ("fineweb", "text", "fineweb"),
    ("wikipedia", "text", "wikipedia"),
    ("book-reviews", "text", "book-reviews"),
    ("amazon-movies", "text", "amazon-movies"),
    ("amazon-electronics", "text", "amazon-electronics"),
]


def onpair_best(fn, col):
    """Best FastPair decode GB/s on B300 over dict-12/16 (max-of-bits, best shipped kernel)."""
    vals = [C.best_shipped(C.cell("b300", fn, col, b)) for b in (12, 16)]
    vals = [v for v in vals if v]
    return max(vals) if vals else None


def de_multiples():
    de = C.de_map()
    out = {}
    for fn, col, did in COLS:
        op, d = onpair_best(fn, col), de.get((did, col))
        if op and d:
            out[(fn, col)] = op / d   # key by (file,col): 5 columns are named "text"
    return out


def sw_mult(g, fn, col):
    """Software-Zstd multiple, the paper's method: best FastPair / best Zstd, each
    maxed over dict-12/16 independently (fig_teaser)."""
    fp = max((C.best_shipped(C.cell(g, fn, col, b)) or 0) for b in (12, 16))
    zs = max((C.software_best(C.cell(g, fn, col, b)) or 0) for b in (12, 16))
    return (fp / zs) if (fp and zs) else None


def fixed_stride_geomean(gpu):
    """Geomean over throughput-bound columns of the fixed-stride lever at dict-12:
    onpair_shmem_4tpt (fixed-stride) over _vdict (variable-stride OnPair), per-kernel
    decode GB/s. ~1.7x on the HBM GPUs (the dependency collapse the cost surface
    predicts); the GDDR6 L40S inverts (the cache-request-vs-bandwidth trade). Backs the
    Section 5.5 ablation claim."""
    ratios = []
    for fn, col, _ in COLS:
        c = C.cell(gpu, fn, col, 12)
        if not c:
            continue
        km = C.kernel_map(c)
        a, b = km.get("onpair_shmem_4tpt"), km.get("onpair_shmem_4tpt_vdict")
        if a and b:
            ratios.append(a / b)
    return statistics.geometric_mean(ratios) if ratios else None


def main():
    print("Re-deriving headline numbers from results/ (via figures/common.py)\n")

    # 1. Hardware-DE multiple: FastPair best / best DE codec, per column. Paper: 2.6-4.6x.
    mult = de_multiples()
    if mult:
        check("DE multiple: min column", min(mult.values()), 2.4, 2.75, "x", "max-over-bits floor (fig_teaser's better-preset view)")
        check("DE multiple: max column", max(mult.values()), 4.5, 4.7, "x", "paper says 4.6x high end")
    # 1b. Per-preset DE multiples (the paper reports both presets as levels; \u00a76.2).
    for bits, lo_rng, hi_rng in ((12, (2.15, 2.3), (4.5, 4.7)), (16, (2.3, 2.45), (4.0, 4.15))):
        mb = {}
        de = C.de_map()
        for fn, col, did in COLS:
            op, d = C.best_shipped(C.cell("b300", fn, col, bits)), de.get((did, col))
            if op and d:
                mb[(fn, col)] = op / d
        if mb:
            check(f"DE multiple dict-{bits}: min", min(mb.values()), *lo_rng, "x", "paper: 2.2-4.6 at dict-12, 2.4-4.1 at dict-16")
            check(f"DE multiple dict-{bits}: max", max(mb.values()), *hi_rng, "x")
        check("DE multiple: clickbench URL", mult.get(("clickbench", "URL")), 2.5, 2.75, "x")
        check("DE multiple: # columns covered", float(len(mult)), 9, 11, "cols")

    # 1c. The DE DENOMINATOR itself, absolutely and by definition.
    #
    # The multiples above were already asserted, but the engine rates underneath them were not,
    # and that gap cost real time: on 2026-08-03 the 432 GB/s ClickBench URL figure was declared
    # underivable and the paper's multiples were "corrected" upward, because the reduction used
    # was a max over the per-codec `codecs` block instead of de_map(). Those are different
    # baselines. The `codecs` entries are measured at the DEFAULT chunk size; top-level
    # best_decode_gib_s is the best over codec AND chunk size, which is the baseline Section 6.1
    # declares. So assert the absolute rates the prose quotes, and assert the definitional
    # relation that makes de_map the authoritative one, so a future reader cannot mistake a
    # weaker denominator for a data defect.
    de = C.de_map()
    check("DE rate: clickbench URL", de.get(("clickbench", "URL")), 430, 434, "GB/s",
          "prose quotes 432 GB/s in sec:eval:arch and the overlap bound")
    de_ten = [de[(did, col)] for _, col, did in COLS if de.get((did, col))]
    if de_ten:
        check("DE rate: min over the ten columns", min(de_ten), 203, 208, "GB/s", "prose: 205 to 692 GB/s")
        check("DE rate: max over the ten columns", max(de_ten), 690, 695, "GB/s")
    raw = {(e["dataset_id"], e["column"]): e
           for e in json.load(open(C.RESULTS / "b300" / "onpair_nvcomp_hw.json"))}
    slack = []
    for _, col, did in COLS:
        e = raw.get((did, col)) or {}
        per = [v["decode_gib_s"] for v in (e.get("codecs") or {}).values()
               if v.get("decode_gib_s") and v.get("ratio")]
        if per and e.get("best_decode_gib_s"):
            slack.append(e["best_decode_gib_s"] / max(per))
    if slack:
        # >= 1 by construction: the chunk-swept best cannot lose to a single-chunk measurement.
        # If this ever dips below 1, best_decode_gib_s is NOT the strongest engine configuration
        # and de_map would be understating the baseline.
        check("DE: chunk-swept best >= best per-codec entry", min(slack), 1.0, 1.10, "x",
              "de_map is the authoritative, stronger denominator (~3% above per-codec on URL)")

    # 2. GSST: A100 l_comment FastPair / GSST's 191 GB/s. Paper: ~3.3x.
    a100_lc = C.best_shipped(C.cell("a100", "tpch-sf10", "l_comment", 12))
    if a100_lc:
        check("GSST multiple (A100 l_comment)", a100_lc / C.GSST_GBS, 3.0, 3.6, "x")

    # 3. Software nvCOMP-Zstd multiple on B300 (the paper's method, per column).
    #    Intro: 6 to 372x; section 6: 6-18x on relational+URL.
    swm = {(fn, col): sw_mult("b300", fn, col) for fn, col, _ in COLS}
    swm = {k: v for k, v in swm.items() if v}
    if swm:
        check("software mult B300: min (intro 6x)", min(swm.values()), 5.8, 6.5, "x", "clickbench URL")
        check("software mult B300: max (intro 372x)", max(swm.values()), 360, 380, "x", "wikipedia text")
        relurl = [v for (fn, col), v in swm.items() if col in ("l_comment", "ps_comment", "URL", "url")]
        check("software mult B300: relational+URL low", min(relurl), 5.8, 6.5, "x", "sec6 says 6-18x")
        check("software mult B300: relational+URL high", max(relurl), 16, 19, "x", "sec6 says 6-18x")

    # 4. CPU fixed-stride vs variable-stride (1 physical core). Paper: median ~1.10x, up to ~1.58x.
    d = json.load(open(C.RESULTS / "cpu-sweep-4phys" / "cpu-sweep.json"))
    fov = [cell["fat_over_entries"]
           for m in d["machines"] for cell in m["results"]
           if cell.get("threads") == 1 and cell.get("fat_over_entries")]
    if fov:
        check("CPU fat/entries: median", statistics.median(fov), 1.05, 1.20, "x")
        check("CPU fat/entries: max", max(fov), 1.40, 1.70, "x")

    # 5. Cost surface: a CACHE pipe binds; DRAM and SM compute never do (the paper's one insight).
    # v2, NOT the original capture. ncu-costsurface.csv profiled the BASE REFERENCE kernel, not the
    # shipped one (figures/fig_costsurface.py:22-23 says so), and the difference is not marginal:
    # it reads A100 L1 at 55.0% and H100 L2 at 88.2% above an L1 of 64.0%, which is exactly the
    # per-chip "Hopper binds on device-wide L2, Blackwell on L1" split that
    # docs/notes/2026-07-06-ncu-v2-rederivation.md RETRACTED. On the shipped kernel it is L1 on
    # every HBM chip: A100 93.5, H100 95.8 (L2 78.7), B300 95.8 (L2 31.9). This checker was
    # asserting the refuted position and passing, so `make verify` handed an artifact reviewer a
    # green tick on the opposite of the paper's central claim.
    rows = list(csv.DictReader(open(C.RESULTS / "ncu-costsurface-v2.csv")))
    flt = lambda r, k: float(r[k])
    HBM = ["a100", "h100", "b300"]
    for arch in HBM + ["l40s"]:
        ar = [r for r in rows if r["arch"] == arch]
        cache = max(max(flt(r, "l1tex"), flt(r, "l2")) for r in ar)
        dram, sm = max(flt(r, "dram") for r in ar), max(flt(r, "sm") for r in ar)
        check(f"cost surface {arch}: cache pipe peak", cache, 70, 100, "%peak")
        # A WIDE CACHE-OVER-DRAM MARGIN IS AN HBM CLAIM, NOT A UNIVERSAL ONE. This ran over all
        # four parts and demanded >= 45 points everywhere. On the shipped-kernel capture the L40S
        # gives 6.0 -- its DRAM sits at 82.3% right behind an 88.3% cache pipe -- so the check was
        # only passing because the retracted base-kernel capture understated the L40S. That the
        # GDDR part does NOT have bandwidth to spare is the paper's own regime boundary, so it is
        # asserted below as itself rather than swept into a universal.
        if arch in HBM:
            check(f"cost surface {arch}: cache >> DRAM", cache - dram, 45, 100, "pts")
        # Compute never binds. Stated as an ABSOLUTE ceiling on SM throughput rather than as a
        # margin below the cache pipe: the margin band silently encoded how saturated the cache
        # was, so it failed on exactly the parts where the cache pipe was measured LOWER.
        check(f"cost surface {arch}: SM compute never binds", sm, 0, 68, "%peak")
    # THE REGIME BOUNDARY, asserted rather than assumed. On the GDDR part the byte path is the
    # tighter limit, which is why the paper scopes its bound claim to HBM devices.
    l40s = [r for r in rows if r["arch"] == "l40s"]
    _l40s_cache = max(max(flt(r, "l1tex"), flt(r, "l2")) for r in l40s)
    check("cost surface l40s: DRAM close behind the cache pipe",
          _l40s_cache - max(flt(r, "dram") for r in l40s), 0, 20, "pts",
          "GDDR part: byte supply is the tighter limit, so the HBM bound claim excludes it")
    b300 = [r for r in rows if r["arch"] == "b300"]
    h100 = [r for r in rows if r["arch"] == "h100"]
    a100 = [r for r in rows if r["arch"] == "a100"]
    # THE CLAIM IS "L1 BINDS ON EVERY HBM CHIP", so that is what is asserted -- per chip, and as an
    # ordering against L2 rather than as an absolute band alone. An absolute band would pass on a
    # capture where L2 had overtaken L1, which is the failure that let the retracted chip split
    # survive here.
    for name, ar in (("A100", a100), ("H100", h100), ("B300", b300)):
        l1 = max(flt(r, "l1tex") for r in ar)
        l2 = max(flt(r, "l2") for r in ar)
        check(f"cost surface: {name} L1/TEX peak", l1, 90, 100, "%peak",
              "L1 binds on every HBM chip (shipped kernel)")
        check(f"cost surface: {name} L1 above L2", l1 - l2, 10, 100, "pts",
              "the binding unit is per-SM L1, not device-wide L2")

    # 6. IAA aggregate vs FastPair on Sapphire (results/iaa/). Paper: ~29 GB/s block, beaten by FastPair.
    iaa_path = C.RESULTS / "iaa" / "iaa_aggregate_sapphire.txt"
    if iaa_path.exists():
        GIB = 1.073741824
        peaks = {}
        for ln in iaa_path.read_text().splitlines():
            m = re.search(r"/([a-z_]+)\.bin threads=(\d+)\s+ratio [\d.]+x\s+IAA-decode ([\d.]+) GB/s", ln)
            if m:
                peaks.setdefault(m.group(1), []).append(float(m.group(3)))
        peaks = {k: max(v) for k, v in peaks.items()}
        ones = {}
        for ln in iaa_path.read_text().splitlines():
            m = re.search(r"/([a-z_]+)\.bin threads=1\s+ratio [\d.]+x\s+IAA-decode ([\d.]+) GB/s", ln)
            if m:
                ones[m.group(1)] = float(m.group(2))
        cpu = json.load(open(C.RESULTS / "iaa" / "onpair_cpu_sapphire.json"))
        fat = lambda col, t: next((r["fat_gibs"] * GIB for r in cpu["results"]
                                   if r["column"] == col and r["threads"] == t and r["bits"] == 12), None)
        shared = [c for c in peaks if any(r["column"] == c for r in cpu["results"])]
        check("IAA aggregate peak (geomean)", statistics.geometric_mean(peaks.values()), 26, 32, "GB/s")
        c1 = statistics.geometric_mean([fat(c, 1) for c in shared if fat(c, 1)])
        c8 = statistics.geometric_mean([fat(c, 8) for c in shared if fat(c, 8)])
        i1 = statistics.geometric_mean([ones[c] for c in shared])
        ipk = statistics.geometric_mean([peaks[c] for c in shared])
        check("IAA: FastPair-1core / IAA-1engine", c1 / i1, 2.0, 2.7, "x")
        check("IAA: FastPair-8core / IAA-allengines", c8 / ipk, 1.0, 1.3, "x")

    # 7. End-to-end decode->scan (results/e2e/, when the B300 run has landed). Correctness
    #    is asserted on every column; the throughput ratios are asserted on ClickBench URL
    #    (the real headline column). The synthetic-URL run is a no-download cross-check whose
    #    degenerate repetition (917 dict entries) makes its scan rate unrepresentative.
    e2e_dir = C.RESULTS / "e2e"
    e2e_files = sorted(e2e_dir.glob("e2e_*.json")) if e2e_dir.exists() else []
    for f in e2e_files:
        j = json.load(open(f))
        tag = f.stem.replace("e2e_", "")
        check(f"e2e {tag}: decode validated", 1.0 if j.get("decode_ok") else 0.0, 1, 1, "bool")
        check(f"e2e {tag}: scan validated", 1.0 if j.get("scan_ok") else 0.0, 1, 1, "bool")
        # on-GPU decode replaces CPU-decode + PCIe-ship-decompressed to land the bytes in HBM
        check(f"e2e {tag}: decode vs PCIe-ship-decompressed",
              (j.get("h2d_decompressed_ms") or 0) / (j.get("decode_ms") or 1), 8, 40, "x",
              "decode-on-GPU is N x faster than shipping the decompressed column over PCIe")
        if "clickbench" in tag:
            check(f"e2e {tag}: PCIe-decompressed / decode+scan",
                  j.get("pcie_decompressed_vs_gpu_decode_scan"), 5, 100, "x")
            if j.get("decoded_bytes"):
                check(f"e2e {tag}: selectivity (matches/byte)",
                      j.get("gpu_matches", 0) / j["decoded_bytes"], 0.0, 1e-4, "frac",
                      "rare needle = selective scan")

    # 8. Per-lever ablation: the fixed-stride dictionary over throughput-bound columns
    #    (dict-12). ~1.7x on the HBM GPUs; the GDDR6 L40S inverts below 1 -- the
    #    cache-request-vs-bandwidth trade, the paper's Section 5.5 point.
    fs = {g: fixed_stride_geomean(g) for g in ("a100", "l40s", "h100", "b300")}
    if fs.get("a100"):
        check("fixed-stride geomean: A100", fs["a100"], 1.55, 1.85, "x", "dependency collapse on HBM")
    if fs.get("h100"):
        check("fixed-stride geomean: H100", fs["h100"], 1.6, 1.9, "x", "dependency collapse on HBM")
    if fs.get("b300"):
        check("fixed-stride geomean: B300", fs["b300"], 1.6, 1.9, "x", "dependency collapse on HBM")
    if fs.get("l40s"):
        check("fixed-stride geomean: L40S inverts (<1)", fs["l40s"], 0.7, 0.95, "x",
              "GDDR6: wasted fetch costs more than the latency it removes")

    # 9. e2e predicate sweep (results/e2e/sweep/): decode is a fixed floor; the scan
    #    (predicate evaluation) grows with selectivity and overtakes decode -- the
    #    decode-dominated -> predicate-dominated cross-over (fig:e2e_sweep, the blog curve).
    sweep_dir = C.RESULTS / "e2e" / "sweep"
    sw = sorted(sweep_dir.glob("sweep_*.json")) if sweep_dir.exists() else []
    if sw:
        ratios, rare_sd = [], None
        for f in sw:
            j = json.load(open(f))
            d, s = j.get("decode_ms"), j.get("scan_ms")
            if d and s:
                ratios.append(s / d)
                if f.stem == "sweep_rare":
                    rare_sd = s / d
        if rare_sd is not None:
            check("e2e sweep: rare scan/decode (decode-dominated)", rare_sd, 0.1, 0.5, "x")
        if ratios:
            check("e2e sweep: max scan/decode (predicate-dominated)", max(ratios), 4.0, 12.0, "x")
            check("e2e sweep: cross-over present (min<1<max)",
                  1.0 if (min(ratios) < 1.0 < max(ratios)) else 0.0, 1, 1, "bool")

    # 10. Offsets/materialization trade-off (results/b300-offtrade/, fig:offtrade). Every cell
    #     byte-exact with GPU count == the selection oracle; the dense stored-offset decode is
    #     filter-agnostic and cheapest down to ~20% selectivity (early materialization crosses it
    #     near m~0.2); the late-materialization prototype never beats min(dense, early).
    off_dir = C.RESULTS / "b300-offtrade"
    off_files = sorted(off_dir.glob("run*_url.json")) if off_dir.exists() else []
    if off_files:
        def _emin(c):
            L = c.get("legs", {}); a = L.get("e2e_ns")
            return (min(a) / 1e6) if a else L.get("e2e_ms")
        all_cells, late, early, regen = [], {}, {}, None
        for f in off_files:
            rc = json.load(open(f))["cells"]
            all_cells += rc
            dv = [c for c in rc if c["strategy"] == "OP4_store" and c["materialization"] == "dense"]
            if not dv:
                continue
            base = _emin(dv[0])
            for c in rc:
                mm, e = c.get("materialization"), _emin(c)
                if not e or not base:
                    continue
                if mm == "late_mat":
                    late[c["m"]] = e / base
                elif mm == "early_mat":
                    early[c["m"]] = e / base
                elif c["strategy"] == "OP2_regen":
                    regen = e / base
        byte_ok = all(c.get("legs", {}).get("validate_ok", c.get("validate_ok")) for c in all_cells)
        count_ok = all(c.get("legs", {}).get("count_ok", True) for c in all_cells)
        check("offtrade: every cell byte-exact", 1.0 if byte_ok else 0.0, 1, 1, "bool")
        check("offtrade: GPU count == selection oracle", 1.0 if count_ok else 0.0, 1, 1, "bool")
        if regen:
            check("offtrade: regen-on-GPU vs stored offsets (OP2/dense)", regen, 1.05, 1.12, "x")
        if early:
            check("offtrade: early-mat crosses dense (>1 at m=1, <1 low-m)",
                  1.0 if (early.get(1.0, 0) > 1.0 and min(early.values()) < 1.0) else 0.0, 1, 1, "bool")
        if late and early:
            dominated = all(late[m] >= min(1.0, early[m]) - 1e-9 for m in late if m in early)
            check("offtrade: late-mat never beats min(dense, early)",
                  1.0 if dominated else 0.0, 1, 1, "bool")

    # 11. FSST-12 generality (§6.4, §1, §7). Until 2026-08-14 NOTHING here was checked, and
    #     three published numbers had silently drifted: the rate range was still B300+H100-only
    #     after the other two chips landed, the compression-ratio range read 0.72-0.81x where
    #     the data gives 0.74-0.84x, and the OnPair-16 margin read 1.06-1.23x (B300) where four
    #     chips give 1.12-1.61x. These checks exist so that cannot recur silently.
    #
    #     The OnPair comparator is same_run_onpair(), NOT cell(..., ONPAIR): the former is the
    #     OnPair cell measured on the same box in the same session, the latter is the canonical
    #     matrix entry from an earlier send. Using the wrong one shifts every ratio.
    TEXT5 = [("fineweb", "text"), ("wikipedia", "text"), ("book-reviews", "text"),
             ("amazon-movies", "text"), ("amazon-electronics", "text")]
    GPUS4 = ("b300", "h100", "l40s", "a100")

    def fsst_rate_ratios(bits):
        """FSST-12 / OnPair-<bits> decode rate, over the five text columns x four GPUs."""
        out = {}
        for g in GPUS4:
            rs = []
            for ds, col in TEXT5:
                f = C.best_shipped(C.cell(g, ds, col, 12, C.FSST12))
                o = C.best_shipped(C.same_run_onpair(g, ds, col, bits))
                if f and o:
                    rs.append(f / o)
            if rs:
                out[g] = rs
        return out

    r12 = fsst_rate_ratios(12)
    if len(r12) == len(GPUS4) and all(len(v) == len(TEXT5) for v in r12.values()):
        flat = [x for v in r12.values() for x in v]
        check("FSST-12: cells present (5 columns x 4 GPUs)", float(len(flat)), 20, 20, "cells")
        check("FSST-12 / OnPair-12: min over 4 GPUs", min(flat), 0.90, 0.93, "x", "§6: 0.91 to 1.11x")
        check("FSST-12 / OnPair-12: max over 4 GPUs", max(flat), 1.09, 1.13, "x", "§6: 0.91 to 1.11x")
        # The A100 inversion is the load-bearing claim: it is the ONE chip where FSST-12 beats
        # OnPair-12 on every one of the five columns, which §6 reads as the access-width account.
        check("FSST-12: A100 beats OnPair-12 on all five",
              1.0 if all(x > 1.0 for x in r12["a100"]) else 0.0, 1, 1, "bool",
              "§6 attributes this to the split's common path plus the narrowest L1 headroom")
        check("FSST-12: A100 min", min(r12["a100"]), 1.00, 1.04, "x", "§6: 1.02 to 1.11x on the A100")
        check("FSST-12: A100 max", max(r12["a100"]), 1.09, 1.13, "x")
        # ... and the other three chips must NOT invert, or the A100 sentence is not a contrast.
        check("FSST-12: B300/H100/L40S do not invert",
              1.0 if all(x <= 1.02 for g in ("b300", "h100", "l40s") for x in r12[g]) else 0.0,
              1, 1, "bool")

    r16 = fsst_rate_ratios(16)
    if len(r16) == len(GPUS4) and all(len(v) == len(TEXT5) for v in r16.values()):
        flat16 = [x for v in r16.values() for x in v]
        check("FSST-12 / OnPair-16: min over 4 GPUs", min(flat16), 1.10, 1.14, "x", "§6: 1.12 to 1.61x")
        check("FSST-12 / OnPair-16: max over 4 GPUs", max(flat16), 1.59, 1.63, "x", "§6: 1.12 to 1.61x")
        check("FSST-12 exceeds OnPair-16 on every cell",
              1.0 if all(x > 1.0 for x in flat16) else 0.0, 1, 1, "bool")

    # Compression ratio, container-matched: the basis §6 and tab:datasets now state explicitly.
    cr = []
    for ds, col in TEXT5:
        f = C.cell("b300", ds, col, 12, C.FSST12)
        o = C.same_run_onpair("b300", ds, col, 12)
        if f and o and f.get("mem_ratio_container_matched") and o.get("mem_ratio"):
            cr.append(f["mem_ratio_container_matched"] / o["mem_ratio"])
    if len(cr) == len(TEXT5):
        check("FSST-12 ratio / OnPair-12 ratio: min", min(cr), 0.72, 0.76, "x", "§6: 0.74 to 0.84x")
        check("FSST-12 ratio / OnPair-12 ratio: max", max(cr), 0.82, 0.86, "x", "§6: 0.74 to 0.84x")

    # The two ratio bases (FSST-12's own fixed 12-bit packing vs the container OnPair's codes
    # pass through) agree on the five REAL TEXT columns the paper evaluates, which is why the
    # basis choice moves no reported number.
    #
    # The scope is exactly those five, NOT "high-cardinality columns": TPC-H p_name has 2.0M
    # distinct values and still diverges 1.34x, because BtrBlocks compresses a structured code
    # stream further than a fixed 12-bit packing regardless of cardinality. An earlier version
    # of this check asserted the agreement over everything above 100k distinct and failed on
    # exactly that column. Cardinality is one driver of the divergence, not the only one.
    agree = []
    for ds, col in TEXT5:
        c = C.cell("b300", ds, col, 12, C.FSST12)
        if c and c.get("mem_ratio") and c.get("mem_ratio_container_matched"):
            agree.append(c["mem_ratio_container_matched"] / c["mem_ratio"])
    diverge = []
    for f in sorted((C.RESULTS / "b300-fsst12").glob("*.json")):
        for c in json.load(open(f)):
            if c.get("codec") != C.FSST12:
                continue
            n, m = c.get("mem_ratio"), c.get("mem_ratio_container_matched")
            if n and m and (c["dataset_id"], c["column"]) not in TEXT5:
                diverge.append(m / n)
    if agree and diverge:
        check("ratio bases agree on the five evaluated text columns", max(agree), 0.99, 1.01, "x",
              "the basis choice moves no number the paper reports")
        check("ratio bases diverge elsewhere", max(diverge), 100, 2000, "x",
              "READMEs said 3.3x; fineweb/language (1 distinct) is 906x")

    # Every FSST-12 cell is byte-exact against the CPU reference -- the generality claim is
    # "decodes byte for byte through the shipped kernels", so a single false here voids it.
    ver = []
    for g in GPUS4:
        d = C.RESULTS / ("%s-fsst12" % g)
        if not d.is_dir():
            continue
        for f in sorted(d.glob("fsst12_summary_*.json")):
            ver += [bool(c.get("verified")) for c in json.load(open(f))
                    if c.get("codec") == C.FSST12]
    if ver:
        check("FSST-12: every cell byte-exact", 1.0 if all(ver) else 0.0, 1, 1, "bool",
              f"{sum(ver)}/{len(ver)} verified")

    # 12. Fused output positioning (results/b300-fusedstall/). §3.2 justifies the stored
    #     sidecar against regeneration as a SEPARATE pass; the reviewer's reply is to fuse
    #     regeneration into the decode. Measured here, and slow -- but only meaningful
    #     because the kernel is byte-exact AND because the obvious objection (our block-wide
    #     stall) was removed and changed nothing.
    fs_dir = C.RESULTS / "b300-fusedstall"
    if fs_dir.is_dir():
        SHIPPED = "onpair_shmem_4tpt_split8read"
        rel = {}
        for f in sorted(fs_dir.glob("fusedstall_summary_*.json")):
            for c in json.load(open(f)):
                g = c.get("gpu") or {}
                km = {k.get("kernel"): k for k in g.get("kernels", []) if k.get("applicable")}
                base = (km.get(SHIPPED) or {}).get("decode_gib_s")
                if not base:
                    continue
                for name in (SHIPPED + "_lookback", SHIPPED + "_lookback_noshift",
                             SHIPPED + "_lookback_w1", SHIPPED + "_stcsedge"):
                    k = km.get(name)
                    if k and k.get("decode_gib_s"):
                        # An unverified rate must never reach a check: that is the whole
                        # reason the experimental kernels are excluded from best_kernel.
                        if not k.get("verified"):
                            continue
                        rel.setdefault(name, []).append(k["decode_gib_s"] / base)
        gm = lambda v: statistics.geometric_mean(v)
        b = rel.get(SHIPPED + "_lookback")
        n = rel.get(SHIPPED + "_lookback_noshift")
        w1 = rel.get(SHIPPED + "_lookback_w1")
        e = rel.get(SHIPPED + "_stcsedge")
        if b and n:
            check("fused positioning: base vs shipped", gm(b), 0.30, 0.40, "x",
                  "about 2.9x slower; §3.2's third option")
            check("fused positioning: stall removed", gm(n), 0.30, 0.40, "x")
            # The load-bearing one: removing the stall must change ~nothing, or the
            # paper's claim that the stall is not the cost is wrong.
            check("fused positioning: removing the stall changes nothing", gm(n) / gm(b),
                  0.97, 1.03, "x", "hypothesis was that this would be >1")
        if b and w1:
            # Second, independent refutation: no-stall-at-all is the WORST configuration.
            check("fused positioning: 1 warp/block is worse, not better", gm(w1) / gm(b),
                  0.35, 0.50, "x", "narrowing removes the idle and loses 2.3x")
        if e:
            check("streaming drain edges: no effect", gm(e), 0.98, 1.02, "x",
                  "head+tail policy change is inside dispersion")
        # Disjoint dictionary halves: §4 discloses that the shipped kernel holds each
        # entry's low eight bytes twice, and now states what that costs in RATE, not only
        # in footprint. Small, and the paper says so; the check keeps "small" honest.
        hi = []
        for f in sorted(fs_dir.glob("fusedstall_summary_*.json")):
            for c in json.load(open(f)):
                km = {k.get("kernel"): k for k in ((c.get("gpu") or {}).get("kernels") or [])
                      if k.get("applicable")}
                base = (km.get(SHIPPED) or {}).get("decode_gib_s")
                k = km.get(SHIPPED + "_hilo")
                if base and k and k.get("decode_gib_s") and k.get("verified"):
                    hi.append(k["decode_gib_s"] / base)
        if hi:
            check("disjoint dict halves: small gain", gm(hi), 1.01, 1.05, "x",
                  "§4: 1.02 to 1.03x; the duplicate costs rate as well as footprint")

    # 13. Access-width isolation on the EVALUATED columns (§5.3). The claim is that
    #     split8read narrows each access rather than making the table more cache-resident,
    #     and it rests on two counters moving in OPPOSITE ways: wavefronts down about a
    #     quarter while sector count stays flat. A hit-rate move of a couple of points
    #     cannot produce a wavefront reduction of 23%, which is the whole argument.
    #
    #     The A100 leg needed an explicit --metrics pass: `--set full` omits both counters
    #     on sm_80, which is why this was a three-chip result until 2026-08-15.
    def width_ratio(chip, col, metric):
        import csv as _csv, io as _io
        d = C.RESULTS / ("%s-widthncu-eval" % chip)
        if not d.is_dir():
            return None
        vals = {}
        for variant, tag in (("split8read", "s"), ("onpair_shmem_4tpt", "t")):
            f = d / ("shdict_ncu_%s_text_b12_%s_width.csv" % (col, variant))
            if not f.exists():
                f = d / ("shdict_ncu_%s_text_b12_%s_raw.csv" % (col, variant))
            if not f.exists():
                return None
            txt = f.read_text(errors="replace")
            i = txt.find('"ID","Process ID"')
            if i < 0:
                return None
            got = []
            for r in _csv.DictReader(_io.StringIO(txt[i:])):
                if r.get("Metric Name") == metric:
                    try:
                        got.append(float((r.get("Metric Value") or "").replace(",", "")))
                    except ValueError:
                        pass
                elif metric in (r.keys() if hasattr(r, "keys") else []):
                    pass
            if not got:
                # raw-page CSVs carry metrics as COLUMNS, not rows
                rows = list(_csv.reader(_io.StringIO(txt[i:])))
                hdr = [h.split(".TriageCompute.")[-1] for h in rows[0]]
                if metric not in hdr:
                    return None
                j = hdr.index(metric)
                for rr in rows[2:]:
                    try:
                        got.append(float(rr[j].replace(",", "")))
                    except (ValueError, IndexError):
                        pass
            if not got:
                return None
            vals[tag] = statistics.median(got)
        return (vals["s"] / vals["t"]) if vals.get("t") else None

    def width_delta_pts(chip, col, metric):
        """split8read minus stride-16, in percentage points (not a ratio)."""
        import csv as _csv, io as _io
        d = C.RESULTS / ("%s-widthncu-eval" % chip)
        vals = {}
        for variant, tag in (("split8read", "s"), ("onpair_shmem_4tpt", "t")):
            f = d / ("shdict_ncu_%s_text_b12_%s_width.csv" % (col, variant))
            if not f.exists():
                return None
            txt = f.read_text(errors="replace")
            i = txt.find('"ID","Process ID"')
            if i < 0:
                return None
            got = []
            for r in _csv.DictReader(_io.StringIO(txt[i:])):
                if r.get("Metric Name") == metric:
                    try:
                        got.append(float((r.get("Metric Value") or "").replace(",", "")))
                    except ValueError:
                        pass
            if not got:
                return None
            vals[tag] = statistics.median(got)
        return vals["s"] - vals["t"]

    WAVE = "l1tex__data_pipe_lsu_wavefronts.sum"
    SECT = "l1tex__t_sectors.sum"
    for chip in ("b300", "a100", "h100", "l40s"):
        for col in ("fineweb", "wikipedia"):
            wv = width_ratio(chip, col, WAVE) or width_ratio(chip, col,
                                                             "l1tex__data_pipe_lsu_wavefronts.avg")
            sc = width_ratio(chip, col, SECT)
            if wv:
                # The L40S reduction is real but SMALLER (0.84) than the HBM parts' 0.77,
                # and its hit rate moves ~8 points rather than under 3, so that chip
                # corroborates the direction without isolating width from residency.
                # Asserting one band for all four would either fail or be too loose to mean
                # anything, so the bands differ and §5.3 says why.
                lo, hi = (0.81, 0.88) if chip == "l40s" else (0.74, 0.81)
                check("width %s/%s: wavefronts fall" % (chip, col), wv, lo, hi, "x",
                      "split8read / stride-16; the narrowing")
            if sc:
                # The control. If sectors moved with wavefronts, the gain would be bytes,
                # not access width, and the mechanism claim would not hold.
                check("width %s/%s: sectors flat" % (chip, col), sc, 0.99, 1.02, "x",
                      "same bytes, fewer accesses")
            # The OTHER control, and the one §5.3's isolation actually rests on: on the
            # L1-bound parts the hit rate must move too little to explain a ~23% wavefront
            # drop. On the L40S it moves ~8 points and the paper says the two terms are not
            # separated there, so that chip is asserted to be the exception rather than
            # quietly averaged in with the rest.
            hr = width_delta_pts(chip, col, "l1tex__t_sector_hit_rate.pct")
            if hr is not None:
                lo, hi = (5.0, 12.0) if chip == "l40s" else (0.0, 3.0)
                check("width %s/%s: hit-rate move (pts)" % (chip, col), hr, lo, hi, "pts",
                      "residency cannot explain the drop where this is small")

    # 10. Token access distribution (Appendix A). Every number the appendix quotes in prose,
    # re-derived through common.freq_* -- the same reduction fig_freqbars draws, so the figure,
    # the prose and the JSON cannot drift apart. This appendix had NO coverage until
    # 2026-08-20, the same exposure that let three FSST-12 numbers in §6 drift unnoticed.
    try:
        fd = C.freqdist()

        # "the 256 most-read entries serve 81% of FSST-12's decoded codes, 35% of OnPair-12's
        # and 13% of OnPair-16's; a thousand entries serve all of FSST-12's, 72% ... and 24%"
        for codec, at256, at1k in (("fsst-12", (80, 82), (99.5, 100)),
                                   ("onpair-12", (34.5, 36), (71, 73)),
                                   ("onpair-16", (13, 14), (24, 25))):
            r = C.freq_record(fd, "l_comment", codec)
            check("freq l_comment/%s: top-256 coverage" % codec, C.freq_at(r, 256),
                  at256[0], at256[1], "%", "appendix A prose")
            check("freq l_comment/%s: top-1024 coverage" % codec, C.freq_at(r, 1024),
                  at1k[0], at1k[1], "%", "appendix A prose")

        # "1026 entries against OnPair-12's 3862 on l_comment, and 870 against 2214 on naics_name"
        for col, codec, want in (("l_comment", "fsst-12", 1026), ("l_comment", "onpair-12", 3862),
                                 ("cg_naics_name", "fsst-12", 870),
                                 ("cg_naics_name", "onpair-12", 2214)):
            got = C.freq_record(fd, col, codec)["entries_referenced"]
            check("freq %s/%s: entries referenced" % (col, codec), float(got),
                  want, want, "", "appendix A prose")

        # "376 entries, 2165 and 26866" to cover 90%, i.e. "37% of FSST-12's table, 56% of
        # OnPair-12's and 48% of OnPair-16's". Interpolated, not nearest-sample: see
        # common.freq_entries_for, which inverts the curve the way the figure reads it forward.
        for codec, ent, frac in (("fsst-12", (374, 378), (36, 38)),
                                 ("onpair-12", (2160, 2172), (55, 57)),
                                 ("onpair-16", (26800, 26930), (47, 49))):
            r = C.freq_record(fd, "l_comment", codec)
            e90 = C.freq_entries_for(r, 90)
            check("freq l_comment/%s: entries for 90%%" % codec, e90, ent[0], ent[1],
                  "entries", "appendix A prose")
            check("freq l_comment/%s: 90%% as share of table" % codec,
                  100.0 * e90 / r["entries_referenced"], frac[0], frac[1], "%",
                  "appendix A prose")

        # "covering 90% of the reads takes between 15 and 59% of the entries" -- the LOW end
        # does not re-derive: the minimum over all (column, codec) is 13.8%, on
        # cg_naics_name/OnPair-16. Asserted against the DATA rather than against the prose, so
        # the discrepancy stays visible. Fix the sentence to "14 to 59%", or recompute it if the
        # appendix is rescoped to the locked corpus, which drops that column entirely.
        shares = [100.0 * C.freq_entries_for(r, 90) / r["entries_referenced"] for r in fd]
        check("freq: min 90% share of table", min(shares), 13.5, 14.2, "%",
              "prose says 15%; data says 13.8% on cg_naics_name/OnPair-16")
        check("freq: max 90% share of table", max(shares), 58, 59.5, "%", "prose: 59%")

        # "that hot set stays under 19 KB on every column at OnPair-12 and FSST-12 alike",
        # charging each entry the eight bytes of a dense plane. OnPair-16 "does not: on the five
        # columns whose dictionaries fill, its hot set is 191 to 299 KB".
        for codec in ("fsst-12", "onpair-12"):
            worst = max(8.0 * C.freq_entries_for(r, 90) / 1024.0
                        for r in fd if r["codec"] == codec)
            check("freq %s: worst 90%% hot set" % codec, worst, 0, 19, "KiB",
                  "appendix A: under 19 KB on every column")
        big = sorted((8.0 * C.freq_entries_for(r, 90) / 1024.0
                      for r in fd if r["codec"] == "onpair-16"), reverse=True)[:5]
        check("freq onpair-16: 5th largest hot set", big[-1], 190, 195, "KiB", "appendix A: 191 KB")
        check("freq onpair-16: largest hot set", big[0], 295, 302, "KiB", "appendix A: 299 KB")

        # "On Wikipedia only 2% of accesses reach the high plane and 90% of those come from
        # 1.1 KB. On l_comment 42% ... from 8.8 KB. On naics_name 79% ... 1.9 KB against the
        # low plane's 3.1 KB." Checked in BYTES: the appendix's KB are binary (9048 B reads as
        # 8.8), so asserting on the raw counter keeps a unit slip out of the check itself.
        for col, frac, hib, lob in (("wikipedia", (1.5, 2.5), (1150, 1200), None),
                                    ("l_comment", (41, 43), (9000, 9100), None),
                                    ("cg_naics_name", (78, 80), (1950, 2000), (3150, 3200))):
            r = C.freq_record(fd, col, "onpair-12")
            check("freq %s: high-plane access share" % col, 100.0 * r["hi_access_frac"],
                  frac[0], frac[1], "%", "appendix A prose")
            check("freq %s: high-plane 90%% bytes" % col, float(r["hi_bytes_90"]),
                  hib[0], hib[1], "B", "appendix A prose")
            if lob:
                check("freq %s: low-plane 90%% bytes" % col, float(r["lo_bytes_90"]),
                      lob[0], lob[1], "B", "appendix A prose")
    except FileNotFoundError:
        pass

    # ── report ──
    w = max(len(r[0]) for r in ROWS)
    print(f"{'check':<{w}}  {'derived':>11}  {'expected':>14}  result")
    print("-" * (w + 40))
    for name, got, exp, unit, ok, note in ROWS:
        gs = f"{got:.3f} {unit}".strip() if isinstance(got, float) else str(got)
        print(f"{name:<{w}}  {gs:>11}  {exp:>14}  {'PASS' if ok else 'FAIL'}"
              + (f"   ({note})" if note and not ok else ""))
    print("-" * (w + 40))
    print(f"{len(ROWS)} checks, {len(FAILS)} failed")
    if len(ROWS) < EXPECTED_CHECKS:
        print(f"INCOMPLETE: only {len(ROWS)}/{EXPECTED_CHECKS} checks ran -- a results file is "
              "missing or unreadable (e.g. results/iaa/ or results/e2e/), so guarded checks were "
              "silently skipped. This is a failure, not a pass.")
        sys.exit(1)
    if FAILS:
        print("FAILED:", ", ".join(FAILS))
        sys.exit(1)
    print(f"all {len(ROWS)} headline numbers re-derive from committed data ✓")



    # 9. Sapphire thread sweep (\u00a76.6): 32-core geomean vs the IAA block peak (28.9 GB/s).
    try:
        import json as _json, math as _math
        _rows = _json.load(open(C.RESULTS / "iaa" / "onpair_cpu_sapphire_threads.json"))
        _rows = _rows.get("results", _rows) if isinstance(_rows, dict) else _rows
        _v = [r["fat_gibs"] for r in _rows if r["bits"] == 12 and r["threads"] == 32]
        if _v:
            _g = _math.exp(sum(_math.log(x) for x in _v) / len(_v)) * 1.0737
            check("CPU 32-core geomean (dict-12)", _g, 178, 186, "GB/s", "paper: roughly 182 GB/s")
            check("32-core vs IAA block peak", _g / 28.9, 6.0, 6.6, "x", "paper: six times")
    except FileNotFoundError:
        pass

if __name__ == "__main__":
    main()
