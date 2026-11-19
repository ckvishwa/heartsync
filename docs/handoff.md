# Handoff: where we are and what to do next

Last updated: 2026-11-19 (real parts in the enclosure, fit check with real geometry, bare back with TPU ring; Phase 3 hardware test still pending). Read this first in a new session, then `CLAUDE.md`,
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

## Carrier board and enclosure (2026-11-19)

- **Carrier PCB** (`Hardware/heartsync_kicad/`, read its `CLAUDE.md`): placement done, not routed.
  - U1 is now the **ESP32-S3-WROOM-1U-N16R8** (ADR 0011, Proposed): U.FL socket, external 2.4 GHz
    flex antenna on the shell wall, no antenna keepout. Socket faces the top edge at (23.0, 2.96) mm.
  - J4 (left speaker) on the left edge, J5 (right) on the right edge.
  - DRC: 0 courtyard, keepout, hole and drill errors. 11 starved thermals wait for routing.
  - Antenna: **Ezurio FlexPIFA 001-0014** (ADR 0011), now on the front wall bottom-left, outside
    the phone footprint. Flex PIFA differs from the certified monopole: extra RF/EMC testing.
  - Next in order: route power, I2S, USB pair, rest; DRC clean; STEP fit check in Fusion.
- **Enclosure** (`cad/fusion/heartsync_assembly.py`, dimensions from `cad/params.csv`,
  positions in its POS block; real parts from `cad/models/`, read its README). One run (about
  5 min) builds everything, imports the carrier STEP and 23 real parts, checks, groups, names
  the sides and paints. Entry points: `fit_check`, `print_checks`, `export_all`, `make_net`,
  `make_renders`, `save_doc`, `sync_from_fusion`. The last build (2026-11-19) is the open,
  **unsaved** Fusion tab; "HeartSync v1" in the cloud is the older version. Fusion crashed once
  this session (four large STEP imports at once); unsaved older tabs were lost.
  - Use case: docked on the BOTTOM edge (4 pogo pads, 4 magnets); in use lying on the BACK on
    the TPU ring; phone charges on the FRONT Qi coil (TX only, centre X 43).
  - **Real parts in (ADR 0013):** LP1160100 cell at its max envelope (101 x 60.5 x 11.3),
    Amphenol 124019572112A USB-C (mid-mount), CES-571423-28PMB speakers with ears cut + printed
    cradle (1.5 back plate, arms to the end wall) + 1 mm foam, NHD-2.7-12864WDW3 module,
    Adafruit 6049 mic and 5378 VEML7700 boards, PTS645 x 4, PS-7054DVB latching mute, FlexPIFA
    (turned 180 deg, adhesive, no clips), SGGP.12.4.A.02 GNSS on a 16 x 13 ground board, Molex
    212570 LTE flex on the TOP wall, pogo pads, 6 x 2 magnets. Still stand-ins: Qi coil + TX
    board, PD board, SIM board, LRA, touch strip, button strip.
  - Stack: cell (max 11.3) Z 1.0..12.3, insulator, 1.2 swell gap, **board layer Z 13.7** (was
    14.4), coil ferrite 24.8. Shell 32.8 (tray 29.8 + **lid 3.0**) + ring 1.5 = **34.3 mm** of 35.
  - Back: bare PETG, continuous TPU ring (4 wide, 2.5 in, R6, 1.0 channel, 1.5 proud, own STL)
    over 4 M2 low-head screws at (+-66, +-31.7), 2.2 holes, no counterbore; engraved ID block
    26 x 11 bottom-right seen from behind ("HeartSync" / "1 / 2" / "made with love 2026", text
    in params.csv, 0.3 deep). Fabric only on the tray TOP edge; net regenerated (one piece);
    the hand-drawn revD net and `net_d.py` were deleted.
  - Lid sections: ring channel floor to gasket channel 1.2, screw hole to gasket 1.25, screw
    hole to pad face 1.2 (`print_checks`: only thin samples left are the gaps between the
    engraved ID letters). The tongue's top half was a loose body before (not in the lid STL):
    fixed.
  - **Fit check: 36 clashing pairs** (511 bodies). Worst (mm3): btn_mute x btn_mute_cap 112.6
    (knob 12.4 tall), mic x oled 94.6, btn_mute x light 91.5, btn_vol_dn x light 62.2, btn_pwr x
    light 59.9, pd_board x speaker_cradle_R 54.1, sim7080g_module x speaker_cradle_L 43.6, light x
    mic 42.3, gnss_board x speaker_L 40.8 (0.7 in Z), mic x shell_tray 38.2, btn_vol_up x light
    32.4, pd_board x usb_c 32.0 (no cut-out), sim_board x speaker_cradle_L 23.2, light x speaker_L
    16.3, pd_board x speaker_foam_R 14.0, carrier_bracket x oled 12.5, button_strip_pcb x light
    10.1, oled x touch_strip_pcb 9.1, gnss_board x speaker_cradle_L 8.1, btn_mute x shell_tray 6.1
    (case into the wall), sim_board x speaker_foam_L 5.3, light x oled 5.2, oled x shell_tray 4.8
    (H3 boss), oled x speaker_L 4.4 (module 1.2 into the speaker top), oled x wifi_coax 2.2,
    btn_mute x speaker_L 1.9 (THT pins), then 10 under 1 mm3: tactile terminals touching their
    neighbours (9 mm wide on a 6.8 pitch), btn_play x bracket, coax/antenna/OLED corner, the
    IP5328P stand-in x USB-C. Full list with overlap boxes: the run report in the commit message.
  - Clearance rule FAIL: Wi-Fi FlexPIFA touches the OLED module (rule >= 5). LTE flex rules all
    pass (USB-C 20.1, coil 14.2); LTE is 3.6 from the cell and 3.3 from the touch strip.
  - Plans (not built), `docs/hardware/board-plans.md`: (a) SIM7080G LCC on a carrier rev B tab
    X -40..-8, Y -33..-15; (b) IP5328P board X 34.5..55.5, Y 8..32.5 with a USB-C cut-out, hot
    parts at X >= 47; (c) 20 x 3.4 sensor board in the band Y 30.4..33.8 above the OLED module,
    holes moved to Y 32.1, one 8-way flex to the carrier. Together they clear 19 of the 36 pairs (a: 3, b: 4, c: 12).
  - Layout moves still needed beyond the plans: latching mute (12.4 tall) vs its cap and the
    wall; OLED module vs the left speaker (1.2 in Z), the bracket bar, the H3 boss and the Wi-Fi
    antenna; GNSS board vs the left speaker; tactile pitch (9.8 for PTS645 terminals).
  - Safety review of this pass (2026-11-19): geometry passes (swell gap 1.2 over the 11.3 max
    cell, stack 34.3, no clash with the swell-gap keep-out). Fixed in the docs: Qi TX fed from
    the input only and gated on cell NTC, coil NTC and cold (plan b); charge-voltage strap at
    4.20 V with an I2C/voltage stop at 4.08-4.10 V (verify the IP5328P has a charge-disable
    register); NTC 10 k vs IP5328P curve and RSET <= 2.0 A to verify; cell JST and leads out
    of the hot zone plus a barrier rib on the PCM end; ring is press-fit, no adhesive; no
    underside parts over the cell on the new boards; mesh/window on the moved front holes.
  - Safety review open points (2026-11-19), still open: cell side restraint (foam pad only);
    Qi coil ferrite over the cell (cut TX on cell NTC); seals at pogo holes, buttons, mic/light
    holes; dock pads dead until seated; inserts before the cell. Closed: lid 0.45 section,
    USB-C part chosen, PD hot parts (plan b keeps them at X >= 47).
  - Missing PDFs (vendors block scripts): Amphenol 124019572112A drawing, C&K PTS645.
- **Parts library and picks:** `cad/models/` (STEP, datasheet, README per part) and
  `cad/models/open_parts.md` (picks; 2 options per open part; magnetic Qi modules, no Qi2).
  **The Molex 212570 LTE flex misses the 700 MHz bands** (B12/B13/B28/B85): confirm the
  carrier's bands, else use the Linx ANT-5GLFPC1-UFL-100 in the same spot. Order the cell with a
  10 k NTC and a JST lead.

## Where we stopped (2026-11-16 evening, user said stop and save)

- Network is now "Peace": PC **10.0.0.18**, `secrets.h` updated by the user, both
  boards reflashed (boot logs show 10.0.0.18). Build the app with
  `--dart-define=EMULATOR_HOST=10.0.0.18`. Re-check `ipconfig` first (DHCP).
- Board-B: set up as Bob on Peace, normal mode. Board-A: reflashed, in setup
  mode, not set up on Peace yet (set up as Alice from the main app copy).
- Phase 3 checks done: 1 list count, 2 wrong password (board), 5 change networks,
  6 proto mismatch. Still to run, in this order: re-run 2 on the phone (new
  network page), 3 BOOT tap with nothing pending, 4 no BOOT tap (25 s), 7 lockout,
  then grep serial and logcat for the password, token and code. Results:
  `docs/hardware/bringup-log.md`.
- App `a43fa28`: Wi-Fi network page (failures stay on it), permission message.
  Not on the Dual App copy yet; not pushed.
- **AVD testing (new, not yet run to completion):** `reva_api36` (API 36). An AVD
  has no BLE, so a debug-only simulated board (`lib/data/simulated_board.dart`,
  `--dart-define=SIMULATED_BOARD=true`) stands in for the board; registration
  is real. Suite: `app/integration_test/app_test.dart`, run with
  `app/tool/avd_test.sh` (emulators up and seeded); screenshots go to
  `app/build/avd_screens/`. The first run was stopped by the user before it
  finished, so its result is unknown. Next: run it, review the screenshots for
  UI/UX, check the PAGECOUNT line (33 networks over several 512-byte pages).
  The simulated board registers `hs-5e1a00000001` to Bob in the emulator.

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
