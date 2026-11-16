# Agent guide: heartsync

Tool-neutral instructions for any coding agent. Same facts as `CLAUDE.md`.

## Project

Two matching pixel-art devices for a couple, paired through Firebase and controlled
by a Flutter app and a small Next.js dashboard. **Current phase: 1 (Display) and
2 (Cloud sync).** Do not build beyond these phases.

## How to work here

1. Read `docs/prd.md` and `docs/phases.md` first.
2. Work in one package at a time, and read that package's `CLAUDE.md`.
3. Run that package's tests before finishing.
4. Never edit generated files (`app/ios/`, `app/android/` build output, `cloud/functions/lib/`,
   `web/.next/`, `cad/exports/`, lock files by hand).

## Repo map

- `firmware/`: ESP32 firmware (PlatformIO, Arduino, C++17).
- `cloud/`: Firebase rules, Cloud Functions (TypeScript), emulator seed and tests.
- `app/`: Flutter app (iOS and Android), Riverpod.
- `web/`: Next.js dashboard.
- `cad/`: enclosure parameters, Fusion 360 scripts, print profiles.
- `tools/`: repo-wide scripts.
- `docs/`: PRD, architecture, phases, protocol, ADRs, hardware docs.

## Commands

| Package  | Build / run                                  | Test                 |
|----------|----------------------------------------------|----------------------|
| firmware | `pio run` (in `firmware/`)                   | `pio test -e native` |
| cloud    | `firebase emulators:start` (in `cloud/`)     | `npm test`           |
| app      | `flutter run` (in `app/`)                    | `flutter test`       |
| web      | `npm run dev` (in `web/`)                    | `npm test`           |

PlatformIO is installed in the repo-local `.venv`.

## Rules

- Draw only through the `IDisplay` interface.
- No secrets in git: `secrets.h`, `.env*`, service accounts are ignored; `*.example` files are committed.
- Pins only in `firmware/include/config.h`.
- Every architectural choice gets an ADR in `docs/adr/`.
- Small, per-package changes.
- Update `docs/phases.md` when a phase item is done.
- Native test for any pure logic.
- Brightness capped at 25 percent until Phase 8; no LiPo wiring before Phase 8.
- Never add an unsigned firmware update path.

## Privacy

Cycle data is health data. Review any change against `docs/protocol.md`. Never log it.

## Definition of done

Builds, tests pass, docs updated, no new secrets.
