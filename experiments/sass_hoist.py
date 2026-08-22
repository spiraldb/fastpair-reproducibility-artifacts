# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""Did the hoist survive compilation? Read it out of the SASS.

    uv run experiments/sass_hoist.py results/suite-<id>/<chip>/kernel_sass.txt

WHY STATIC AND NOT RUNTIME. H is a scheduling knob: issue up to H high-plane loads before
consuming any of them. Whether that transformation happened is a property of instruction ORDER in
the native code, and ptxas is where scheduling and register allocation both occur. NUM_REGS cannot
answer it -- it reports what was allocated, not whether the loads moved -- and runtime counters
measure the consequence rather than the transformation.

The runtime half is already settled: registers are flat across H on all three chips (56/56/56/56
on the B300, 64 across the board on H100 and L40S) and local_bytes is zero, so the hoist costs
nothing. What is open is whether it DOES anything, and that is what this reads.

THE MEASUREMENT IS A COUNT, NOT A DIFF. SASS text carries absolute offsets, so a raw diff between
two variants is almost entirely noise. Three quantities, in increasing rigour:

  1. Opcode histogram -- LDG (global), LDS/STS (shared), and total. If H=1 and H=4 agree on all
     three, nothing moved.
  2. MAX OUTSTANDING GLOBAL LOADS before the first consumer. Walk the listing and count how many
     LDGs are in flight whose destination register has not yet been read. This should track H if
     the hoist works. If it stays flat regardless of H, the hoist is inert even when instructions
     shuffled. This is the quantity that answers the question.
  3. Scheduling control bits (stall counts, yield, barrier indices). Identical barrier allocation
     on the consumers means the compiler made no scheduling change. Not parsed here: the encoding
     is undocumented and version-specific, and quantity 2 already carries the argument.

DO NOT BUILD A CLAIM ON AN OPCODE SEQUENCE. SASS is undocumented and unstable across toolkit
versions. The durable statement is the counted one -- "the number of high-plane loads in flight
before the first consumer does not increase with H" -- which survives disassembly details and is
what the design model actually asserts.

Reading the outcome:
  outstanding does NOT rise with H  -> ptxas sank the hoist back. Since H demonstrably does
      something at B=8, that makes it a pressure-dependent scheduling choice by the compiler,
      which is a sharper mechanism sentence than the paper currently has.
  outstanding rises, registers flat -> the hoist survived and is free, reusing live ranges the
      non-hoisted schedule already held. Then its null effect at B<=4 means latency was already
      covered by K, which is the latency-coverage reading.
"""
import argparse
import collections
import re
import sys

# cuobjdump listings vary in decoration across versions; match the opcode as a word rather than
# anchoring on column positions.
OPCODE = re.compile(r"\b([A-Z][A-Z0-9_.]{1,15})\b")
# Destination register is the first operand after the opcode; sources are the rest. R2, R2.64 etc.
REG = re.compile(r"\bR(\d+)\b")
HEADER = re.compile(r"^=====\s+(\S+)")


def kernels(path):
    """name -> [instruction text] for every kernel in a kernel_sass.txt."""
    out, cur = {}, None
    for line in open(path, errors="ignore"):
        m = HEADER.match(line)
        if m:
            cur = m.group(1)
            out[cur] = []
            continue
        if cur is None:
            continue
        # A SASS body line has an opcode and usually an address in /*....*/ form.
        if "*/" in line or re.search(r"^\s+[A-Z@]", line):
            out[cur].append(line.rstrip())
    return out


def opcode_of(text):
    body = text.split("*/")[-1] if "*/" in text else text
    body = body.strip().lstrip("@!PT ").strip()
    m = OPCODE.match(body)
    return m.group(1) if m else None


def histogram(instrs):
    h = collections.Counter()
    for t in instrs:
        op = opcode_of(t)
        if op:
            h[op.split(".")[0]] += 1
    return h


def max_outstanding_loads(instrs):
    """Peak number of global loads in flight whose destination has not yet been read.

    A load's destination enters the in-flight set when the LDG issues and leaves it the first time
    any later instruction reads that register. The peak of that set is the depth the schedule
    actually achieves, which is what H is supposed to raise."""
    inflight, peak = {}, 0
    for t in instrs:
        op = opcode_of(t)
        if not op:
            continue
        body = t.split("*/")[-1] if "*/" in t else t
        regs = REG.findall(body)
        if not regs:
            continue
        dst, srcs = regs[0], regs[1:]
        for r in srcs:                      # a read retires the load that produced it
            inflight.pop(r, None)
        if op.startswith("LDG"):
            inflight[dst] = True
            peak = max(peak, len(inflight))
        else:
            inflight.pop(dst, None)         # overwritten without being read
    return peak


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sass", help="kernel_sass.txt from a suite leg")
    ap.add_argument("--coord", default="k6_t256_b4",
                    help="coordinate to compare H across, e.g. k6_t256_b4")
    a = ap.parse_args()
    ks = kernels(a.sass)
    if not ks:
        sys.exit("no kernels found; is this a cuobjdump --dump-sass listing?")

    sel = sorted(n for n in ks if a.coord in n)
    if not sel:
        sys.exit(f"no kernels matching {a.coord} in {a.sass}\n"
                 f"available: {', '.join(sorted(ks)[:8])}")
    print(f"{'kernel':<34}{'total':>7}{'LDG':>6}{'LDS':>6}{'STS':>6}{'max outstanding LDG':>21}")
    for n in sel:
        h = histogram(ks[n])
        print(f"{n:<34}{sum(h.values()):>7}{h.get('LDG', 0):>6}{h.get('LDS', 0):>6}"
              f"{h.get('STS', 0):>6}{max_outstanding_loads(ks[n]):>21}")
    peaks = {n: max_outstanding_loads(ks[n]) for n in sel}
    if len(set(peaks.values())) == 1:
        print(f"\nVERDICT: outstanding-load depth is {next(iter(peaks.values()))} for every H at "
              f"{a.coord}.\n         The hoist did not change the schedule ptxas emitted.")
    else:
        print(f"\nVERDICT: depth varies with H at {a.coord}: {peaks}.\n"
              f"         The hoist survived compilation.")


if __name__ == "__main__":
    main()
