# agent-skills

Practitioner-grade [Agent Skills](https://agentskills.io) for **enterprise data
engineering and governance** — the parts of the job that are hard to get right
and scarce in the current skill ecosystem: master data, data quality, pipelines,
lineage, and AI/data governance.

Every skill here is built to the same bar: a tuned, trigger-rich description;
progressive disclosure so it stays cheap in context; deterministic scripts where
correctness and auditability matter; and a runnable eval suite so it actually
works instead of merely looking plausible.

## Why these, and why this way

The skill ecosystem is enormous but shallow — most published skills duplicate a
narrow set of generic tasks, and many go uninstalled. The gap is
**domain-specific, expert-authored** skills that encode judgment a general model
doesn't have. That's what this collection is: the how-to layer of real data
work, packaged so an agent can execute it consistently.

Skills follow the open SKILL.md standard, so they work across Claude Code, the
Claude API, Codex, Gemini CLI, Cursor, GitHub Copilot, and other compatible
agents. The format is a shared language; discovery and invocation differ
slightly per platform.

## Skills

| Skill | What it does | Status |
| --- | --- | --- |
| [`mdm-golden-record`](skills/mdm-golden-record) | Golden records via survivorship rules + entity matching, with a full audit trail | ✅ Available |
| `data-quality-rules` | Profile a dataset and emit DQ checks as dbt tests / Great Expectations / Soda | 🛠 Planned |
| `data-contract-authoring` | Generate and validate data contracts (schema, semantics, SLAs, ownership) | 🛠 Planned |
| `snowflake-task-dag` | Build and reason about Snowflake task DAGs: dependencies, error handling, resumption | 🛠 Planned |
| `data-lineage-docs` | Turn pipeline definitions into reviewable lineage documentation | 🛠 Planned |
| `ai-governance-readiness` | Model cards, risk classification, and audit-ready docs for AI/data governance | 🛠 Planned |

## Install

Skills are plain-text folders. Drop the skill directory into your agent's skills
location; the agent loads it on demand when a task matches its description.

| Agent | Location |
| --- | --- |
| Claude Code (personal) | `~/.claude/skills/` |
| Claude Code (project, shared via git) | `.claude/skills/` |
| Codex | `~/.codex/skills/` or `.codex/skills/` |
| Copilot / others | `.github/skills/` (see the agent's docs) |

For example, to install the MDM skill for Claude Code:

```bash
git clone https://github.com/<you>/agent-skills
cp -r agent-skills/skills/mdm-golden-record ~/.claude/skills/
```

On the Claude API and claude.ai, upload the skill folder per the
[Agent Skills docs](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview).

## Security

Skills are readable text and bundled scripts — nothing runs until an agent
executes it. **Read a skill before you load it.** Everything here is stdlib-only
Python with no network calls, so you can audit each script end to end. Treat
skills the way you'd treat any dependency in a supply chain: inspect, pin, and
review updates.

## Contributing

New data/governance skills are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md)
for the quality bar and structure. Start from
[`_templates/SKILL.template.md`](_templates/SKILL.template.md).

## License

[MIT](LICENSE).
