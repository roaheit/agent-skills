# mdm-golden-record

An agent skill for building **golden records** from duplicate/matched source
records using configurable survivorship rules, and for resolving entity
duplicates via deterministic + fuzzy matching. Every surviving value comes with
an audit trail explaining which source it came from and why.

Built for real MDM work: customer / supplier / product / party consolidation
across multiple source systems, where the merge has to be reproducible and
defensible to a data steward or auditor.

## What's in the box

```
mdm-golden-record/
├── SKILL.md                     # what the agent reads
├── scripts/
│   ├── survivorship.py          # deterministic golden-record builder + audit
│   └── match.py                 # entity matching -> clusters
├── references/
│   ├── survivorship-strategies.md
│   └── matching.md
└── evals/
    ├── run_evals.py             # runnable test suite
    └── cases/                   # input.json + hand-verified expected.json
```

## Requirements

Python 3.8+. **Standard library only** — no `pip install`, no network. The
scripts run unchanged in a code-execution sandbox or on your laptop.

## Quickstart

Merge already-matched clusters into golden records:

```bash
python scripts/survivorship.py \
  --input evals/cases/01-customer-merge/input.json
```

Match raw records into clusters first, then merge:

```bash
python scripts/match.py --input raw_records.json --output clusters.json
# add a "config" block to clusters.json, then:
python scripts/survivorship.py --input clusters.json --output golden.json
```

## Using it as a skill

Drop the `mdm-golden-record/` folder into your agent's skills directory (see the
repo root README for per-platform paths). The agent loads it automatically when
a task involves master data, survivorship, matching, or deduplication.

## Run the tests

```bash
python evals/run_evals.py
```

## Configuration

The survivorship config (source trust, per-attribute strategy) is documented in
[`references/survivorship-strategies.md`](references/survivorship-strategies.md);
the matching config in [`references/matching.md`](references/matching.md).

## License

MIT — see the repository root `LICENSE`.
