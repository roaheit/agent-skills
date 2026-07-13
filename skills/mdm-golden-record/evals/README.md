# Evals

A small, runnable test suite that proves the survivorship engine does what the
skill claims. Each case is a real merge scenario with a hand-verified expected
result, so the skill can be changed with confidence and regressions get caught.

## Run

```bash
python run_evals.py
```

Exits non-zero if any case fails, so it can gate CI.

## Layout

```
cases/
  01-customer-merge/
    input.json      # { config, clusters } fed to survivorship.py
    expected.json   # { clusters: [ { golden_record, sources } ] }
  02-supplier-merge/
    ...
```

The runner runs `scripts/survivorship.py` on each `input.json` and checks two
things against `expected.json`: the golden record values, and the winning source
for each attribute (from the audit trail). It deliberately does **not** assert on
`master_id` or candidate counts, so the tests stay robust to harmless internal
changes.

## What each case covers

- **01-customer-merge** — the five headline strategies on one clean cluster:
  `most_trusted_source`, `most_recent`, `most_complete`, `most_frequent`, `max`.
- **02-supplier-merge** — edge cases: a `most_frequent` tie broken by trust, a
  `most_recent` winner when some records lack timestamps, `min` aggregation, an
  attribute empty across every record (survives as null), the `default_strategy`
  applying to unconfigured fields, and a singleton cluster.

## Adding a case

1. Create `cases/NN-name/input.json` with a `config` and `clusters`.
2. Work out the correct golden values and winning sources by hand.
3. Save them to `cases/NN-name/expected.json` in the `{ clusters: [...] }` shape.
4. Run `python run_evals.py`.

Deriving `expected.json` by hand (not by copying the script's output) is the
point — it keeps the tests an independent check on the logic.
