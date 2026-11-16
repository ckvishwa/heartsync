# heartsync

Two matching, cloud-synced pixel-art devices for a couple. A heart sent from one
lights up the other. Working name; rename freely.

**Status:** Phases 1 (Display) and 2 (Cloud sync) of 11. See [docs/phases.md](docs/phases.md).

## Layout

| Folder      | What                                                        |
|-------------|-------------------------------------------------------------|
| `firmware/` | ESP32 firmware (PlatformIO, Arduino, C++17)                 |
| `cloud/`    | Firebase: rules, Cloud Functions (TypeScript), emulator     |
| `app/`      | Flutter app (iOS and Android)                               |
| `web/`      | Next.js dashboard: devices, pixel editor, OTA releases      |
| `cad/`      | Enclosure parameters, Fusion 360 scripts, print profiles    |
| `tools/`    | Repo-wide scripts (PNG to bitmap, couple seeding)           |
| `docs/`     | PRD, architecture, phases, protocol, ADRs, hardware notes   |

## Quick start

```sh
# Firmware (PlatformIO lives in the repo-local .venv)
python -m venv .venv && .venv/Scripts/pip install platformio cryptography pillow
cp firmware/include/secrets.example.h firmware/include/secrets.h   # then edit Wi-Fi
cd firmware && pio run && pio test -e native

# Cloud (emulators, offline, project id demo-heartsync)
cd cloud && npm install && npm --prefix functions install
npm run emulators          # terminal 1
npm run seed               # terminal 2: demo users, couple, devices
npm test                   # rules + sendHeart tests

# App (with the emulators running)
cd app && flutter run

# Web (with the emulators running)
cd web && npm install && npm run dev
```

Demo logins after seeding: `alice@example.com` and `bob@example.com`, password `heartsync`.

Start with [docs/prd.md](docs/prd.md), then [docs/architecture.md](docs/architecture.md).
