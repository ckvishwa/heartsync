# Skills: what exists and how to use them

A skill is a packaged set of instructions. Claude loads one automatically when your
request matches its description, or you can call it yourself:

- `/<name>` for project skills, for example `/new-adr My title`
- `/<plugin>:<name>` for plugin skills, for example `/engineering-skills:code-reviewer`
- or just say it: "use the red-green-proof skill on this bug"

`/reload-skills` re-reads them after you add or edit one.

Where `CLAUDE.md` and a plugin skill disagree, `CLAUDE.md` wins.

> **Out of date (2026-11-16):** sections 2, 2b, 2c and 3 below describe the
> `engineering-skills`, `product-skills`, `c-level-skills` and `android-skills`
> plugins, which are not loaded now. For what is loaded, with prompts to type, see
> `docs/how-to-use.md`.

## 1. Project skills (`.claude/skills/`)

| Skill | What it does | Call |
|---|---|---|
| `firmware-reviewer` | Reviews `firmware/` changes: IDisplay only, no hardcoded pins, memory, OTA signing. Report only. | `/firmware-reviewer` |
| `cloud-rules-auditor` | Audits Firestore and Storage rules and Cloud Functions against `docs/protocol.md`. Report only. | `/cloud-rules-auditor` |
| `hardware-safety-reviewer` | Checks hardware docs, CAD and power code against `docs/hardware/safety.md`. Report only. | `/hardware-safety-reviewer` |
| `bringup-check` | Walks the hardware bring-up checklist one part at a time. | `/bringup-check [part]` |
| `new-adr` | Creates the next numbered ADR from the template. | `/new-adr <title>` |
| `release-firmware` | Builds, signs, records and version-bumps a firmware release. Manual only. | `/release-firmware <version>` |

## 2. `engineering-skills` plugin

Most relevant to heartsync first.

| Skill | Use it for |
|---|---|
| `code-reviewer` | Review a diff or PR (Dart, TypeScript, C++ and more); gives a merge verdict |
| `adversarial-reviewer` | Harsh second-opinion review before merge |
| `named-persona-adversarial-review` | Review through named engineers' documented views |
| `red-green-proof` | Prove a bug: failing test, fix, pass, then revert the fix and confirm it fails again |
| `tdd-guide` | Test-first development, fixtures, coverage gaps |
| `senior-secops`, `senior-security` | Threat model, secrets scan, hardening (useful for cycle-data privacy) |
| `senior-frontend`, `senior-fullstack`, `senior-backend` | Next.js dashboard and Cloud Functions work |
| `senior-qa` | Jest, React Testing Library, Playwright for `web/` |
| `senior-architect`, `tech-stack-evaluator` | Architecture decisions and ADR drafts, X-vs-Y comparisons |
| `embedded-iot-mentor` | ESP32 planning; treat as a second opinion next to our ADRs |
| `incident-commander`, `incident-response` | Outage handling; suspected breach or leaked key |
| `security-pen-testing`, `ai-security`, `cloud-security`, `red-team`, `threat-detection` | Authorized security testing and posture checks |
| `senior-devops`, `gcp-cloud-architect`, `aws-solution-architect`, `azure-cloud-architect` | CI/CD and cloud design (GCP fits Firebase) |
| `email-template-builder`, `stripe-integration-expert`, `epic-design` | Email, billing, cinematic landing pages |
| `senior-data-engineer`, `senior-data-scientist`, `senior-ml-engineer`, `senior-computer-vision`, `senior-prompt-engineer` | Data and ML work (not used here) |
| `ms365-tenant-manager` | Microsoft 365 admin (not used here) |
| `engineering-skills` | Index: tells you which skill fits a task |

### Playwright sub-skills (`/pw:*`)

`/pw:init` set up Playwright, `/pw:generate` write tests, `/pw:fix` debug a failing
test, `/pw:coverage` find untested flows, `/pw:review` audit tests,
`/pw:report` summarize results, `/pw:migrate` move from Cypress or Selenium.
Only relevant to `web/`.

### Self-improving sub-skills (`/si:*`)

`/si:remember` save a lesson, `/si:memory-status` memory health,
`/si:memory-review` what to promote or prune, `/si:promote` move a lesson into
`CLAUDE.md`, `/si:extract` turn a pattern into a skill.

### Hook

The plugin adds a `UserPromptSubmit` hook (`skill_router.py`). It adds one line
naming a fitting skill when your prompt matches a pattern. It never blocks. Turn it
off with the environment variable `SKILL_ROUTER=0`.

## 2b. `product-skills` plugin

Design, UX and product. Most useful for the Flutter app and the `web/` dashboard.

| Skill | Use it for |
|---|---|
| `design-qa` | Gate a finished screen: dead controls, placeholder text, contrast, tap size, missing loading/empty/error states |
| `ui-design-system` | Design tokens (colors, spacing, type), component docs, developer handoff |
| `ux-researcher-designer` | Personas, journey maps, usability test plans |
| `product-discovery`, `product-manager-toolkit`, `product-strategist` | Is it worth building, rank features, PRDs, OKRs, roadmap |
| `roadmap-communicator` | Release notes and plans written for others |
| `experiment-designer`, `product-analytics` | A/B tests, retention and KPI reading |
| `competitive-teardown` | Compare against a rival product |
| `landing-page-generator`, `saas-scaffolder`, `spec-to-repo` | Scaffolding (use only when asked) |
| `product-skills` | Router across all of the above |

## 2c. `c-level-skills` plugin

Executive advisors written for company founders. **`cto-advisor` and `vpe-advisor`
are the closest fits** (rewrite or not, tech bets, team growth). `ciso-advisor` fits
the cycle-data privacy rules. The rest (CFO, CMO, CRO, CHRO, M&A, board decks and
similar) are company-level and rarely relevant to a two-person device project.
`cs-onboard` writes `~/.claude/company-context.md` on first use.

## 3. `android-skills` plugin (21 skills)

Native Android and Kotlin Multiplatform. **heartsync's app is Flutter, so these rarely
apply.** They are useful only for native Android work, for example inside
`app/android/`.

`android-dev` (baseline, routes to the rest), `compose`, `android-ux`, `coil-compose`,
`kotlin-coroutines`, `kotlin-flows`, `android-data-layer`, `datastore`, `paging`,
`android-retrofit`, `kmp-ktor`, `koin`, `kmp-boundaries`, `modularization`,
`android-gradle-logic`, `gradle-build-performance`, `android-testing`,
`android-debugging`, `android-source-search`, `pdf-annotations`, `rxjava-migration`
(only when you ask for the migration).

## Typical heartsync flows

| Situation | Do this |
|---|---|
| Changed firmware | `/firmware-reviewer` |
| Changed rules or functions | `/cloud-rules-auditor` |
| Touched battery, CAD or power code | `/hardware-safety-reviewer` |
| Fixing a bug | `red-green-proof`, then `/firmware-reviewer` or the matching reviewer |
| Before merging a PR | `code-reviewer`, then `adversarial-reviewer` |
| New design choice | `/new-adr <title>` |
| Wiring a new board part | `/bringup-check <part>` |
| Shipping firmware | `/release-firmware <version>` |
