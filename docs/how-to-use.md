# How to use agents and skills: prompts you can type

Checked against the loaded session on 2026-11-16 (9 plugins, 10 agents).
Copy a prompt, replace the `<...>` parts, and send it.

Two ways to call something:

- **Slash command**: `/<skill-name> <arguments>`. Works for skills only.
- **Plain words**: "Use the `<name>` agent to ..." or "Use the `<name>` skill to ...".
  Works for both agents and skills.

**Skill** = a recipe Claude follows itself, in your chat.
**Agent** = a helper that works in another room and sends back a short report.

---

## 0. Pick by kind of work (start here)

Find the work you are doing, use the tools in that row. The "Gap" column says what the
old plugins gave that is not loaded now.

| Kind of work | Skills to use | Agent to send | Gap / note |
|---|---|---|---|
| **Planning a feature or phase** (product manager role) | `superpowers:brainstorming` first, then `prd-writing`, `mvp-scoping`, `roadmap-planning`, then `superpowers:writing-plans` | `Plan` | No `product-manager-toolkit`. These cover it |
| **Big decision or architecture** | `architecture-design`, `tech-stack-eval`, then `/new-adr <title>` | `Plan` | No `devils-advocate`. Ask `Plan`: "find the 3 biggest holes in this" |
| **App or dashboard UI design** (UI/UX role) | `artifact-design` (look and layout), `theme-factory`, `brand-guidelines`, `canvas-design`, `dataviz` for charts. Figma tools if you have a Figma file | none | No `ui-design-system` or `ux-researcher-designer`. Use Figma or Canva tools for real mockups |
| **UI check before calling it done** | `playwright-cli` or `claude-in-chrome`: open the screen, click everything, look for dead buttons, placeholder text, missing loading/empty/error states | none | No `design-qa`. Give the checklist in the prompt (see below) |
| **Frontend code** (`web/` Next.js, `app/` Flutter) | `superpowers:test-driven-development`, `web-artifacts-builder` for prototypes, `run` to see it working | `cavecrew-builder` for small edits | No `senior-frontend`. Read `web/CLAUDE.md` or `app/CLAUDE.md` first |
| **Backend and cloud** (`cloud/` Functions and rules) | `security-review`, `superpowers:test-driven-development`, then `/cloud-rules-auditor` | `cavecrew-investigator` to find code | Cycle data rules in `docs/protocol.md` always win |
| **Firmware** (`firmware/`) | `superpowers:test-driven-development`, `superpowers:systematic-debugging`, then `/firmware-reviewer` | `cavecrew-investigator` | Native test for any pure logic |
| **Hardware, battery, CAD** | `/bringup-check <part>`, `/hardware-safety-reviewer` | none | No LiPo before Phase 8 |
| **Bug or failing test** | `superpowers:systematic-debugging`, then TDD to fix, then `superpowers:verification-before-completion` | `Explore` if the cause is hard to find | |
| **Test writing** | `superpowers:test-driven-development`, `playwright-cli` for `web/` | none | No `test-architect`. Ask `Plan` to list tests first |
| **Review before merge** | `/caveman:caveman-review`, then `/code-review:code-review <PR#>`, plus the matching reviewer skill | `cavecrew-reviewer` | No `adversarial-reviewer`. Prompt: "review this harshly, assume it is wrong" |
| **Security and privacy** | `security-review`, `/cloud-rules-auditor` | none | Cycle data is health data. Never log it |
| **Docs and handoff** | `doc-coauthoring`, `docs`, update `docs/handoff.md` | none | |
| **Shipping** | `superpowers:verification-before-completion`, `/release-firmware <version>`, `superpowers:finishing-a-development-branch` | none | Never add an unsigned update path |
| **Research a topic** | `deep-research` | `web-fetch` for one page, `general-purpose` for a long job | |

### 0b. Full routing with the reinstalled plugins

Needs `/reload-plugins` first. Names come from the earlier verified plugin docs
(`docs/skills.md`). Use this table in place of the one above where it is more specific.

| Kind of work | Skills | Agent |
|---|---|---|
| **Plan a feature** (product manager) | `product-discovery` (is it worth building), `product-manager-toolkit` (rank, PRD), `product-strategist` (OKRs), `roadmap-communicator`, then `superpowers:writing-plans` | `cs-product-orchestrator`, `Plan` |
| **Challenge a plan or decision** | `adversarial-reviewer`, `named-persona-adversarial-review` | `devils-advocate` |
| **Architecture and ADR** | `senior-architect`, `tech-stack-evaluator`, then `/new-adr <title>` | `Plan` |
| **Tech leadership call** (rewrite or not, team) | `cto-advisor`, `vpe-advisor` | none |
| **UX research and flows** | `ux-researcher-designer` (personas, journey, usability plan) | none |
| **UI design system** | `ui-design-system` (tokens, components, handoff), `frontend-design` (after reload), Figma or Canva tools for mockups | none |
| **UI check before done** | `design-qa` | `cs-design-qa` |
| **Frontend code** (`web/`, `app/`) | `senior-frontend`, `senior-fullstack`, `superpowers:test-driven-development` | `cavecrew-builder` |
| **Backend and Functions** | `senior-backend`, `senior-fullstack`, then `/cloud-rules-auditor` | `cavecrew-investigator` |
| **Firmware and ESP32** | `embedded-iot-mentor` (second opinion), `superpowers:systematic-debugging`, then `/firmware-reviewer` | `cavecrew-investigator` |
| **Tests** | `tdd-guide`, `senior-qa`, `/pw:generate`, `/pw:coverage`, `/pw:fix`, `/pw:review`, `/pw:report` | `test-architect`, `test-debugger` |
| **Bug proof** | `red-green-proof` (failing test, fix, pass, revert, fails again) | none |
| **Code review** | `code-reviewer`, `/code-review:code-review <PR#>`, `/caveman:caveman-review` | `cavecrew-reviewer` |
| **Security and cycle-data privacy** | `senior-secops`, `senior-security`, `ciso-advisor`, `security-review`, `/cloud-rules-auditor` | none |
| **Pen test or incident** | `security-pen-testing`, `cloud-security`, `incident-response`, `incident-commander` | none |
| **CI/CD and hosting** | `senior-devops`, `gcp-cloud-architect` (fits Firebase), `cicd-setup` | none |
| **Analytics and experiments** | `product-analytics`, `experiment-designer` | none |
| **Competitor check** | `competitive-teardown`, `competitive-analysis` | none |
| **Release notes** | `roadmap-communicator`, `/release-firmware <version>` | none |
| **Memory and lessons** | `/si:remember`, `/si:memory-review`, `/si:promote` | `memory-analyst` |
| **Make a new skill** | `/si:extract`, `skill-creator` | `skill-extractor` |

Not relevant here: `android-skills` (we use Flutter), `senior-data-*`, `ms365-tenant-manager`,
`cs-arquiteto`, `migration-planner`, most `c-level-skills` (CFO, CMO, CRO, CHRO).

### Example: planning a feature, start to end

1. "Use brainstorming: how should partner heart-send work in the app?"
2. "Use prd-writing for the design we agreed."
3. "Use mvp-scoping: what is the smallest first version?"
4. "Use the Plan agent to find the 3 biggest holes in this plan."
5. `/new-adr <title>` if it is an architectural choice.
6. "Use writing-plans", then "Use executing-plans". Update `docs/handoff.md`.

### Example: building and checking a screen

1. "Use artifact-design to propose the layout for the pairing screen."
2. Build it with TDD (`superpowers:test-driven-development`).
3. "Use run to launch the dashboard."
4. "Use playwright-cli to open the page and check: no dead buttons, no placeholder text,
   loading, empty and error states exist, text contrast is readable, tap targets are at
   least 44 px."
5. Fix what it finds, then `/code-review:code-review`.

### Keep it automatic

Claude picks these skills on its own when your request matches. To make the routing
stick for every session, `CLAUDE.md` points here. If a role keeps missing (for example
you want a real product-manager or UI/UX skill), install the plugin that has it, then
add a row above.

---

## 1. Project skills (heartsync only)

These live in `.claude/skills/`. They know our rules.

| Skill | When | Type this | What you get |
|---|---|---|---|
| `firmware-reviewer` | After any change in `firmware/` | `/firmware-reviewer` | Report on IDisplay-only drawing, pins only in `config.h`, memory use, OTA signing. Report only, no edits |
| `cloud-rules-auditor` | After any change in `cloud/` | `/cloud-rules-auditor` | Checks Firestore and Storage rules and Functions against `docs/protocol.md`, including cycle-data privacy |
| `hardware-safety-reviewer` | After changing `docs/hardware/`, `cad/`, `firmware/src/power/` | `/hardware-safety-reviewer` | Checks battery and safety rules (25 percent brightness cap, no LiPo before Phase 8) |
| `bringup-check` | Wiring or testing a new part | `/bringup-check OLED` | Walks the checklist for that one part, step by step |
| `new-adr` | Any architecture choice | `/new-adr Use NimBLE for BLE` | Makes the next numbered ADR in `docs/adr/` from the template |
| `release-firmware` | Shipping firmware. Manual only | `/release-firmware 0.3.0` | Builds, signs, records, and bumps the version |

Order for a normal firmware change: edit, `pio test -e native`, `/firmware-reviewer`,
commit.

---

## 2. Agents (helpers in another room)

| Agent | Use it when | Type this | Notes |
|---|---|---|---|
| `caveman:cavecrew-investigator` | You need to find code | "Use the cavecrew-investigator agent to find every caller of `WifiStore::save`" | Read-only. Returns a short file:line list. Cheapest way to search |
| `caveman:cavecrew-builder` | Tiny edit in 1-2 files | "Use the cavecrew-builder agent to rename `ssid_` to `ssidStr_` in `WifiStore.cpp` and `WifiStore.h`" | Refuses 3+ files or new features |
| `caveman:cavecrew-reviewer` | Review a diff before commit | "Use the cavecrew-reviewer agent on my uncommitted changes in `firmware/src/net/`" | One line per finding, with severity |
| `Explore` | Wide search over many files | "Use the Explore agent, very thorough: where do we handle Wi-Fi credentials?" | Says "medium" or "very thorough" for depth. Finds, does not review |
| `Plan` | Design before building | "Use the Plan agent to plan the Phase 3 BLE Wi-Fi setup slice" | Gives steps, critical files, trade-offs. Does not edit. **Do not build Phase 3 until you say "go"** |
| `general-purpose` | Research or multi-step job nothing else fits | "Use a general-purpose agent to compare ESP32 NVS vs Preferences for storing Wi-Fi keys" | Can use all tools |
| `claude` | Default catch-all | "Use the claude agent to ..." | Same idea as general-purpose |
| `claude-code-guide` | Questions about Claude Code itself | "Ask the claude-code-guide agent how to add a hook that runs `pio test` after edits" | Covers CLI, hooks, MCP, SDK, API |
| `statusline-setup` | Change the status line | "Use the statusline-setup agent to show the model and git branch" | One-off |
| `web-fetch` | Read a public web page | "Use the web-fetch agent to read <url> and tell me the NimBLE pairing flags" | Fails on private pages |

Agents only report. Ask Claude afterwards to apply the changes.

---

## 3. Process skills (`superpowers`): how Claude works

Use these by saying them. Claude often loads them on its own.

| Skill | When | Type this | What it does |
|---|---|---|---|
| `superpowers:brainstorming` | Before any new feature or design | "Use brainstorming: how should Phase 3 BLE setup work?" | Asks questions, compares options, settles a design before code |
| `superpowers:writing-plans` | You have a spec, need steps | "Use writing-plans for the BLE Wi-Fi setup spec in `docs/handoff.md`" | Writes a step-by-step plan |
| `superpowers:executing-plans` | Plan is approved | "Use executing-plans on the plan we wrote" | Runs the plan in this chat |
| `superpowers:subagent-driven-development` | Plan with independent tasks | "Use subagent-driven-development for the plan" | One helper per task, reviewed between tasks |
| `superpowers:dispatching-parallel-agents` | 2+ unrelated jobs | "Use dispatching-parallel-agents: fix the web typecheck and the cloud test failure" | Runs them side by side |
| `superpowers:test-driven-development` | Any feature or bugfix | "Use TDD to add RSSI sorting to the Wi-Fi scan list" | Failing test first, then code |
| `superpowers:systematic-debugging` | Any bug or failing test | "Use systematic-debugging: `pio test -e native` fails in `test_setup`" | Finds root cause before fixing |
| `superpowers:verification-before-completion` | About to say "done" | "Use verification-before-completion before I commit" | Runs the commands and shows real output |
| `superpowers:requesting-code-review` | Finished a task | "Use requesting-code-review on the WifiStore work" | Reviews against requirements |
| `superpowers:receiving-code-review` | Got review feedback | "Use receiving-code-review on these comments: ..." | Checks feedback is correct before applying |
| `superpowers:using-git-worktrees` | Isolated branch work | "Use a git worktree for the BLE branch" | Separate working folder |
| `superpowers:finishing-a-development-branch` | Work done, tests pass | "Use finishing-a-development-branch" | Offers merge, PR, or cleanup |
| `superpowers:writing-skills` | Make or edit a skill | "Use writing-skills to improve `bringup-check`" | Tests the skill before you rely on it |
| `superpowers:diagnosing-superpowers` | A session went wrong | "Use diagnosing-superpowers: why did that take so long?" | Explains what happened |

---

## 4. Code and engineering skills

| Skill | When | Type this |
|---|---|---|
| `/code-review:code-review` | Review a GitHub PR | `/code-review:code-review 12` |
| `code-review` (skill) | Review code or a diff | "Use code-review on `firmware/src/ble/`" |
| `security-review` | Threat model, auth, secrets, cycle-data privacy | "Use security-review on the BLE pairing flow" |
| `architecture-design` | Services, data model, API shape | "Use architecture-design for device-scoped tokens" |
| `tech-stack-eval` | X vs Y choices | "Use tech-stack-eval: NimBLE vs Bluedroid for ESP32" |
| `cicd-setup` | CI pipelines | "Use cicd-setup to add GitHub Actions running `pio test -e native` and `npm test`" |
| `mvp-scoping` | Decide what to cut | "Use mvp-scoping for the first app release" |
| `prd-writing` | Write a feature spec | "Use prd-writing for the partner heart-send feature" |
| `roadmap-planning` | Order the work | "Use roadmap-planning for phases 3 to 8" |
| `/simplify` | Clean up changed code | `/simplify` |
| `ponytail` | Smallest-change mode | "Use ponytail: fix this with the least change" |
| `playwright-cli` | Test or drive a web page (`web/`) | "Use playwright-cli to open localhost:3000 and check the devices page" |
| `claude-in-chrome` | Drive your real Chrome | "Use claude-in-chrome to open the dashboard and screenshot the editor" |
| `run` | Start the app and see a change work | "Use run to launch the web dashboard" |
| `claude-api` | Anthropic SDK questions | "Use claude-api: how do I set prompt caching?" |
| `init` | Make a CLAUDE.md | `/init` |
| `claude-code-setup:claude-automation-recommender` | Suggest hooks, agents, skills for the repo | "Recommend Claude Code automations for this repo" |

---

## 5. Caveman skills (short replies, cheap tokens)

| Skill | Type this | Effect |
|---|---|---|
| `caveman:caveman` | `/caveman lite`, `/caveman full`, `/caveman ultra` | Sets how terse replies are. Say "stop caveman" to turn off |
| `caveman:caveman-commit` | `/caveman:caveman-commit` | Short commit message |
| `caveman:caveman-review` | `/caveman:caveman-review` | One-line review comments |
| `caveman:caveman-compress` | `/caveman:caveman-compress D:\SyncD\CLAUDE.md` | Shrinks a memory file. Saves a `.original.md` backup |
| `caveman:caveman-stats` | `/caveman:caveman-stats` | Token use and savings |
| `caveman:caveman-help` | `/caveman:caveman-help` | Command card |
| `caveman:caveman-init` | `/caveman:caveman-init` | Adds the always-on rule to this repo |
| `caveman:cavecrew` | "Use cavecrew to decide which helper to send" | Picks the right cavecrew agent |

---

## 6. Design, docs, and files (`anthropic-skills`, artifact skills)

| Skill | When | Type this |
|---|---|---|
| `artifact-design`, `artifact-capabilities`, `artifact-diagramming` | Publishing a web page or diagram | "Make an artifact page showing the Phase 3 BLE flow" |
| `dataviz` | Any chart | "Use dataviz to chart battery drain from `bench.csv`" |
| `docs`, `doc-coauthoring` | Write a doc together | "Use doc-coauthoring for the hardware overview" |
| `docx`, `pdf`, `pptx`, `xlsx` | Make or read those files | "Use pdf to extract the SSD1306 datasheet pages 10-15" |
| `web-artifacts-builder` | Bigger web artifacts | "Use web-artifacts-builder for a pairing demo" |
| `canvas-design`, `theme-factory`, `brand-guidelines`, `algorithmic-art` | Visual design | "Use canvas-design for the heart pixel logo" |
| `slack-gif-creator` | Animated GIF | "Use slack-gif-creator for a beating-heart GIF" |
| `mcp-builder` | Build an MCP server | "Use mcp-builder for a Firestore reader" |
| `skill-creator` | Make a skill | "Use skill-creator for a `/phase-tick` skill" |
| `deep-research` | Long research | "Use deep-research on BLE LE Secure Connections on ESP32" |
| `built-in-browser`, `chrome-browser`, `computer-use` | Drive a browser or desktop | "Use chrome-browser to open the Firebase console" |
| `google-workspace` | Docs, Sheets, Drive | "Use google-workspace to list my Drive files about heartsync" |
| `import-memory`, `morning`, `internal-comms` | Memory import, daily brief, updates | "Use morning" |

---

## 7. AWS skills (`aws-core:*`)

We use Firebase, not AWS. Only use these if you add AWS.

| Skill | Type this |
|---|---|
| `aws-serverless`, `aws-database`, `aws-storage`, `aws-iam`, `aws-security` | "Use aws-iam to design a least-privilege role" |
| `aws-cdk`, `aws-cloudformation`, `aws-deployment` | "Use aws-cdk to deploy a Lambda" |
| `aws-compute`, `aws-containers`, `aws-networking` | "Use aws-networking for a VPC" |
| `aws-observability`, `aws-billing-and-cost-management` | "Use aws-billing-and-cost-management to find what costs money" |
| `amazon-bedrock`, `aws-ai-ml` | "Use amazon-bedrock to call a model" |
| `aws-auth` | "Use aws-auth to add Cognito login" |
| `aws-messaging-and-streaming`, `aws-secrets-manager` | "Use aws-secrets-manager to store a key" |
| `aws-sdk-js-v3-usage`, `aws-sdk-python-usage`, `aws-sdk-swift-usage` | "Use aws-sdk-python-usage to list S3 buckets" |
| `aws-well-architected-review`, `aws-blocks`, `launch-with-aws`, `signing-in-to-aws` | "Use aws-well-architected-review on my setup" |

---

## 8. Business and startup skills

Not needed for building the devices. Use them only if heartsync becomes a product.
Prompt shape is always: "Use `<skill>` to `<job>`".

| Group | Skills |
|---|---|
| Fundraising | `pitch-deck`, `investor-research`, `fundraising-email`, `data-room`, `board-update`, `accelerator-application` |
| Marketing and content | `landing-page`, `email-marketing`, `content-strategy`, `social-content`, `founder-thought-leadership`, `seo-technical`, `launch-strategy`, `community-discovery`, `event-hosting`, `earned-media-outreach` |
| Sales and partners | `cold-outreach`, `sales-script`, `lead-scoring`, `partnership-outreach`, `proposal-generation` |
| Research | `market-research`, `competitive-analysis`, `competitor-monitoring`, `review-mining`, `sentiment-monitoring`, `user-research-synthesis`, `feedback-synthesis`, `churn-analysis`, `daily-product-digest` |
| Legal and compliance | `privacy-policy`, `terms-of-service`, `contract-review`, `soc2-prep` |
| Team | `job-description`, `interview-kit`, `employer-brand`, `sourcing-outreach` |
| Other | `onboarding-flow`, `support-docs`, `process-docs`, `startup-context`, `pinokio`, `career-ops` |

Example: "Use privacy-policy to draft a policy for an app that stores cycle data."
Check it against `docs/protocol.md` before using it.

---

## 9. Claude Code setup skills

| Skill | Type this |
|---|---|
| `update-config` | "Allow `pio` commands without asking" |
| `fewer-permission-prompts` | `/fewer-permission-prompts` |
| `keybindings-help` | "Rebind ctrl+s to submit" |
| `loop` | `/loop 5m check the emulator tests` |
| `schedule` | "Schedule a daily run of `npm test` in `cloud/`" |
| `plugin-authoring` | "Make a status line mod" |
| `workflow-authoring` | Only when you ask for a multi-agent workflow |
| `cowork-plugin-management:create-cowork-plugin` | "Create a plugin for heartsync tools" |
| `google-multi-account:setup`, `add-account`, `reauth` | `/google-multi-account:setup` (the server failed to connect this session) |

---

## 10. Ready-made flows for heartsync

| Situation | Type these, in order |
|---|---|
| Changed firmware | `pio test -e native`, then `/firmware-reviewer` |
| Changed rules or functions | `npm test` in `cloud/`, then `/cloud-rules-auditor` |
| Touched battery, CAD, power | `/hardware-safety-reviewer` |
| Bug found | "Use systematic-debugging on `<error>`", then TDD to fix, then verification-before-completion |
| New feature | "Use brainstorming for `<idea>`", then writing-plans, then executing-plans |
| Before merging | `/caveman:caveman-review` or the cavecrew-reviewer agent, then `/code-review:code-review <PR#>` |
| Design choice | `/new-adr <title>` |
| New board part | `/bringup-check <part>` |
| Ship firmware | `/release-firmware <version>` |
| Where is X used? | "Use the cavecrew-investigator agent to find `<X>`" |
| Check the dashboard in a browser | "Use playwright-cli to open localhost:3000" |
| Privacy check on cycle data | "Use security-review on `<change>`", then `/cloud-rules-auditor` |

**Rules that always apply** (from `CLAUDE.md`): draw only through `IDisplay`, pins only
in `config.h`, no secrets in git, never log cycle data, brightness capped at 25
percent, no unsigned firmware update path, and no Phase 3 build until you say "go".
