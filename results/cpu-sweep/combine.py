#!/usr/bin/env python3
"""Merge per-machine onpair-cpu-bench results into a single cpu-sweep.json.

Reads <dir>/<label>/{onpair_cpu.json, machine.meta, cpu-env.txt} and emits <dir>/cpu-sweep.json:
the cross-generational CPU decode matrix (fat vs entries vs naive), one entry per machine,
ordered by vendor then generation. Target dir defaults to this script's dir; pass another to
combine a sibling sweep:

    python3 results/cpu-sweep/combine.py results/cpu-sweep-4phys
    python3 results/cpu-sweep/combine.py results/cpu-sweep-8phys
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TARGET = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else HERE
ORDER = ["amd-rome", "amd-milan", "amd-genoa", "amd-turin",
         "intel-icelake", "intel-sapphire", "intel-granite",
         "arm-graviton2", "arm-graviton3", "arm-graviton4"]


def read_meta(d):
    m = {}
    p = d / "machine.meta"
    if p.exists():
        for line in p.read_text().splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                m[k.strip()] = v.strip()
    return m


def read_cpuenv(d):
    model = cores = threads = None
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
    return model, cores, threads


labels = [l for l in ORDER if (TARGET / l).is_dir()]
labels += [d.name for d in sorted(TARGET.iterdir())
           if d.is_dir() and d.name not in labels]

machines, bench_mb, region, pin_cores, thread_set = [], None, None, None, None
for label in labels:
    d = TARGET / label
    jp = d / "onpair_cpu.json"
    if not jp.exists():
        continue
    data = json.loads(jp.read_text())
    m = read_meta(d)
    model, cores, threads = read_cpuenv(d)
    bench_mb = bench_mb or data.get("mb") or m.get("bench_mb")
    region = region or m.get("region")
    pin_cores = pin_cores or m.get("pin_cores")
    thread_set = thread_set or m.get("threads")
    machines.append({
        "label": label,
        "instance_type": m.get("instance_type"),
        "ddr": m.get("ddr"),
        "cpu_model": model,
        "cores_per_socket": cores,
        "threads_per_core": threads,
        "pinned_cores": m.get("pin_cores"),
        "results": data.get("results", []),
    })

out = {
    "sweep": "onpair-cpu decode: fat vs entries vs naive, cross-generational CPU matrix",
    "bench_mb": bench_mb,
    "region": region,
    "pinned_physical_cores": pin_cores,
    "thread_counts": thread_set,
    "columns": ["synthetic_url", "tpch_comment", "fineweb_text"],
    "metric": "GiB/s of decoded output (byte-identical across all three layouts)",
    "layouts": {
        "fat": "data + code*16: independent fixed-stride load + 16-byte over-copy (this work; FSST's fixed-stride decode at OnPair's dict scale)",
        "entries": "variable-stride (offset->bytes dependent load) + 16-byte over-copy = the PUBLISHED OnPair decode (Gargiulo & Venturini, arXiv:2508.02280)",
        "naive": "variable-stride + inlined exact per-token copy; a non-over-copying baseline, NOT a real codec",
    },
    "machines": machines,
}
(TARGET / "cpu-sweep.json").write_text(json.dumps(out, indent=2) + "\n")
print(f"wrote {TARGET.name}/cpu-sweep.json: {len(machines)} machines, "
      f"pin={pin_cores}, threads={thread_set}, mb={bench_mb}")
