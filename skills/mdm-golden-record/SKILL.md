---
name: mdm-golden-record
description: >-
  Builds golden records from duplicate or matched source records using
  configurable survivorship rules, and resolves entity duplicates via
  deterministic and fuzzy matching. Produces an auditable trail showing which
  value won, from which source, and why. Use this whenever the user works with
  master data or MDM, golden records, survivorship or best-of-breed merge,
  entity or identity resolution, deduplication, record linkage/matching, source
  trust ranking, or consolidating customer / product / supplier / party data
  from multiple source systems -- even if they never say "golden record"
  explicitly.
---

# MDM Golden Record

Turn many conflicting source records for the same real-world entity into one
trusted golden record, with a defensible reason for every surviving value.

Two capabilities, run in sequence or independently:

1. **Matching** (`scripts/match.py`) — group records that refer to the same
   entity into clusters.
2. **Survivorship** (`scripts/survivorship.py`) — collapse each cluster into a
   golden record plus an audit trail.

## The one rule that shapes everything here

Do the merge in the script, not in your head. Survivorship has to be
**deterministic, repeatable, and auditable**: the same inputs must always yield
the same golden record, and a data steward or auditor must be able to see why
each value survived. Free-text reasoning satisfies none of those — it is
non-reproducible and unsignable. So the division of labour is:

- **The scripts** own the merge: comparison, scoring, rule application, audit.
- **You** own the judgment: understanding the entity and sources, proposing the
  survivorship config, mapping messy schemas onto it, and explaining or
  escalating genuine conflicts the rules can't settle.

Both scripts are stdlib-only (Python 3.8+, `difflib` for fuzzy similarity). No
network access or package install is required, so they run anywhere.

## Workflow

Follow these steps; do not skip the config confirmation, since the whole result
hinges on it.

1. **Identify the entity and its sources.** What is being mastered (customer,
   supplier, product, patient)? Which source systems contribute, and roughly
   how much do we trust each?
2. **Confirm source trust order with the user.** This ranking drives most
   tie-breaks. Highest-trust source first. Never guess it silently — an
   authoritative-but-stale source is a classic trap (see Gotchas).
3. **Choose a survivorship strategy per attribute.** Map each field to a rule
   (table below; full detail in `references/survivorship-strategies.md`). Set a
   `default_strategy` for anything unlisted.
4. **Get clusters.** If the records are already matched (share an entity id),
   group them and go to step 5. If not, run `match.py` first.
5. **Run `survivorship.py`.** Produce golden records + audit.
6. **Review the audit and surface conflicts.** Read the trail. Where the rules
   made a low-confidence or high-stakes call, tell the user rather than passing
   it off as settled.

## Survivorship strategies

| Strategy              | Surviving value                                        | Typical use                          |
| --------------------- | ------------------------------------------------------ | ------------------------------------ |
| `most_trusted_source` | value from the highest-ranked source that has one      | names, IDs, authoritative attributes |
| `most_recent`         | value from the record with the latest timestamp        | contact details, status, addresses   |
| `most_frequent`       | the value most sources agree on (ties → trust)         | categoricals, tiers, codes           |
| `most_complete`       | the richest value (longest non-empty; ties → trust)    | free-text, phone, address lines      |
| `longest`             | alias of `most_complete`                               | descriptions, notes                  |
| `max` / `min` / `sum` | numeric aggregate across the cluster (source=computed) | balances, scores, counts             |

Missing values (`null`, empty, or whitespace-only) never win and never break a
tie. Details, tie-break order, and pitfalls: `references/survivorship-strategies.md`.

## Config shape

```json
{
  "id_field": "record_id",
  "source_field": "source",
  "timestamp_field": "updated_at",
  "source_trust": ["CRM", "ERP", "WEB"],
  "default_strategy": "most_trusted_source",
  "attributes": {
    "full_name":      { "strategy": "most_trusted_source" },
    "email":          { "strategy": "most_recent" },
    "loyalty_tier":   { "strategy": "most_frequent" },
    "lifetime_value": { "strategy": "max" }
  }
}
```

## Running the scripts

Survivorship, from already-matched clusters:

```bash
python scripts/survivorship.py --input clusters.json --output golden.json
# input:  { "config": {...}, "clusters": [ [ {rec}, {rec} ], ... ] }
# output: { "golden_records": [ { master_id, golden_record, source_record_ids, audit } ] }
```

Matching first, then survivorship (config for matching described in
`references/matching.md`):

```bash
python scripts/match.py --input raw_records.json --output clusters.json
# then hand clusters.json a "config" block and run survivorship.py on it
```

The audit block names, per attribute, the surviving `value`, the `source` and
`record_id` it came from (or `computed` for aggregates), the `rule` applied, and
how many candidates were considered.

## When to stop and ask the user

The rules resolve mechanics, not meaning. Escalate rather than silently commit
when:

- Two equally trusted sources disagree on a **high-stakes** field (legal name,
  tax id, primary email) — a tie-break exists, but the user should decide.
- The `most_recent` winner comes from your **least-trusted** source (fresh but
  dubious data can beat correct-but-older data).
- A cluster looks **over-merged** (a matched group that plainly mixes two
  entities) — fix matching, don't survivor your way out of it.
- A numeric rule silently fell back because the data was **non-numeric** (the
  audit rule will say so).

## Gotchas

- **Nulls vs zeros.** `0`, `false`, and `"0"` are real values, not missing. Only
  `null` / empty / whitespace count as absent.
- **Timestamps must be ISO-8601.** `most_recent` sorts timestamps as strings;
  mixed or non-ISO formats will sort wrong. Normalise before merging.
- **Trust ≠ freshness.** A "system of record" can hold stale values. If recency
  matters for a field, use `most_recent`, not `most_trusted_source`.
- **PII in the audit.** The audit repeats source values. If you persist or log
  it, treat it as containing the same PII as the records and handle accordingly.
- **Matching precision/recall.** A low threshold causes false merges (two people
  become one). For governed data, prefer a higher threshold and review borderline
  pairs. See `references/matching.md`.

## References

- `references/survivorship-strategies.md` — every strategy in depth, tie-break
  order, and when each is the right choice.
- `references/matching.md` — blocking, comparison methods, thresholds, and how
  to tune precision vs recall.
