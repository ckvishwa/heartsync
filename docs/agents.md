# Agents, explained simply

## What is an agent?

Think of Claude as the boss and an agent as a **helper you send into another room**.
The helper does one job, works alone, and comes back with a short report. The mess it
makes stays in that room, so your main chat stays tidy.

A **skill** is different: it is a recipe card Claude reads and follows itself. See
`docs/skills.md`.

## How do I use one?

Just ask by name:

> "Use the cavecrew-investigator agent to find where `WifiStore` is used."

Type `/agents` to see who is available.

Agents only **report back**. You (or Claude) then make the changes.

## The helpers we have (10)

Checked against the loaded session on 2026-11-16 (9 plugins).

| Helper | What it does, in plain words | Do we need it? |
|---|---|---|
| `caveman:cavecrew-investigator` | Read-only. Answers "where is X defined", "what calls Y" with a short file:line list | **Yes**, cheap code lookups |
| `caveman:cavecrew-builder` | Makes a small edit in 1-2 files (typo, rename, one-function rewrite). Refuses bigger jobs | Handy for tiny fixes |
| `caveman:cavecrew-reviewer` | Reviews a diff, one line per finding, with severity | **Yes**, quick pre-commit check |
| `Explore` | Read-only search across many files and folders | Handy for wide searches |
| `Plan` | Designs a step-by-step implementation plan and names critical files | **Yes**, before Phase 3 |
| `general-purpose` | Does multi-step research or work when no other helper fits | Fallback |
| `claude` | Catch-all default helper | Fallback |
| `claude-code-guide` | Answers questions about Claude Code, the Agent SDK and the Claude API | Only when asking about the tool |
| `statusline-setup` | Sets up the Claude Code status line | One-off |
| `web-fetch` | Reads a public web page and reports the answer | Handy for docs lookups |

## Gaps (agents the old doc listed that are NOT loaded)

The earlier version of this file listed `test-architect`, `test-debugger`,
`migration-planner`, `memory-analyst`, `skill-extractor`, `cs-product-orchestrator`,
`cs-design-qa`, `devils-advocate` and `cs-arquiteto`. They came from the
`engineering-skills`, `product-skills` and `c-level-skills` plugins, which are **not
installed now**. The `/pw:*` and `/si:*` commands went with them. Use these instead:

| Missing | Use instead |
|---|---|
| `devils-advocate` | `superpowers:brainstorming`, or the `Plan` agent |
| `cs-design-qa` | `playwright-cli` or `claude-in-chrome` skill to open the screen and check it |
| `test-architect`, `test-debugger` | `playwright-cli` plus `superpowers:systematic-debugging` and `superpowers:test-driven-development` |
| `cs-product-orchestrator` | `prd-writing`, `roadmap-planning`, `mvp-scoping` skills |
| `migration-planner`, `cs-arquiteto` | Not needed (no Cypress or Selenium, no company-level work) |
| `memory-analyst`, `skill-extractor` | `caveman:caveman-compress` for memory files, `skill-creator` for new skills |

To bring the old agents back, reinstall those three plugins, then update this file.

## Our own reviewers (they are skills)

They work in their own room (`context: fork`). Call them like a command:

- `/firmware-reviewer` after changing `firmware/`
- `/cloud-rules-auditor` after changing `cloud/`
- `/hardware-safety-reviewer` after changing `docs/hardware/`, `cad/`, or power code

Other project skills: `/bringup-check`, `/new-adr`, `/release-firmware`.

## Quick picture

```
You ──ask──▶ Claude (boss)
                │  sends a helper
                ▼
          Agent works alone ──short report──▶ Claude ──▶ You
```
