# Handoff: where we are and what to do next

Last updated: 2026-11-16 (Phase 3 BLE slice built; setup protocol 2 committed, hardware test pending). Read this first in a new session, then `CLAUDE.md`,
`docs/phases.md`, and the package `CLAUDE.md` for the area you touch.

## State

- **Phase 1 (display):** bench display is a 0.96" 128x64 SSD1306 I2C OLED on each
  board (ADR 0007). Art draws on a 64x32 logical canvas, scaled 2x. Both boards pass
  the visual check. Open Phase 1 items: real avatars, animations, HUB75 (1b).
- **Phase 2 (cloud sync): done on the emulator.** Board sign-in, heartbeat, event
  polling (ADR 0008), app and BOOT-button hearts pass in both directions on real
  hardware. Results: `docs/hardware/bringup-log.md`. Carried over: real Firebase
  project, Phase 2b OTA download and verify.
- **Phase 3 slice, BLE Wi-Fi setup: BUILT, hardware test pending** (ADR 0009).
  - Cloud:
    - Boards have their own uid `dev_<deviceId>` with claims
      `{deviceId, coupleId, owner}`.
    - `registerDevice` callable, a server-only `deviceRegistry`, board-aware
      `sendHeart`.
    - Rules use `token.owner` in board mode. People cannot create device records.
    - 68 cloud tests pass. Audited by `cloud-rules-auditor`; fixes applied.
  - **Setup protocol 2** (user feedback, 2026-11-16), firmware and app:
    - Numeric comparison: same code on the OLED (`TAP BOOT 123456`) and the phone;
      tap Pair on the phone, then BOOT on the board within 25 s. A tap counts only
      while a pairing waits and only if pressed after the code appeared.
    - Paged Wi-Fi list (up to 40, each page <= 512 bytes); the notify is a 1-byte
      "page ready" signal and the app reads each page.
    - Token in numbered 180-byte chunks plus a length/CRC32 end frame (a real
      custom token is ~1 KB; emulator tokens are short and hid this).
    - Proto mismatch: the app says "Update the board firmware" / "Update the app".
    - The installed phone app and board-B are still proto 1: rebuild both.
  - Firmware:
    - Setup mode with a NimBLE GATT service. Numeric comparison + BOOT confirm,
      LE SC only, lockout after 3 tries, 60 s pairing deadline, 15 min window.
    - Wi-Fi is tested before it is saved. The token is held in RAM and used once.
    - `CloudClient` reads couple and owner from claims (no `users/` reads).
    - BOOT tap sends a heart; a 5 s hold wipes and re-enters setup.
    - 52 native tests pass. Reviewed by `firmware-reviewer` (proto 2 too); fixes applied.
    - esp32dev at 62.8% flash, 18.4% static RAM.
  - App:
    - "Set up a board" screen (flutter_blue_plus): scan, pair, Wi-Fi list or
      manual entry, register, send key, wait for `signed_in`.
    - Android BLE permissions, iOS usage string. 40 tests pass, analyze clean.
- **App:** connection check panel on the home screen; Firebase options come from
  `--dart-define-from-file=config/emulator.json` (git-ignored; copy the example).
- Repo: private github.com/ckvishwa/heartsync (`main`). CI runs on push; the cloud
  deploy job stays off until a `FIREBASE_PROJECT_ID` repo variable exists.

## Next: hardware test of BLE setup, proto 2 (needs the user's go)

Before starting: run `ipconfig` and confirm the PC IP (last `10.143.236.144`; it is
DHCP). The user sets `HS_FIREBASE_EMULATOR_HOST` in `secrets.h` to it (agents never
touch that file; last seen value was a stale `10.143.236.90`).

1. Emulators running and seeded (`cd cloud && npm run emulators`, `npm run seed`).
2. Check the MAC (`python ~/.platformio/packages/tool-esptoolpy/esptool.py --port COMx
   read_mac`), then `cd firmware && ../.venv/Scripts/pio run -e esp32dev -t upload
   --upload-port COMx` for board-B.
3. `cd app && flutter build apk --debug --dart-define-from-file=config/emulator.json
   --dart-define=EMULATOR_HOST=<PC IP>`, then `adb -s <device> install -r
   build/app/outputs/flutter-apk/app-debug.apk`.
4. Sign in as Bob. Hold BOOT 5 s while running; the board shows SET UP. App: Set up
   a board, heartsync-63f4, compare codes, Pair on the phone, tap BOOT, full Wi-Fi
   list, password, Connect board, done.
5. Serial at 115200 (reset via RTS only, GPIO 0 untouched): uid
   `dev_hs-20500dcd63f4`, couple `demo-couple`, owner `bob`. Grep serial and
   `adb logcat` for the password, token and code: none. `status` prints heap.
6. Tests: no BOOT tap (pairing times out, one try); a BOOT tap with nothing pending
   does nothing; 3 failures give LOCKED and a BOOT hold clears it; wrong Wi-Fi
   password; a proto 1 board is refused by the app with a clear message; change
   networks; hearts both ways in normal mode; all ~30 networks the board sees
   appear in the app.
7. Repeat on board-A as Alice. Record in `docs/hardware/bringup-log.md` (also the
   Wi-Fi scan and connect with a BLE link up on esp32dev), tick the Phase 3 hardware
   item, update this file.
8. If pairing misbehaves on Android: `removeBond`/`createBond` in
   `board_setup_repository.dart`, NimBLE `onConfirmPassKey` and
   `onAuthenticationComplete` in `BleSetup.cpp`.

### Open decisions and known risks (ADR 0009)

- Board-id squatting: needs proof of possession plus an unregister path (open).
- Re-pairing an owner to a new couple cannot re-register their board yet.
- flutter_blue_plus uses `License.nonprofit`. Commercial use needs a paid license.
- Revocation stops refreshes only; an ID token already issued lives up to 1 h
  (rules do not check revocation). Custom tokens are reusable for their 1 h.
- Someone nearby can burn the 3 pairing tries on purpose (lock-out nuisance; a
  BOOT hold clears it). Accepted.
- iOS build path (a Mac or cloud build, an Apple developer account). Pairing must
  be tested on an iPhone before Phase 3 counts as done.
- Mood and cycle data must never appear in event payloads (the board reads all
  couple events): confirm with a rules or function test.
- Wi-Fi scan and connect while BLE is up on esp32dev: no spike result is recorded
  in the bring-up log yet; record it in the hardware test, and test again on the S3.
- The Auth emulator does not enforce revocation on refresh (production does).

## Bench setup (to resume testing)

- Boards (both ESP32-D0WD-V3, env `esp32dev`, OLED SDA 21 / SCL 22):
  - board-A, Alice: MAC `20:50:0d:cd:fd:18`, `hs-20500dcdfd18`
  - board-B, Bob: MAC `20:50:0d:cd:63:f4`, `hs-20500dcd63f4`
  - COM ports move (last: A on COM6, B on COM3). **Check the MAC with esptool
    before every flash.**
- Network last used: open 2.4 GHz hotspot (its SSID has a trailing space), PC at
  `10.143.236.144`. The home network refused the boards at the auth step. The user
  owns `firmware/include/secrets.h`; agents never read or write it. If the PC IP
  changes, the user updates `HS_FIREBASE_EMULATOR_HOST` there and the app's
  `EMULATOR_HOST`.
- Emulators: `cd cloud && npm run emulators`, then `npm run seed`. Bound to
  `0.0.0.0`; Windows firewall rule "heartsync emulators (LAN)" allows 9099, 8080,
  5001 from the local subnet. Tests: `npm test` (separate ports, runs alongside).
- Bench serial fallback (esp32dev builds only, `HS_DEV_SERIAL_TOKEN`): `python tools/seed_couple.py --couple-id demo-couple
  --person alice@example.com:Alice:hs-20500dcdfd18 --person
  bob@example.com:Bob:hs-20500dcd63f4 --mint-tokens`, then
  `python tools/provision_device.py --port COMx --device-id hs-...` within 1 h.
  Emulator restarts wipe Auth, so re-mint and re-provision after one.
- App on the phone: `cd app && flutter run -d <device>
  --dart-define-from-file=config/emulator.json --dart-define=EMULATOR_HOST=<PC IP>`.
  Logins: `alice@example.com` / `bob@example.com`, password `heartsync`.
- Serial: 115200; commands `status`, `heart`, `token <jwt>` (bench builds), `forget`.
- BOOT: tap sends a heart (in setup mode it confirms the pairing code instead);
  hold 5 s while running wipes Wi-Fi and tokens and enters BLE setup. Never hold it
  at power-up (that is ROM download mode).

## Known gaps (not blocking Phase 3 work on the emulator)

1. Partner invite callables are still stubs (seed scripts until then).
2. No real Firebase project: board talks plain HTTP to the emulator only; app needs
   real options; HTTPS and root CA on the board.
3. OTA download and signature verification (Phase 2b); device tokens currently have
   no Storage or `releases` access, so OTA needs an explicit, tested exception.
4. Push notifications, avatars, pixel editor, settings, mood/cycle screens: stubs.
5. HUB75, touch, IMU, power: later phases.
