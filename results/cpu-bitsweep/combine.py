#!/usr/bin/env python3
"""Merge per-machine onpair-cpu-bench bit-width-sweep results into cpu-bitsweep.json.

Reads <dir>/<label>/{onpair_cpu.json, machine.meta, cpu-env.txt} and emits cpu-bitsweep.json:
the cross-generational fat-vs-compact decode sweep over dict bit-widths 9..16 at one physical
core, one entry per machine. Also captures the per-core L1d/L2 and shared L3 sizes, which bound
where the fat table (2^bits entries * 16 bytes) sits in the cache hierarchy.

    python3 results/cpu-bitsweep/combine.py
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TARGET = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else HERE
ORDER = ["amd-rome", "amd-milan", "amd-genoa", "amd-turin",
         "intel-icelake", "intel-sapphire", "intel-granite",
         "arm-graviton2", "arm-graviton3", "arm-graviton4"]
_UNIT = {"KiB": 1024, "MiB": 1024 ** 2, "GiB": 1024 ** 3}


def read_meta(d):
    m = {}
    p = d / "machine.meta"
    if p.exists():
        for line in p.read_text().splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                m[k.strip()] = v.strip()
    return m


def _cache(line):
    """'L2 cache: 8 MiB (8 instances)' -> (total_bytes, instances)."""
    mm = re.search(r"([\d.]+)\s*(KiB|MiB|GiB)\s*\((\d+)\s*instance", line)
    if not mm:
        return None
    return int(float(mm.group(1)) * _UNIT[mm.group(2)]), int(mm.group(3))


def read_cpuenv(d):
    model = cores = threads = None
    cache = {}
    p = d / "cpu-env.txt"
    if p.exists():
        for line in p.read_text().splitlines():
            s = line.strip()
            if model is None and "Model name" in line:
                model = line.split(":", 1)[1].strip()
            if s.startswith("Core(s) per socket"):
                cores = s.split(":", 1)[1].strip()
            if s.startswith("Thread(s) per core"):
                threads = s.split(":", 1)[1].strip()
            for lvl in ("L1d", "L2", "L3"):
                if s.startswith(f"{lvl} cache"):
                    c = _cache(s)
                    if c:
                        cache[lvl] = c
    pc = {}
    if "L1d" in cache:
        pc["l1d_per_core_b"] = cache["L1d"][0] // max(cache["L1d"][1], 1)
    if "L2" in cache:
        pc["l2_per_core_b"] = cache["L2"][0] // max(cache["L2"][1], 1)
    if "L3" in cache:
        pc["l3_total_b"] = cache["L3"][0]
    return model, cores, threads, pc


labels = [l for l in ORDER if (TARGET / l).is_dir()]
labels += [d.name for d in sorted(TARGET.iterdir())
           if d.is_dir() and d.name not in labels]

machines, bench_mb, region, pin_cores = [], None, None, None
for label in labels:
    d = TARGET / label
    jp = d / "onpair_cpu.json"
    if not jp.exists():
        continue
    data = json.loads(jp.read_text())
    m = read_meta(d)
    model, cores, threads, pc = read_cpuenv(d)
    bench_mb = bench_mb or data.get("mb") or m.get("bench_mb")
    region = region or m.get("region")
    pin_cores = pin_cores or m.get("pin_cores")
    rec = {
        "label": label,
        "instance_type": m.get("instance_type"),
        "ddr": m.get("ddr"),
        "cpu_model": model,
        "cores_per_socket": cores,
        "threads_per_core": threads,
        "pinned_cores": m.get("pin_cores"),
        "results": data.get("results", []),
    }
    rec.update(pc)
    machines.append(rec)

out = {
    "sweep": "onpair-cpu decode: fat vs compact across dict bit-widths 9..16, cross-generational CPU matrix",
    "bench_mb": bench_mb,
    "region": region,
    "pinned_physical_cores": pin_cores,
    "threads": 1,
    "bit_widths": [9, 10, 11, 12, 13, 14, 15, 16],
    "metric": "GiB/s of decoded output; dict_entries gives the fat table size (entries*16 bytes)",
    "layouts": {
        "fat": "data + code*16: fixed-stride load + 16-byte over-copy (this work)",
        "entries": "variable-stride offset->bytes dependent load + 16-byte over-copy = published OnPair",
        "naive": "variable-stride + exact per-token copy; a non-over-copying baseline, NOT a codec",
    },
    "cache_note": "l1d_per_core_b / l2_per_core_b are per-core; l3_total_b is shared; the fat table at 2^bits entries spans entries*16 bytes",
    "machines": machines,
}
(TARGET / "cpu-bitsweep.json").write_text(json.dumps(out, indent=2) + "\n")
print(f"wrote cpu-bitsweep.json: {len(machines)} machines, mb={bench_mb}, pin={pin_cores}")
for m in machines:
    print(f"  {m['label']:16} L1d/core={m.get('l1d_per_core_b',0)//1024}K  "
          f"L2/core={m.get('l2_per_core_b',0)//1024}K  L3={m.get('l3_total_b',0)//1024//1024}M")
