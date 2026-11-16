# Handoff: where we are and what to do next

Last updated: 2026-11-16. Read this first in a new session, then `CLAUDE.md`,
`docs/phases.md`, and the package `CLAUDE.md` for the area you touch.

## State

- **Phase 1 (display):** bench display is a 0.96" 128x64 SSD1306 I2C OLED on each
  board (ADR 0007). Art draws on a 64x32 logical canvas, scaled 2x. Both boards pass
  the visual check. Open Phase 1 items: real avatars, animations, HUB75 (1b).
- **Phase 2 (cloud sync): done on the emulator.** Board sign-in, heartbeat, event
  polling (ADR 0008), app and BOOT-button hearts pass in both directions on real
  hardware. Results: `docs/hardware/bringup-log.md`. Carried over: real Firebase
  project, Phase 2b OTA download and verify.
- **Board tokens hardened (before Phase 3):** Firestore and Storage rules scope any
  token with a `deviceId` claim to its couple's events and its own device record
  (`docs/protocol.md` "Device tokens"). 51 cloud tests pass. Reviewed by
  `cloud-rules-auditor`. Bench boards still hold plain owner tokens (no claims).
- **App:** connection check panel on the home screen; Firebase options come from
  `--dart-define-from-file=config/emulator.json` (git-ignored; copy the example).
- Everything is committed. Nothing is pushed.

## Phase 3 slice: BLE Wi-Fi setup from the app. PLANNED, NOT BUILT

**Do not start building until the user says "go" and answers decisions A, B, C.**

### User decisions already made

1. Passkey on the OLED: random per pairing session, LE Secure Connections only,
   every setup characteristic needs an encrypted, authenticated link, lock out
   after 3 wrong attempts.
2. The board scans Wi-Fi; the app shows the list (2.4 GHz only) plus manual entry
   for hidden networks.
3. Partner invites stay on the seed scripts for this slice.
4. `registerDevice` must not give the board the owner's own token: mint a
   short-lived custom token with a `deviceId` claim; the board exchanges it for a
   refresh token immediately.
5. Never log Wi-Fi credentials, tokens, or the passkey.

### Decisions still open (ask the user)

- **A. Board identity (auditor finding, HIGH).** A board signed in with the owner's
  uid can call Firebase Auth account APIs (set a password, delete the account) that
  rules never see. Recommended: each board gets its own uid `dev_<deviceId>` with an
  `owner` claim; rules switch to `token.owner` in board mode. Alternative: keep the
  owner uid and record the risk in ADR 0009.
- **B. Token lifetime.** Firebase custom tokens always live 1 h and cannot be
  shortened. Mitigation: app hands it over BLE within seconds; the board exchanges
  it at once and erases it. Acceptable?
- **C. Secrets at rest.** Wi-Fi password and refresh token sit unencrypted in NVS
  until flash encryption is enabled (one-way per chip; planned for the final build).
  Accept for the bench?

### Plan (order: cloud, firmware, app; one small commit per package)

**Cloud: `registerDevice` callable** (`cloud/functions/src/pairing.ts`)
- Caller must be a person (reject `deviceId` tokens). Validate `deviceId`
  (`hs-` + 12 hex). Couple from `users/{uid}.coupleId`, membership re-checked.
  Refuse a board already registered to another owner.
- Write `couples/{c}/devices/{deviceId}` (owner, firmwareVersion, online, lastSeen).
- Mint with `createCustomToken(uid, {deviceId, coupleId[, owner]})`. Never
  `setCustomUserClaims` (it would turn the owner's phone sessions into board tokens).
- `sendHeart`: for board callers, reject a `coupleId` claim that does not match the
  couple (auditor finding 2); post as `token.owner` if decision A is "own uid".
  Add the functions test with a mismatched claim.
- If A = own uid: rules use `token.owner` for `from`, `owner`, and membership in
  board mode; update tests.

**Firmware**
- Provisioning mode only when no Wi-Fi is stored, or BOOT held 5 s at power-up.
- NimBLE GATT service: `deviceId` (read), `wifiList` (read/notify, board's own
  scan), `wifiCreds` (write), `token` (long write, about 1 KB), `status`
  (read/notify). All encrypted plus authenticated; LE Secure Connections only;
  random passkey on the OLED; 3 wrong passkeys stop BLE until BOOT is held again.
- Store Wi-Fi and the refresh token in NVS; exchange and erase the custom token.
- `CloudClient`: board tokens can no longer read `users/` or the couple doc, so take
  `coupleId` and owner from the ID token claims and poll events newer than the
  cursor, skipping the owner's own.
- `secrets.h` Wi-Fi becomes a dev-only fallback.
- Native tests: characteristic decoding, provisioning state machine, lockout, claims.
- Size check done: NimBLE adds about 248 KB flash on esp32dev (47% to 61%) and
  187 KB on S3 (45% to 55%); static RAM +6 to +10 KB. Measure runtime heap on the
  board in the first firmware step.

**App:** "Set up a board" screen with `flutter_blue_plus` (Android 12+ BLE
permissions, iOS usage string): scan `heartsync-*`, pair (OS passkey prompt),
read `deviceId` and `wifiList` (or manual entry), call `registerDevice`, write
credentials and token, follow `status` to signed in. Repository plus fake, widget
tests, no secrets in logs.

**Docs:** ADR 0009 (BLE provisioning and board identity), `protocol.md`
"BLE provisioning", `phases.md`.

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
- Board tokens (until Phase 3): `python tools/seed_couple.py --couple-id demo-couple
  --person alice@example.com:Alice:hs-20500dcdfd18 --person
  bob@example.com:Bob:hs-20500dcd63f4 --mint-tokens`, then
  `python tools/provision_device.py --port COMx --device-id hs-...` within 1 h.
  Emulator restarts wipe Auth, so re-mint and re-provision after one.
- App on the phone: `cd app && flutter run -d <device>
  --dart-define-from-file=config/emulator.json --dart-define=EMULATOR_HOST=<PC IP>`.
  Logins: `alice@example.com` / `bob@example.com`, password `heartsync`.
- Serial: 115200; commands `status`, `heart`, `token <jwt>`, `forget`.

## Known gaps (not blocking Phase 3 work on the emulator)

1. Pairing callables are stubs (Phase 3; `registerDevice` is the first one).
2. No real Firebase project: board talks plain HTTP to the emulator only; app needs
   real options; HTTPS and root CA on the board.
3. OTA download and signature verification (Phase 2b); device tokens currently have
   no Storage or `releases` access, so OTA needs an explicit, tested exception.
4. Push notifications, avatars, pixel editor, settings, mood/cycle screens: stubs.
5. HUB75, touch, IMU, power: later phases.
