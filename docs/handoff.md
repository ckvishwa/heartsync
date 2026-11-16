# Handoff: where we are and what to do next

Last updated: 2026-11-16 (Phase 3 BLE slice built). Read this first in a new session, then `CLAUDE.md`,
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
  - Firmware:
    - Setup mode with a NimBLE GATT service. Passkey on the OLED, LE SC only,
      lockout after 3 tries, 60 s pairing deadline, 15 min window.
    - Wi-Fi is tested before it is saved. The token is held in RAM and used once.
    - `CloudClient` reads couple and owner from claims (no `users/` reads).
    - BOOT tap sends a heart; a 5 s hold wipes and re-enters setup.
    - 47 native tests pass. Reviewed by `firmware-reviewer`; fixes applied.
    - esp32dev at 62.7% flash, 18.4% static RAM.
  - App:
    - "Set up a board" screen (flutter_blue_plus): scan, pair, Wi-Fi list or
      manual entry, register, send key, wait for `signed_in`.
    - Android BLE permissions, iOS usage string. 31 tests pass, analyze clean.
- **App:** connection check panel on the home screen; Firebase options come from
  `--dart-define-from-file=config/emulator.json` (git-ignored; copy the example).
- Repo: private github.com/ckvishwa/heartsync (`main`). CI runs on push; the cloud
  deploy job stays off until a `FIREBASE_PROJECT_ID` repo variable exists.

## Next: hardware test of BLE setup (needs the user)

Nothing is flashed yet. The boards still run the Phase 2 firmware with plain owner
tokens. The new firmware refuses those tokens and shows `SETUP NEEDED`.

1. The user starts the emulators (`cd cloud && npm run emulators`, then `npm run seed`)
   and confirms `HS_FIREBASE_EMULATOR_HOST` in `secrets.h` is the PC's current IP.
2. Flash board-B over USB (`pio run -e esp32dev -t upload --upload-port COMx`). Check
   the MAC with esptool first.
3. On the phone: install the app (`flutter run ... --dart-define=EMULATOR_HOST=<PC IP>`),
   sign in as Bob, and choose **Set up a board**.
4. On board-B: hold BOOT 5 s. It shows SET UP. Pair: PIN on the OLED, typed on the
   phone. Then Wi-Fi (the hotspot SSID with a trailing space), registration, and
   `signed_in`. The board restarts.
5. Check the serial log: uid `dev_hs-20500dcd63f4`, couple `demo-couple`, owner
   `bob`, and no secrets anywhere. Run `status`, which prints free and minimum heap.
6. Run the tests:
   - wrong PIN 3 times gives LOCKED, and a BOOT hold clears it
   - a wrong Wi-Fi password shows "Wrong Wi-Fi password." on the phone
   - change networks: hold, then set up again
   - hearts both ways (app to board, BOOT tap)
7. Repeat for board-A as Alice. Record results in `docs/hardware/bringup-log.md` and
   tick the Phase 3 hardware item.
8. If pairing misbehaves on Android, check first: the `removeBond`/`createBond` flow
   in `board_setup_repository.dart`, and NimBLE `onAuthenticationComplete`.

### Open decisions and known risks (ADR 0009)

- Board-id squatting: needs proof of possession plus an unregister path (open).
- Re-pairing an owner to a new couple cannot re-register their board yet.
- flutter_blue_plus uses `License.nonprofit`. Commercial use needs a paid license.
- Revocation stops refreshes only; an ID token already issued lives up to 1 h.
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
- BOOT: tap sends a heart; hold 5 s while running wipes Wi-Fi and tokens and enters
  BLE setup. Never hold it at power-up (that is ROM download mode).

## Known gaps (not blocking Phase 3 work on the emulator)

1. Partner invite callables are still stubs (seed scripts until then).
2. No real Firebase project: board talks plain HTTP to the emulator only; app needs
   real options; HTTPS and root CA on the board.
3. OTA download and signature verification (Phase 2b); device tokens currently have
   no Storage or `releases` access, so OTA needs an explicit, tested exception.
4. Push notifications, avatars, pixel editor, settings, mood/cycle screens: stubs.
5. HUB75, touch, IMU, power: later phases.
