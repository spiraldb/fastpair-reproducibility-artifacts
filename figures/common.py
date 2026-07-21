"""Shared helpers for OnPair-GPU figure generation.

Every figure script reads the committed `results/` JSON/CSV and writes a PDF (+PNG)
into `figures/out/`. Nothing here re-runs a GPU job; the figures are reproduced
purely from the archived measurement artifacts. See figures/README.md.
"""
import json
import re
from pathlib import Path


def _repo_root() -> Path:
    """The directory containing results/ (walk up from this file)."""
    here = Path(__file__).resolve()
    for d in [here.parent, *here.parents]:
        if (d / "results").is_dir():
            return d
    raise RuntimeError("could not locate results/ above %s" % here)


ROOT = _repo_root()
RESULTS = ROOT / "results"
OUTDIR = Path(__file__).resolve().parent / "out"

# Four architectures, one representative GPU each: A100 (Ampere), L40S (Ada Lovelace,
# GDDR6), H100 (Hopper), B300 (Blackwell) -- two memory technologies (HBM + GDDR6).
# GH200 dropped (a second Hopper, within noise of H100); B200 dropped for B300 (the
# newer Blackwell, complete locked sweep + full NCU). Raw for the dropped parts is in
# results/{gh200,b200}.
GPUS = ["a100", "l40s", "h100", "b300"]
GPU_LABEL = {"a100": "A100", "l40s": "L40S", "gh200": "GH200", "h100": "H100", "b200": "B200", "b300": "B300"}

# Vendor-rated HBM peak, GiB/s. Matches the Sec 2 architecture table (TB/s) and the
# GH200 "paper figure" of 3725 GiB/s used for the %-of-peak resolution.
HBM_PEAK_GIBS = {"a100": 1448, "l40s": 805, "gh200": 3725, "h100": 3120, "b200": 7451, "b300": 7451}

# Throughput is reported in GB/s (decimal, 10^9 B/s), reduced from the raw per-iteration
# timings at figure-generation: GB/s = decoded_bytes / min(decode_ns_iters) (bytes per
# nanosecond == GB/s exactly). Best-of-100-iterations (min) is the microbenchmark
# convention. This factor converts a stored GiB/s scalar (binary, 2^30) to GB/s for the
# DE and any older cell that lacks the raw samples.
GIB_TO_GB = (2 ** 30) / 1e9   # 1.073741824

# --------------------------------------------------------------------------
# Unified theme: one palette and one look across every results-bearing figure.
# --------------------------------------------------------------------------
INK = "#333333"
PRIMARY = "#2166ac"   # OnPair-GPU; the binding L1/TEX pipe (the protagonist)
WARM = "#e08214"      # hardware DE; the %-of-peak accent (the baseline to beat)
GRAY = "#9aa0a6"      # software nvCOMP-Zstd; idle pipes (muted)

# Decode techniques (Fig. field).
TECH = {"onpair": PRIMARY, "de": WARM, "software": GRAY}

# GPU generations, A100 -> B200, light -> dark (newest/fastest is darkest). Used
# wherever a bar or panel is keyed by GPU (Fig. breadth, Fig. scaling).
GPU_RAMP = {"a100": "#9ecae1", "l40s": "#74c476", "gh200": "#6baed6", "h100": "#3182bd", "b200": "#08519c", "b300": "#08519c"}

# GSST (CHEOPS'25), the prior GPU decoder for the FSST family: 191 GB/s on the A100,
# TPC-H l_comment. Its only reported point, drawn as a soft dashed reference line on
# the l_comment panel. Converted to GiB/s to match the figures' axes.
GSST_GIBS = 191.0 * 1e9 / (2 ** 30)   # ~177.9
GSST_GBS = 191.0   # GSST's reported rate is already GB/s (decimal); use directly on GB/s axes
GSST_COL = ("tpch-sf10", "l_comment")
GSST_RED = "#d6604d"

# Stage decomposition (Fig. stagecost): the two migrating stages echo the theme's
# blue/orange; gather and drain barely move, so they are muted.
STAGE = {"scan": PRIMARY, "emit": WARM, "gather": "#7fb3a6", "drain": GRAY}

# Cost surface (Fig. costsurface): foreground the cache path that binds, mute the
# idle pipes. L1/TEX is the bound; L2 is the same path one level down; DRAM/SM idle.
PIPE = {"L1/TEX": PRIMARY, "L2": "#a8c5e0", "DRAM": GRAY, "SM (compute)": GRAY}

# Launch-bound (1-6 MB) columns: reported for completeness, not as throughput.
LAUNCH_BOUND = {
    ("dbtext", "email"), ("dbtext", "hex"), ("dbtext", "l_comment"),
    ("dbtext", "ps_comment"), ("dbtext", "yago"), ("tpch-sf10", "s_comment"),
}

# Representative (dataset, column) for breadth/scaling, with a short label.
REPRESENTATIVE = [
    ("tpch-sf10", "ps_comment", "TPC-H ps_comment"),
    ("tpch-sf10", "l_comment", "TPC-H l_comment"),
    ("clickbench", "URL", "ClickBench URL"),
    ("fineweb", "text", "FineWeb"),
    ("wikipedia", "text", "Wikipedia"),
    ("book-reviews", "text", "book-reviews"),
    ("synthetic", "url", "synthetic"),
    ("lship", "l_shipinstruct", "l_shipinstruct"),
]


def load(gpu, dataset):
    f = RESULTS / gpu / ("onpair_summary_%s.json" % dataset)
    return json.load(open(f)) if f.exists() else []


def cell(gpu, dataset, column, bits=12):
    for c in load(gpu, dataset):
        if c.get("column") == column and c.get("bits") == bits:
            return c
    return None


def kernel_map(c):
    """{kernel_name: decode_gib_s} for one cell."""
    g = c.get("gpu") or {}
    return {k.get("kernel"): k.get("decode_gib_s") for k in g.get("kernels", [])}


def _gb_s(decoded_bytes, ns_iters, gib_s_scalar=None):
    """Reduce one kernel's raw per-iteration ns to GB/s = decoded_bytes / min(ns).
    Falls back to a stored GiB/s scalar (converted) when raw samples are absent."""
    if decoded_bytes and ns_iters:
        return decoded_bytes / min(ns_iters)   # bytes / ns == GB/s
    return gib_s_scalar * GIB_TO_GB if gib_s_scalar else None


def best_shipped(c):
    """Best decode GB/s over SHIPPED kernels, reduced from the raw per-iteration timings.

    GB/s = decoded_bytes / min(decode_ns_iters). Excludes the non-byte-exact `*ablate*`
    instrumentation builds and any kernel that failed byte-validation. Falls back to the
    stored best_decode_gib_s (converted) if no raw per-iteration samples are present.
    """
    if not c:
        return None
    g = c.get("gpu") or {}
    db = g.get("decoded_bytes")
    vals = [
        _gb_s(db, k.get("decode_ns_iters"), k.get("decode_gib_s"))
        for k in g.get("kernels", [])
        if k.get("decode_gib_s")
        and "ablate" not in str(k.get("kernel", ""))
        and k.get("verified") is not False
    ]
    vals = [v for v in vals if v]
    if vals:
        return max(vals)
    bd = g.get("best_decode_gib_s")
    return bd * GIB_TO_GB if bd else None


def software_best(c):
    """Best software nvCOMP-Zstd decode GB/s for one cell (or None), from raw min."""
    if not c:
        return None
    g = c.get("gpu") or {}
    best = None
    for e in (g.get("nvcomp_zstd") or []):
        if not isinstance(e, dict):
            continue
        rb, it = e.get("raw_bytes"), e.get("decode_ms_iters")
        v = (rb / min(it) / 1e6) if (rb and it) else (
            e["decode_gib_s"] * GIB_TO_GB if e.get("decode_gib_s") else None)
        if v and (best is None or v > best):
            best = v
    return best


def zstd_gb_s(entry):
    """One nvCOMP-Zstd entry's decode GB/s (min of raw samples, else converted scalar)."""
    rb, it = entry.get("raw_bytes"), entry.get("decode_ms_iters")
    if rb and it:
        return rb / min(it) / 1e6
    return entry["decode_gib_s"] * GIB_TO_GB if entry.get("decode_gib_s") else None


def distinct_codes(c):
    return ((c or {}).get("gpu") or {}).get("distinct_codes")


def de_map():
    """Blackwell hardware Decompression Engine best decode GB/s per (dataset, column).
    Sourced from B300; the DE is fixed-function silicon, byte-identical on B200/B300.
    The DE stores only a min-reduced scalar (no raw samples), so convert GiB/s -> GB/s."""
    f = RESULTS / "b300" / "onpair_nvcomp_hw.json"
    return {(e["dataset_id"], e["column"]):
            (e["best_decode_gib_s"] * GIB_TO_GB if e.get("best_decode_gib_s") else None)
            for e in json.load(open(f))}


def ncu_sol(metric, fname="b200-ncu/ncu_costsurface_synthetic_url_b12_sol.txt"):
    """Parse a Speed-of-Light %-of-peak value from an NSight Compute SOL dump."""
    txt = (RESULTS / fname).read_text(errors="ignore")
    for line in txt.splitlines():
        if line.strip().startswith(metric):
            m = re.findall(r"[-+]?\d*\.?\d+", line)
            if m:
                return float(m[-1])
    raise KeyError("metric %r not found in %s" % (metric, fname))


def apply_theme():
    """One consistent look across all figures. Returns the pyplot module."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.size": 8, "axes.titlesize": 8, "axes.labelsize": 8,
        "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 7,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.edgecolor": "#888888", "axes.linewidth": 0.8, "axes.axisbelow": True,
        "axes.grid": True, "axes.grid.axis": "y",
        "grid.color": "#e6e6e6", "grid.linewidth": 0.7,
        "text.color": INK, "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK,
        "figure.dpi": 200, "figure.facecolor": "white", "savefig.facecolor": "white",
    })
    return plt


def new_fig(w=3.3, h=2.2):
    return apply_theme().subplots(figsize=(w, h))


def save(fig, name):
    OUTDIR.mkdir(exist_ok=True)
    for ext in ("pdf", "png"):
        fig.savefig(OUTDIR / ("%s.%s" % (name, ext)), bbox_inches="tight", pad_inches=0.02)
    print("wrote", (OUTDIR / (name + ".pdf")).relative_to(ROOT))
