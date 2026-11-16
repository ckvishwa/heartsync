# heartsync

## Project

Two matching pixel-art devices for a couple, paired through Firebase and controlled
by a Flutter app and a small Next.js dashboard. **Current phase: 1 (Display) and
2 (Cloud sync)**: pixel art on the small LEDs, and a heart sent from one board
appears on the other. Do not build beyond these phases.

## Repo map

- `firmware/`: ESP32 firmware (PlatformIO, Arduino, C++17).
- `cloud/`: Firebase rules, Cloud Functions (TypeScript), emulator seed and tests.
- `app/`: Flutter app (iOS and Android), Riverpod.
- `web/`: Next.js dashboard (devices, pixel editor, OTA releases).
- `cad/`: enclosure parameters, Fusion 360 scripts, print profiles.
- `tools/`: repo-wide scripts (`pixel2header.py`, `seed_couple.py`).
- `docs/`: PRD, architecture, phases, protocol, ADRs, hardware docs.

Each package has its own `CLAUDE.md`. Read it before working there.

## Commands

PlatformIO is installed in the repo-local `.venv` (activate it, or call `.venv/Scripts/pio`).

| Package  | Build / run                              | Test                         |
|----------|------------------------------------------|------------------------------|
| firmware | `pio run` (in `firmware/`)               | `pio test -e native`         |
| cloud    | `firebase emulators:start` (`npm run emulators` in `cloud/`) | `npm test` (in `cloud/`) |
| app      | `flutter run` (in `app/`)                | `flutter test`               |
| web      | `npm run dev` (in `web/`)                | `npm test` (typecheck)       |

## Rules

- Draw only through `IDisplay`. No LED library calls outside `firmware/src/display/`.
- No secrets in git. `secrets.h`, `.env*`, and service-account files are git-ignored;
  only `*.example` files are committed.
- Pins live only in `firmware/include/config.h` (mirrored in `docs/hardware/pinout.md`).
- Every architectural choice gets an ADR in `docs/adr/` (use `/new-adr`).
- Keep PRs small and scoped to one package.
- Tick the item in `docs/phases.md` when a phase item is done.
- Write a native test for any pure logic (no hardware needed to run it).
- Brightness stays capped (25 percent) until Phase 8. No LiPo wiring before Phase 8.
- Never add an unsigned firmware update path.

## Privacy

Cycle data (`users/{uid}/private/cycle`) is health data. Any change touching it must
be reviewed against the rules in `docs/protocol.md` (owner-only write, partner read
only while `sharingEnabled` is true). Never log it, on any platform.

## Definition of done

Builds, tests pass, docs updated, no new secrets.
