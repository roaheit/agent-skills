# Survivorship strategies (reference)

Survivorship is the step that picks, for each attribute, the single value that
survives into the golden record from a cluster of matched source records. This
file explains each strategy, how ties are broken, and when to reach for it.

Two framing ideas:

- **Attribute-level (best-of-breed) survivorship**, used here, decides each
  field independently, so the golden record can be an assembly of values from
  different sources. This usually beats **record-level survivorship** (pick one
  whole record to survive), which throws away good values that happen to live on
  an otherwise-weaker record.
- **Missing values never compete.** `null`, empty strings, and whitespace-only
  strings are treated as absent: they cannot win and cannot break a tie. This
  keeps a source from "winning" a field just by being blank.

## Trust ranking

Most strategies fall back to source trust to break ties, so the
`source_trust` list is the single most important part of the config. It is an
ordered list, highest trust first:

```json
"source_trust": ["CRM", "ERP", "WEB"]
```

Sources not in the list rank below every listed source (they are least
trusted), so an unexpected source never silently outranks a known one.

## Strategies

### most_trusted_source

Take the value from the highest-ranked source that actually has one. Skips
sources whose value is missing, so a trusted-but-blank source does not suppress
a good value from a lower source.

Use for authoritative, slow-changing attributes: legal name, party id, country
of registration — fields where "who said it" matters more than "when."

### most_recent

Take the value from the record with the latest `timestamp_field`. Records
without a timestamp are considered only if no record in the cluster has one;
ties on timestamp fall back to trust.

Timestamps are compared as strings and therefore **must be ISO-8601**
(`2026-06-20T18:45:00Z`), which sorts chronologically. Normalise formats before
merging or recency will be wrong.

Use for fast-changing attributes: contact details, address, status, current
tier.

### most_frequent

Take the value the most source records agree on (a simple vote). Ties between
values are broken by picking the tied value held by the most trusted source.

Use for categoricals where agreement is signal: segment, tier, classification
codes, country. Weak when one source is duplicated across systems, since that
inflates its vote — prefer trust or recency there.

### most_complete

Take the richest value. For strings that means the longest non-empty value; for
other types every present value is equally complete, so trust breaks the tie.

Use where more content is usually better: full phone with country code, full
address line, complete free-text description. Watch for junk that is long but
wrong (e.g. an address field stuffed with notes).

### longest

Alias of `most_complete`, named for readability when the intent is explicitly
"keep the longest string" (descriptions, notes).

### max / min / sum

Numeric aggregates computed across all numeric values in the cluster. The
surviving value is `computed` (not attributable to one source), and the audit
records that. Non-numeric values are ignored; if none are numeric, the rule
fails safe to `most_trusted_source` and the audit rule notes the fallback.

Use for measures: `max` lifetime value, `min` risk rating, `sum` of balances
across accounts. Do not use for identifiers or codes that merely look numeric
(a summed customer number is nonsense) — use `most_trusted_source` for those.

## Choosing a strategy: quick heuristics

- Identifier or authoritative fact → `most_trusted_source`
- Changes over time, latest is truth → `most_recent`
- Consensus across systems is meaningful → `most_frequent`
- More text is better → `most_complete` / `longest`
- A real measurement to roll up → `max` / `min` / `sum`

When unsure, `most_trusted_source` is the safest default: it is explainable in
one sentence ("came from our system of record") and never invents a value.

## Reading the audit

Every attribute in the output carries an audit entry:

```json
"email": {
  "value": "priya.sharma@new-domain.com",
  "source": "WEB",
  "record_id": "WEB-889",
  "rule": "most_recent",
  "candidates_considered": 2
}
```

`candidates_considered` counts only records that held a non-missing value, so a
low number on an important field is a signal the golden value rests on thin
evidence — worth surfacing to a steward.
