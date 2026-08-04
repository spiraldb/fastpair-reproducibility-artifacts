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
EXPECTED_CHECKS = 54


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
    rows = list(csv.DictReader(open(C.RESULTS / "ncu-costsurface.csv")))
    flt = lambda r, k: float(r[k])
    for arch in ["a100", "l40s", "h100", "b300"]:
        ar = [r for r in rows if r["arch"] == arch]
        cache = max(max(flt(r, "l1tex"), flt(r, "l2")) for r in ar)
        dram, sm = max(flt(r, "dram") for r in ar), max(flt(r, "sm") for r in ar)
        check(f"cost surface {arch}: cache pipe peak", cache, 70, 100, "%peak")
        # the binding pipe outruns DRAM and SM by a wide margin on every arch
        check(f"cost surface {arch}: cache >> DRAM", cache - dram, 45, 100, "pts")
        check(f"cost surface {arch}: cache >> SM", cache - sm, 40, 100, "pts")
    b300 = [r for r in rows if r["arch"] == "b300"]
    h100 = [r for r in rows if r["arch"] == "h100"]
    check("cost surface: B300 L1/TEX peak", max(flt(r, "l1tex") for r in b300), 86, 95, "%peak",
          "Blackwell binds on per-SM L1/TEX")
    check("cost surface: H100 L2 peak", max(flt(r, "l2") for r in h100), 84, 92, "%peak",
          "Hopper binds on device-wide L2")

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
