# Predicate-selectivity sweep on decode→scan (blog experiment)

**Status: EXECUTED 2026-06-27** — results in [`sweep/`](sweep/) (`sweep_<needle>.json` for the
10 needles + `sweep_rare.json` for the AUTO near-unique anchor), from a B300 (Nebius uk-south1)
at rev `6ee03c1d8`, min-of-200. The curve figure and a `validate.py` check are still to be added.
The decode kernel and the e2e bench are unchanged; this is the same `bench/gpu/e2e_scan.cu` run
with a set of needles, so it needed no new code.

## Question

The headline e2e experiment ([`ANALYSIS.md`](ANALYSIS.md)) runs one predicate: a rare,
near-unique substring scan over the whole decoded ClickBench `URL` column (the heaviest
hand-off — the operator consumes the entire decoded output). This sweep asks the natural
follow-up: **how does the decode→scan overhead move with the predicate's selectivity?** It
runs the *same* substring scan (`LIKE '%needle%'`, matched anywhere) over the *same*
decoded column for a spread of needles from near-unique to ubiquitous, and traces e2e
overhead against match count. (It is one operator class — a substring scan — swept by
selectivity, not a set of different operators; a prefix/equality or length aggregate would
need per-row structure the e2e dump does not carry.)

## Needles (rare → common)

All are real URL substrings. Sources: FSST's own URL-corpus symbols (`http://`, `www.`,
`.org`; FSST §3), ClickBench **Q20** (`SELECT COUNT(*) FROM hits WHERE URL LIKE '%google%'`),
and the Yandex Metrica origin of the ClickBench `hits` data (`yandex`, `.ru`).

| needle | expected end | source |
|---|---|---|
| *(auto, 24-byte)* | near-unique (light anchor) | the headline run |
| `youtube` | rare-ish (one site) | — |
| `google`  | **ClickBench Q20** | ClickBench |
| `yandex`  | common (dataset origin) | dataset |
| `index`   | path token, mid | — |
| `.html`   | path token, mid | — |
| `.org`    | common | **FSST symbol** |
| `www.`    | common | **FSST symbol** |
| `.com`    | very common | web |
| `http`    | ~every URL | FSST (`http://`) |
| `.ru`     | very common (Yandex TLD) | dataset |

Single-character needles (e.g. `/`) are deliberately excluded: they match ~100M positions
and drive the scan's match counter atomic-bound — a pathological case, not a real `LIKE`.

## Reproduce (build-and-run, your own GPU box)

Build the frozen harness fork (`github.com/mprammer/vortex`) and `e2e_scan` per the fork's
`benchmarks/onpair-bench/README.md` §3, dump the ClickBench `URL` column once, then run the
one binary over the needle set against that one dump:

```sh
# 1. dump the decoded ClickBench URL column once (bits 16, 1 GB sample) — the fork's §3 flow
ONPAIR_DUMP_E2E=/tmp/clickbench_url.e2ebin \
  python benchmarks/onpair-bench/run.py --gpu-decode --datasets clickbench --columns URL \
  --bits 16 --chunk-mb 1000

# 2. build the scan bench (inside the fork tree)
nvcc -O3 -arch=native -std=c++17 benchmarks/onpair-bench/e2e_scan.cu -o e2e_scan

# 3. sweep the predicate (each run is seconds; min-of-200, matches the e2e protocol)
./e2e_scan /tmp/clickbench_url.e2ebin "" 200 > sweep_rare.json          # near-unique anchor
for n in youtube google yandex index .html .org www. .com http .ru; do
  ./e2e_scan /tmp/clickbench_url.e2ebin "$n" 200 > "sweep_${n}.json"
done
```

Each run emits `cpu_matches`, `e2e_overhead_pct`, `decode_gbps`, and `scan_gbps`. (Our
private orchestration that drives this on a rented B300 is not shipped; reproduction is the
commands above on your own hardware — see the repo README's Tier-2 note.)

## Output and analysis

The sweep self-labels by `cpu_matches`: a curve of **e2e overhead (% over decode alone) vs
predicate selectivity**, with the rare anchor at the light end and the common URL tokens at
the heavy end, ClickBench Q20 (`google`) marked on it. Results land in `results/e2e/sweep/`
(`sweep_<needle>.json`); the curve figure and a `validate.py` check are added once the data
is committed.
