# Contributing

New skills for enterprise data engineering and governance are welcome. To keep
the collection best-in-class, every skill must clear the same bar. Start from
[`_templates/SKILL.template.md`](_templates/SKILL.template.md).

## The quality bar

**1. The description is the whole game for adoption.** An agent selects a skill
almost entirely from its `description`. Write it in the third person, state both
what the skill does *and* the concrete triggers that should fire it, and lean
slightly pushy — models tend to under-trigger. List the synonyms real users say
(e.g. "dedup", "record linkage", "best-of-breed merge"), not just the canonical
term.

**2. Be concise; use progressive disclosure.** Keep `SKILL.md` under ~500 lines.
Move depth into reference files and link them one level deep. Only include what
the model doesn't already know — skip generic background, keep your specific
rules and gotchas.

**3. Explain the why; don't shout rules.** Prefer "use X because Y" over walls of
`ALWAYS`/`NEVER`. The reasoning lets the agent generalise to cases you didn't
enumerate. Reserve bare imperatives for genuinely fragile steps.

**4. Push determinism into scripts.** Anything that must be correct, repeatable,
or auditable belongs in a script the agent runs, not in prose it re-derives. Keep
scripts stdlib-only where possible (no network, no install) so they run in any
sandbox; if a dependency is unavoidable, list it explicitly in `SKILL.md`.

**5. Ship evals.** Include an `evals/` suite with real input/output cases and a
runner that exits non-zero on failure. Derive expected outputs by hand, not by
copying the script's output, so the tests are an independent check.

**6. Mind security and PII.** No network calls unless essential and documented.
Don't log or persist PII by default. Skills are a supply chain — keep them
auditable.

## Structure

```
skills/<skill-name>/
├── SKILL.md            # gerund or noun-phrase name; tuned description
├── README.md           # human-facing
├── scripts/            # deterministic helpers (stdlib preferred)
├── references/         # depth, linked one level deep from SKILL.md
└── evals/
    ├── run_evals.py
    └── cases/
```

Naming: prefer clear, specific skill names (`data-quality-rules`,
`snowflake-task-dag`). Avoid time-sensitive content and OS-specific paths inside
`SKILL.md`.

## Before you open a PR

- [ ] Description states what + when, third person, with real trigger words
- [ ] `SKILL.md` under ~500 lines; references linked one level deep
- [ ] Scripts run with stdlib only (or dependencies documented)
- [ ] `python evals/run_evals.py` passes
- [ ] Added a row to the Skills table in the root `README.md`
