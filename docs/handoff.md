# Handoff: where we are and what to do next

Last updated: 2026-11-19 evening (enclosure full pass: 157 mm, dead-front 3.12 in panel, custom boards planned, fit check 0 clashes; Phase 3 hardware test still pending). Read this first in a new session, then `CLAUDE.md`,
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

## Ansonia rev G in Fusion (2026-11-23): digital clone, 18 clashes

- `cad/fusion/ansonia_revG.py` (+ `run_revG.py`, `export_boards.sh`, `board_standins.py`, `cad/params_revG.csv`)
  builds the rev G shell, lid, speaker boxes, bracket, TPU parts and every part, imports the four board STEPs
  (commit `36561403` placement), runs interference + clearance/antenna/cable/mass checks. Report, clash list and
  every interpretation: **`docs/hardware/fusion_revG.md`**. Outputs: `cad/exports/revG/` (3MF per part, STEP zip,
  .f3d), `cad/renders/revG/`. The Fusion tab is unsaved (not in the cloud).
- Biggest clashes: the 30 mm Dayton drivers sit on the lid tongue / gasket / end hooks; power board, J7, USB-C 2
  reach 1.2 into speaker box R; OLED 1.2 into box L; MR30 plug on the nano-SIM; button PCB blocks J7/J8/J12;
  carrier J1 and power J1 face each other 2 mm apart. Nothing fixed yet: waiting for the user's choices.
- Safety review (same day) lists blockers at the top of that file: 35.5/38.0 vs the 35 mm hard limit, screw heads
  and power back-side parts in the swell gap, no cell retention, cell on the e-paper glass, NTC connector blocked,
  IP5356M + L1 over the cell end, no vent.
- Rebuild after a placement change: `bash cad/fusion/export_boards.sh`, then `go("build")`, `go("exports")`, `go("shots")`.
- **Option B (user's choice, same day):** shell 35.0 (front wall 1.7, ribs; safety.md updated), interior 30.3 kept
  for the Dayton drivers. The ~8 mm free layer is now sealed back-box chambers glued to each speaker box:
  back volume L 23.2 -> 32.0 cc, R 23.2 -> 35.8 cc, all >= 5.0 mm from the antennas, 0.5 under the Qi ferrite.
  Electronics minimum: 26.8 mm (30.8 with the MR30/PH on the power board). 16 clashes left (the drawn ones).
- **Power-board change needed (board session, not done in KiCad):** J7 PH -> JST SM02B-SRSS-TB and turn it to take
  the cable from +Y/-Y (box R blocks +X); remove MR30 J4 and keep TP1/TP2 for an 18 AWG pigtail (better on the
  back side at X >= 48); then re-export and rebuild.

## Ansonia rev A custom boards (2026-11-23, ADR 0019)

Reviews 1-3 applied (IP5356M charger, own Qi boost, 5 A / 8 A budget, MR30 + wire pads, e-paper (G) verified). Routing in progress: touch strip
done, front sensor nearly, carrier RF hand-routed + autorouter run, power board not routed (see Hardware/pcb/README.md 'Routing status').
Next: finish routing, DRC clean, exports (Gerber/BOM/CPL/PDF/renders). Open: cell PCM limit, IP5356M I2C address + dual-Type-C part number.

- `Hardware/pcb/` (read its `README.md`): carrier, power, front_sensor, front_touch as KiCad 10 projects,
  generated by `Hardware/pcb/tools/`. Schematics ERC 0/0, netlists cross-checked, boards outlined and
  **placed, not routed**. Waiting for the user's placement review (`Hardware/pcb/placement_review.png`).
- Next after the review: route RF (CPWG) and power by hand, then the rest; DRC against JLCPCB rules;
  Gerbers/BOM/CPL; then commit and push (the user asked for push when done).
- Open: PD IC choice (placeholder), PH2.0 cell connector vs ~7 A audio peaks, BT antenna spot, e-paper size,
  USB-C footprint built from the drawing (verify), H3/H4 moved.

## Carrier board and enclosure (2026-11-19)

- **Carrier PCB** (`Hardware/heartsync_kicad/`, read its `CLAUDE.md`): placement done, not routed.
  - U1 is now the **ESP32-S3-WROOM-1U-N16R8** (ADR 0011, Proposed): U.FL socket, external 2.4 GHz
    flex antenna on the shell wall, no antenna keepout. Socket faces the top edge at (23.0, 2.96) mm.
  - J4 (left speaker) on the left edge, J5 (right) on the right edge.
  - DRC: 0 courtyard, keepout, hole and drill errors. 11 starved thermals wait for routing.
  - Antenna: **Ezurio FlexPIFA 001-0014** (ADR 0011), now on the front wall bottom-left, outside
    the phone footprint. Flex PIFA differs from the certified monopole: extra RF/EMC testing.
  - Next in order: route power, I2S, USB pair, rest; DRC clean; STEP fit check in Fusion.
- **Enclosure, full pass (2026-11-19 evening): 157 x 72.5, fit check 0 clashes** (445 bodies).
  `cad/fusion/heartsync_assembly.py`, dimensions in `cad/params.csv`, positions in its POS block.
  `HS_PHASE` (env, default 4) rebuilds stage 1-4. One run is about 9 min (longer than the MCP
  timeout): the runner opens a new document, loads the script with importlib, writes the report to
  a file. The final build is the open, **unsaved** Fusion tab (not saved to the cloud; "HeartSync
  v1" in the cloud is older). ADRs 0014 (length 157, front fabric, tray 29.4), 0015 (dead-front
  bare SSD1322 panel), 0016 (custom boards, cell turned).
  - Clashing pairs by phase: before 36 -> 1 size + front 23 -> 2 real parts 17 -> 3 safety +
    print 17 (all 17 were the Adafruit sensor boards and the PD stand-in) -> 4 custom boards 1
    (IP5328P vs its MOSFET, moved) -> **0**.
  - Front: bare 3.12 in panel X -76..12 (2.5 from the left end), Y -9.9..17.9, FPC folded
    behind; window 79.8 x 22.2 on the VA (VA ends **2.06** before the phone zone); smoked PC lens
    82.8 x 25.2 x 1.0 flush with the fabric on a 1.5 foam gasket; tuck groove 1.0 wide, 0.8 deep
    (same floor as the lens recess, so the ledge prints as one 2.7 mm overhang: check in PLA);
    Qi ring 0.4 proud under the fabric; touch pocket from inside (1.2 wall); mic (-48, 20.8) and
    light (-42.5, 20.8) holes, sealed.
  - Qi coil at X 47.95: magnet ring **3.05** from the right end's outer face (0.85 from its inner
    face); speaker_R box 1.9 from the magnet ring, ferrite 1.1 from it; driver magnet (estimated,
    not modelled) about 13.4 from the ring.
  - Stack **34.9** (lid 3.0 + tray 29.4 + fabric 0.6 + ring 0.4 + back ring 1.5). Swell gap 1.2
    over the 11.3 max cell, board layer Z 13.7.
  - Top edge (ADR 0017, 0018): one 51.6 x 9.2 pocket (X -70..-18.4, Z 19.7) with a 2 mm rib
    between VOL- and VOL+, one flush TPU strip (own STL) with five evenly spread 0.6 icons and
    0.8 groove rings. Five low PTS810 switches (MUTE is a firmware toggle + red LED) sit over
    speaker_L, each 1.0 above its icon with a nub under the TPU. Two USB-C ports (port 1
    bidirectional at X 53.3, port 2 output only at X 40.5, no USB-A). **LTE to port 2 is 6.3 mm
    (5.8 to the gasket) against the 7 mm rule: 10 mm needs about 161.2 mm** (ADR 0018).
  - Ends (ADR 0017): 230 round holes per end (dia 1.6, 2.5 pitch, web 0.9), brass-tone trim
    frame 61 x 26.3 sunk flush in a 0.6 channel (pocket floor Z 1.8): overall length stays 157.
  - Back: engraved "Rexi" only, 6.5 mm letters, 0.3 deep, bottom-right seen from behind.
  - Print checks (2026-11-20): tray 0 thin samples (grille webs 0.9 by spec), lid 0, strip flange 0.6 and
    skins 1.0 / LED well 0.5 by design. Strip windows bridge 30.0 and 19.6 mm when the tray prints
    front-down (66 + 43 mm2 overhang): PLA test print first. Open: MIC_MUTE_BTN / MUTE_LED pins,
    PTS810 real height, LTE gap (ADR 0018).
  - Wi-Fi coax: thick end -> R 9 S-bend under the panel FPC and front board -> R 8 turns -> U.FL;
    min bend radius **6.2**, 79.8 of 100 mm used (stow 20 mm).
  - Carrier: no front-wall bosses at H3/H4 (the panel covers them); a printed bracket frame holds
    all four holes, the front board (3 x M1.6 into front-wall bosses) clamps it.
  - Cell turned: PCM/seal end at -X, foam frame on lid ribs (ends full height, sides low), stretch-
    release strips under it; leads along the top channel (order 150 mm leads, JST PH 3-pin).
  - Seals: pogo pad flange + silicone washer + pogo board, top strip, mic ePTFE membrane, light PC
    window, USB-C IPX8 + gasket.
  - Print checks: tray 0 thin samples (grille webs 0.9 by spec: PLA test print), lid 0 (ID text
    letter gaps listed apart), bracket and cradles 0; strip flange 0.6 TPU by design.
  - Generated: `cad/net/heartsync_net.dxf/.pdf` (FRONT + TOP, one piece), `cad/renders/*.jpg`
    (`tools/renders_to_jpg.py`), `cad/exports/` (git-ignored; top strip STL added).
  - New docs: `docs/hardware/assembly-order.md` (inserts first, cell last, pads dead until docked,
    charge stop about 90 percent), `docs/hardware/board-plans.md` (carrier rev B tab, front board,
    power board, Qi TX options), panel model `cad/models/oled_wex025664b_panel_312`.
  - Still stand-ins: Qi coil + TX board (plan d recommends a 15 W PCBA flat under the coil), LRA.
  - Safety review of this pass (2026-11-19): fixed in model/docs: battery connector SMD
    (S3B-PH-SM4-TB), Qi/dock switches moved off the cell, dock switch must block reverse current,
    Qi "input present" from charger status (USB-C port input-only), Qi module must have FOD and
    over-temperature shutdown, screw-pad washers (inside the gasket line), lead dressing, venting
    note, Phase 8 gate on the cell step. Still open: USB-C shell legs over the cell (Amphenol
    drawing), a positive mount for the power board, 90 % stop is firmware-only (fallback 4.20 V),
    stack margin 0.1 mm (measure fabric; fallback ring 0.3 or back ring 1.4), Phase 8 cell
    thermocouple test. `docs/hardware/fit/` (untracked revE files) still shows the cell PCM at +X.
  - Open: verify the panel thickness/FPC on arrival; the SSD1322 needs a driver behind
    `IDisplay` and a VCC enable pin; new pins (OLED_VCC_EN, QI_EN, DOCK_SEATED) wait for rev B;
    IP5328P charge-disable register and NTC curve; LTE 700 MHz bands (Molex) vs carrier.
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
