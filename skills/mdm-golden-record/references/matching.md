# Matching (reference)

Matching (a.k.a. identity resolution or record linkage) groups source records
that describe the same real-world entity into clusters. Survivorship runs
afterwards on each cluster. Get matching wrong and survivorship faithfully
merges the wrong things, so this step deserves care.

## How `match.py` works

1. **Blocking** partitions records into candidate groups that share a blocking
   key, so only records in the same block are ever compared. This is what keeps
   the work tractable on real volumes (all-pairs comparison is O(n²)).
2. **Pairwise scoring** compares each pair within a block across the configured
   attributes and produces a weighted average similarity in `[0, 1]`.
3. **Clustering** unions every pair scoring at or above `threshold`
   (union-find), so transitive matches (a≈b, b≈c ⇒ a,b,c) land in one cluster.

## Config

```json
{
  "id_field": "record_id",
  "blocking_keys": ["postal_code"],
  "threshold": 0.8,
  "comparisons": [
    { "attribute": "name",  "method": "fuzzy",  "weight": 0.5 },
    { "attribute": "email", "method": "exact",  "weight": 0.3 },
    { "attribute": "phone", "method": "digits", "weight": 0.2 }
  ]
}
```

### Blocking keys

Choose a key that is **stable and rarely wrong** for records that truly match —
postal code, email domain, birth year, first three letters of a surname. Two
records that should match but disagree on the blocking key will never be
compared, so a volatile or dirty key silently costs recall.

Leave `blocking_keys` empty to compare all pairs. That is fine for small inputs
and eval fixtures, but scales poorly.

### Comparison methods

- **exact** — normalised equality (case, whitespace folded). Score 1.0 or 0.0.
  Best for emails, codes, government ids.
- **fuzzy** — normalised string similarity via `difflib.SequenceMatcher`.
  Tolerant of typos, casing, spacing. Best for names and free text.
- **digits** — strips non-digits and compares the last 10 digits, so country
  and area prefixes don't sink an otherwise-identical phone number.

### Weights and the score

Weights express how much each attribute should count. The score is a weighted
average over only the attributes present on **both** records, so a field that
is missing on one side is excluded rather than scored as a mismatch. If no
comparable attribute exists for a pair, the score is 0.

## Tuning the threshold (precision vs recall)

The threshold is the safety dial:

- **Higher (e.g. 0.85+)** → fewer false merges (higher precision). Two distinct
  entities are less likely to be fused. Cost: more true duplicates missed.
- **Lower (e.g. 0.65)** → catches more duplicates (higher recall). Cost: more
  false merges, which are expensive to unpick and can leak data between
  entities.

For governed master data, bias toward precision and review the borderline band
by hand. Tune against a **labelled sample** of known match / non-match pairs
rather than by feel: sweep the threshold, and pick the point where precision
meets your risk tolerance.

## Deterministic vs probabilistic matching

`match.py` is a transparent, rule-weighted matcher: every decision is
inspectable and reproducible, which is what governance usually needs. Fully
probabilistic approaches (e.g. Fellegi–Sunter / EM-estimated match weights) can
squeeze out more accuracy on large, messy datasets but are harder to explain
and audit. Start here; graduate to a probabilistic engine only when a labelled
evaluation shows this one leaving real matches on the table.

## Failure modes to watch

- **Over-merging.** A cluster that clearly contains two different entities means
  the threshold is too low or a comparison is too permissive. Fix it here —
  never try to survivor your way out of a bad cluster.
- **Under-merging.** Obvious duplicates left in separate clusters usually means
  a bad blocking key kept them from ever being compared.
- **Prefix-heavy identifiers.** Phone/tax numbers with country prefixes need the
  `digits` method (or normalisation) or exact comparison will fail spuriously.
