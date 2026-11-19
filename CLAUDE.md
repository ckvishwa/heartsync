# heartsync

## Start here

**Read `docs/handoff.md` first.** It holds the current state, the open decisions,
and the next step. Update it at the end of every session that changes the plan.

## Project

Two matching pixel-art devices for a couple, paired through Firebase and controlled
by a Flutter app and a small Next.js dashboard. **Phase 2 (cloud sync) is done on
the emulator. The Phase 3 BLE Wi-Fi setup slice is built (ADR 0009) and waits for
its hardware test with the user** (steps in `docs/handoff.md`). The bench display
is an SSD1306 OLED (ADR 0007). Do not start new slices beyond that without the
user's go.

## Repo map

- `firmware/`: ESP32 firmware (PlatformIO, Arduino, C++17).
- `cloud/`: Firebase rules, Cloud Functions (TypeScript), emulator seed and tests.
- `app/`: Flutter app (iOS and Android), Riverpod.
- `web/`: Next.js dashboard (devices, pixel editor, OTA releases).
- `cad/`: enclosure parameters, Fusion 360 scripts, print profiles.
- `tools/`: repo-wide scripts (`pixel2header.py`, `seed_couple.py`).
- `docs/`: PRD, architecture, phases, protocol, ADRs, hardware docs.
- `Hardware/heartsync_kicad/`: carrier PCB (KiCad 10, SKiDL netlist, placement scripts).

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

## Picking skills and agents

Match the kind of work to the right skill or agent using the table in
`docs/how-to-use.md` section 0 (planning, UI design, frontend, backend, firmware,
review, shipping). Run the matching reviewer skill after changes in its area.

## Definition of done

Builds, tests pass, docs updated, no new secrets.
