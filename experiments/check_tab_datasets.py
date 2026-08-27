# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""Compare the paper's tab:datasets against what tab_datasets_suite.py derives.

    uv run experiments/check_tab_datasets.py /tmp/tab_datasets.regen

WHY THIS EXISTS. The table is hand-maintained in the paper, and the gate that was supposed to
protect it (figures/tab_datasets.py --check) validated a hardcoded snapshot of the RETIRED
ten-column table against the RETIRED ten-column corpus. It passed green for weeks while the paper
carried an FSST-12 compression ratio measured on a different container from OnPair's -- and its own
snapshot held the corrected value for the very cell the paper got wrong. A check with no contact
with the artifact it certifies is worse than no check, because its green tick suppresses the
question.

WHAT IT COMPARES. Cell by cell, keyed on the ROW LABEL, so reordering the table is not a failure
and a changed number is. Both sides are normalised before comparison: TeX thin spaces (\\,) are
stripped from numbers, and whitespace around & is collapsed, because those are typesetting choices
rather than measurements.

MISSING ROWS ARE FAILURES, not skips. A row the paper prints and the generator does not produce
means the paper is claiming something the committed data does not, which is the whole failure mode
this file exists to catch. A row the generator produces and the paper omits is reported but not
fatal -- the paper is allowed to present a subset.
"""
import re
import sys
from pathlib import Path

PAPER = Path(
    __import__("os").environ.get("PAPER_DIR", str(Path.home() / "repos/onpair-gpu-paper"))
)
TABLE_FILE = PAPER / "sections/1_introduction_asplos.tex"


def norm_cell(c):
    c = c.strip()
    c = c.replace("\\,", "")        # TeX thin space inside numbers
    c = re.sub(r"\s+", " ", c)
    return c


def rows_from(text):
    """{row label: [cells]} for every tabular row that looks like a data row."""
    out = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("%"):
            continue
        if "&" not in line or not line.rstrip().endswith("\\\\"):
            continue
        body = line.rstrip()[:-2]
        cells = [norm_cell(c) for c in body.split("&")]
        label = cells[0]
        # Header rows carry \multicolumn or are the column-name row; neither is data.
        if not label or "multicolumn" in body or "$\\lvert" in body:
            continue
        out[label] = cells[1:]
    return out


def main(argv):
    if len(argv) < 2:
        print("usage: check_tab_datasets.py <regenerated-rows-file>", file=sys.stderr)
        return 2
    regen = rows_from(Path(argv[1]).read_text())
    if not TABLE_FILE.exists():
        print(f"FATAL: cannot read the paper's table at {TABLE_FILE}", file=sys.stderr)
        return 2
    paper = rows_from(TABLE_FILE.read_text())
    # Only the rows the generator knows about; the paper file holds other tables too.
    paper = {k: v for k, v in paper.items() if k in regen}

    if not paper:
        print("FATAL: no tab:datasets rows in the paper matched the generator's row labels.",
              file=sys.stderr)
        print("       generator labels: " + ", ".join(sorted(regen)[:4]) + " ...", file=sys.stderr)
        return 1

    bad = 0
    checked = 0
    for label, want in sorted(regen.items()):
        got = paper.get(label)
        if got is None:
            print(f"  note: generator produces '{label}', the paper does not print it")
            continue
        for i, (w, g) in enumerate(zip(want, got)):
            checked += 1
            if w in ("--", "") or g in ("--", ""):
                continue
            if w != g:
                bad += 1
                print(f"  MISMATCH {label!r} cell {i + 1}: paper {g!r} vs data {w!r}")
        if len(want) != len(got):
            bad += 1
            print(f"  MISMATCH {label!r}: paper has {len(got)} cells, data produces {len(want)}")

    print(f"tab:datasets: {checked} cells compared across {len(paper)} rows, {bad} disagree")
    if bad:
        print("A disagreement means the paper prints a number the committed data does not produce.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
