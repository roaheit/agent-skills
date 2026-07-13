---
name: skill-name-here
description: >-
  One or two sentences on WHAT this skill does, followed by the concrete
  triggers for WHEN to use it. Third person. List the real words users say,
  including synonyms, and lean slightly pushy: "Use this whenever the user
  mentions X, Y, or Z -- even if they don't explicitly ask for it." The
  description is what the agent uses to pick this skill from many, so make it
  earn selection.
---

# Skill Name

One line on the outcome this skill produces.

## The principle that shapes this skill

State the core idea the agent must hold onto (e.g. "do the merge in the script,
not in your head, because it must be auditable"). Explain the *why* — that is
what lets the agent handle cases you didn't spell out. Note the runtime
requirements here (e.g. "stdlib only, no network or install").

## Workflow

Numbered steps the agent should follow. Call out any step it must not skip and
why. Keep judgment with the agent and mechanics in the scripts.

1. ...
2. ...

## Configuration / inputs

Show the minimal config or input shape as a code block. Point to a reference
file for the full detail rather than inlining it all.

## Running the scripts

```bash
python scripts/<script>.py --input input.json --output output.json
```

Describe the output shape and, importantly, the audit/explanation it produces.

## When to stop and ask the user

List the situations where the rules resolve mechanics but not meaning, and the
agent should escalate rather than silently commit.

## Gotchas

Short, specific pitfalls (nulls vs zeros, formats, precision/recall, PII). These
are the hard-won details that make the skill trustworthy.

## References

- `references/<topic>.md` — what it covers and when the agent should read it.
