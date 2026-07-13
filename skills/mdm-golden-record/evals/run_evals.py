#!/usr/bin/env python3
"""Run the mdm-golden-record evaluation suite.

For each case under evals/cases/, runs scripts/survivorship.py on input.json and
compares the produced golden values and winning sources against expected.json.
Exits non-zero if any case fails, so this can gate CI.

Usage:
    python evals/run_evals.py
"""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SURVIVORSHIP = ROOT / "scripts" / "survivorship.py"
CASES = Path(__file__).resolve().parent / "cases"


def run_case(case_dir):
    proc = subprocess.run(
        [sys.executable, str(SURVIVORSHIP), "--input", str(case_dir / "input.json")],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return False, [f"script error: {proc.stderr.strip()}"]

    actual = json.loads(proc.stdout)["golden_records"]
    expected = json.loads((case_dir / "expected.json").read_text())["clusters"]

    failures = []
    if len(actual) != len(expected):
        return False, [f"cluster count: got {len(actual)}, want {len(expected)}"]

    for i, (got, want) in enumerate(zip(actual, expected)):
        if got["golden_record"] != want["golden_record"]:
            failures.append(
                f"cluster {i} golden_record:\n    got  {got['golden_record']}\n"
                f"    want {want['golden_record']}"
            )
        got_sources = {a: got["audit"][a]["source"] for a in want["sources"]}
        if got_sources != want["sources"]:
            failures.append(
                f"cluster {i} winning sources:\n    got  {got_sources}\n"
                f"    want {want['sources']}"
            )
    return len(failures) == 0, failures


def main():
    case_dirs = sorted(d for d in CASES.iterdir() if d.is_dir())
    if not case_dirs:
        sys.exit("no eval cases found")

    all_passed = True
    for case_dir in case_dirs:
        passed, failures = run_case(case_dir)
        mark = "PASS" if passed else "FAIL"
        print(f"[{mark}] {case_dir.name}")
        for f in failures:
            print(f"       {f}")
        all_passed = all_passed and passed

    print()
    if all_passed:
        print(f"All {len(case_dirs)} cases passed.")
    else:
        print("Some cases failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
