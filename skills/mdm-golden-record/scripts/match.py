#!/usr/bin/env python3
"""Entity matching -> clusters ready for survivorship.

Groups source records that refer to the same real-world entity. Optional
blocking cuts the comparison space; within each block, a weighted similarity
score across configured attributes decides pairwise matches, and union-find
turns those pairs into clusters. Output feeds directly into survivorship.py.

Design notes:
  * Blocking trades a little recall for a large speed win. Only records that
    share a blocking key are ever compared, so choose a key that is stable and
    rarely wrong (e.g. postal code, email domain), never the field you are
    trying to resolve.
  * Similarity is averaged only over attributes present on *both* records, so a
    missing field neither helps nor hurts the score.
  * The threshold is the precision/recall dial. Higher = fewer false merges
    (safer for governance), lower = fewer missed duplicates. Tune it against a
    labelled sample; see references/matching.md.

Stdlib only (difflib for fuzzy string similarity). No install required.

Usage:
    python match.py --input records.json [--output clusters.json]

Input JSON shape:
    { "config": { ...see references/matching.md... }, "records": [ {..}, {..} ] }
Output JSON shape:
    { "clusters": [ [ {record}, ... ], ... ] }   # ready for survivorship.py
"""

import argparse
import json
import re
import sys
from difflib import SequenceMatcher
from itertools import combinations


def norm(v):
    return re.sub(r"\s+", " ", str(v).strip().lower()) if v is not None else ""


def only_digits(v):
    return re.sub(r"\D", "", str(v)) if v is not None else ""


def sim_exact(a, b):
    na = norm(a)
    return 1.0 if na and na == norm(b) else 0.0


def sim_fuzzy(a, b):
    na, nb = norm(a), norm(b)
    if not na or not nb:
        return 0.0
    return SequenceMatcher(None, na, nb).ratio()


def sim_digits(a, b):
    # Compare on the last 10 digits so country/area prefixes don't sink a match.
    da, db = only_digits(a)[-10:], only_digits(b)[-10:]
    if not da or not db:
        return 0.0
    return 1.0 if da == db else SequenceMatcher(None, da, db).ratio()


METHODS = {"exact": sim_exact, "fuzzy": sim_fuzzy, "digits": sim_digits}


def pair_score(r1, r2, comparisons):
    total_w, acc = 0.0, 0.0
    for c in comparisons:
        attr = c["attribute"]
        method = c.get("method", "fuzzy")
        weight = c.get("weight", 1.0)
        v1, v2 = r1.get(attr), r2.get(attr)
        if v1 in (None, "") or v2 in (None, ""):
            continue  # attribute absent on one side: excluded from the average
        total_w += weight
        acc += weight * METHODS[method](v1, v2)
    return acc / total_w if total_w else 0.0


def block_key(record, keys):
    return tuple(norm(record.get(k)) for k in keys) if keys else ("__all__",)


class UnionFind:
    def __init__(self, n):
        self.parent = list(range(n))

    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[ra] = rb


def match(data):
    cfg = data["config"]
    records = data["records"]
    comparisons = cfg["comparisons"]
    threshold = cfg.get("threshold", 0.8)
    blocking = cfg.get("blocking_keys", [])
    id_field = cfg.get("id_field", "record_id")

    uf = UnionFind(len(records))
    blocks = {}
    for i, r in enumerate(records):
        blocks.setdefault(block_key(r, blocking), []).append(i)

    for idxs in blocks.values():
        for i, j in combinations(idxs, 2):
            if pair_score(records[i], records[j], comparisons) >= threshold:
                uf.union(i, j)

    groups = {}
    for i in range(len(records)):
        groups.setdefault(uf.find(i), []).append(records[i])

    # Stable ordering: clusters sorted by their smallest source id.
    clusters = sorted(
        groups.values(),
        key=lambda g: min(str(r.get(id_field)) for r in g),
    )
    return {"clusters": clusters}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--input", required=True, help="JSON with {config, records}")
    p.add_argument("--output", help="Write clusters here; defaults to stdout")
    args = p.parse_args(argv)

    with open(args.input, encoding="utf-8") as f:
        data = json.load(f)
    if "config" not in data or "records" not in data:
        sys.exit("Input must contain both 'config' and 'records'.")

    text = json.dumps(match(data), indent=2, ensure_ascii=False)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text + "\n")
    else:
        print(text)


if __name__ == "__main__":
    main()
