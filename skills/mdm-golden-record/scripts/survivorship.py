#!/usr/bin/env python3
"""Deterministic golden-record survivorship engine.

Takes clusters of matched source records plus a survivorship config and
produces one golden record per cluster, together with a full audit trail
explaining -- for every attribute -- which value won, from which source
record, and by which rule.

Why a script and not the model: survivorship must be deterministic,
repeatable, and auditable. The same inputs must always yield the same
golden record, and every surviving value must be explainable to a data
steward or an auditor. Re-deriving merge logic as free text fails all
three properties. Reserve the model for judgment (mapping schemas,
proposing rules, explaining genuine conflicts) and let this handle the
merge.

Stdlib only. No network access or package installation required.

Usage:
    python survivorship.py --input input.json [--config config.json] [--output out.json]

Input JSON shape:
    {
      "config":   { ...see references/survivorship-strategies.md... },
      "clusters": [ [ {record}, {record}, ... ], [ ... ] ]
    }
"""

import argparse
import hashlib
import json
import sys
from collections import Counter

STRATEGIES = {
    "most_trusted_source",
    "most_recent",
    "most_frequent",
    "most_complete",
    "longest",
    "max",
    "min",
    "sum",
}


def is_missing(value):
    """A value is missing if it is None or an empty/whitespace string."""
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    return False


def norm_str(value):
    return value.strip() if isinstance(value, str) else value


def source_rank(record, cfg):
    """Lower rank == higher trust. Unknown/unlisted sources rank last."""
    src = record.get(cfg["source_field"])
    order = cfg.get("source_trust", [])
    return order.index(src) if src in order else len(order)


def candidates(records, attr, cfg):
    """Records holding a usable (non-missing) value for attr, with metadata."""
    out = []
    for r in records:
        val = r.get(attr)
        if is_missing(val):
            continue
        out.append(
            {
                "value": norm_str(val),
                "source": r.get(cfg["source_field"]),
                "record_id": r.get(cfg["id_field"]),
                "rank": source_rank(r, cfg),
                "timestamp": r.get(cfg.get("timestamp_field")),
            }
        )
    return out


def pick_most_trusted(cands):
    return sorted(cands, key=lambda c: c["rank"])[0]


def pick_most_recent(cands):
    # Prefer records that actually carry a timestamp; assumes ISO-8601 strings
    # (lexicographically sortable). Ties on timestamp fall back to trust.
    with_ts = [c for c in cands if c["timestamp"] is not None]
    pool = with_ts if with_ts else cands
    return max(pool, key=lambda c: (c["timestamp"] or "", -c["rank"]))


def pick_most_frequent(cands):
    counts = Counter(c["value"] for c in cands)
    top = max(counts.values())
    tied = {v for v, n in counts.items() if n == top}
    # Tie-break: among records holding a tied value, pick the most trusted.
    return min((c for c in cands if c["value"] in tied), key=lambda c: c["rank"])


def pick_most_complete(cands):
    # "Most complete" at attribute level == richest value. For strings that is
    # the longest non-empty value; other types are equally complete once
    # present, so trust breaks the tie.
    def completeness(c):
        return len(c["value"]) if isinstance(c["value"], str) else 1

    return max(cands, key=lambda c: (completeness(c), -c["rank"]))


def numeric_values(cands):
    nums = []
    for c in cands:
        try:
            nums.append(float(c["value"]))
        except (TypeError, ValueError):
            continue
    return nums


def _coerce(num):
    return int(num) if float(num).is_integer() else num


def _audit(winner, rule, cands):
    return {
        "value": winner["value"],
        "source": winner["source"],
        "record_id": winner["record_id"],
        "rule": rule,
        "candidates_considered": len(cands),
    }


def resolve_attribute(records, attr, strategy, cfg):
    cands = candidates(records, attr, cfg)
    if not cands:
        return {
            "value": None,
            "source": None,
            "record_id": None,
            "rule": strategy,
            "note": "no non-null values in cluster",
            "candidates_considered": 0,
        }

    if strategy in ("max", "min", "sum"):
        nums = numeric_values(cands)
        if not nums:
            # Non-numeric data under a numeric rule: fail safe to trust, and
            # say so in the audit rather than silently dropping the value.
            winner = pick_most_trusted(cands)
            return _audit(winner, "most_trusted_source (fallback: non-numeric)", cands)
        agg = {"max": max, "min": min, "sum": sum}[strategy](nums)
        return {
            "value": _coerce(agg),
            "source": "computed",
            "record_id": None,
            "rule": strategy,
            "candidates_considered": len(cands),
        }

    picker = {
        "most_trusted_source": pick_most_trusted,
        "most_recent": pick_most_recent,
        "most_frequent": pick_most_frequent,
        "most_complete": pick_most_complete,
        "longest": pick_most_complete,
    }[strategy]
    return _audit(picker(cands), strategy, cands)


def master_id(records, cfg):
    """Stable, deterministic master id derived from contributing source keys."""
    ids = sorted(str(r.get(cfg["id_field"])) for r in records)
    digest = hashlib.sha256("|".join(ids).encode()).hexdigest()[:12]
    return f"MDM-{digest}"


def build(data):
    cfg = data["config"]
    default = cfg.get("default_strategy", "most_trusted_source")
    attr_cfg = cfg.get("attributes", {})
    control = {cfg["id_field"], cfg["source_field"], cfg.get("timestamp_field")}

    results = []
    for cluster in data["clusters"]:
        # Attribute set = every non-control field seen anywhere in the cluster,
        # in first-seen order (stable across runs).
        attrs = []
        for r in cluster:
            for k in r:
                if k not in control and k not in attrs:
                    attrs.append(k)

        golden, trail = {}, {}
        for a in attrs:
            strat = attr_cfg.get(a, {}).get("strategy", default)
            if strat not in STRATEGIES:
                strat = default
            res = resolve_attribute(cluster, a, strat, cfg)
            golden[a] = res["value"]
            trail[a] = res

        results.append(
            {
                "master_id": master_id(cluster, cfg),
                "golden_record": golden,
                "source_record_ids": sorted(
                    str(r.get(cfg["id_field"])) for r in cluster
                ),
                "audit": trail,
            }
        )
    return {"golden_records": results}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--input", required=True, help="JSON with {config, clusters}")
    p.add_argument("--config", help="Optional config JSON; overrides embedded config")
    p.add_argument("--output", help="Write result here; defaults to stdout")
    args = p.parse_args(argv)

    with open(args.input, encoding="utf-8") as f:
        data = json.load(f)
    if args.config:
        with open(args.config, encoding="utf-8") as f:
            data["config"] = json.load(f)
    if "config" not in data or "clusters" not in data:
        sys.exit("Input must contain both 'config' and 'clusters'.")

    text = json.dumps(build(data), indent=2, ensure_ascii=False)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text + "\n")
    else:
        print(text)


if __name__ == "__main__":
    main()
