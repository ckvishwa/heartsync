# Phases

## Assumptions (change these when the real answer is known)

- **Bench display:** 0.96 inch 128x64 monochrome I2C OLED (SSD1306 class) on each
  board, address 0x3C or 0x3D, powered from 3V3 (ADR 0007). Driver `ssd1306`.
  The old 8x8 WS2812B driver is kept in env `esp32-s3-small-led`.
- **Logical canvas:** art always draws at 64x32 (the final HUB75 size). The OLED
  scales it 2x and thresholds colour to on/off.
- **OLED I2C pins:** SDA 21 / SCL 22 on classic ESP32, SDA 8 / SCL 9 on ESP32-S3 (`config.h`).
- **Boards:** both are classic ESP32-D0WD-V3, 4 MB (`esp32dev`). board-A (Alice)
  `hs-20500dcdfd18`, board-B (Bob) `hs-20500dcd63f4`. COM ports can move; check
  the MAC before flashing. `esp32-s3-devkitc-1` stays the default env.
- **Firebase project:** none yet. Everything runs on the emulator with project id
  `demo-heartsync`.
- **Device auth:** device signs in as its owner with a custom token (see `architecture.md`).
- **Signing:** ECDSA P-256 (see ADR 0005).

Phases 1 to 10 are prototypes. Phase 11 is the final build.

## Phase 1: Display (current: art and animation items remain)

- [x] Repo scaffold, docs, ADRs
- [x] `IDisplay` abstraction and `DISPLAY_DRIVER` build flag
- [x] `SmallLedDisplay` driver (FastLED), brightness capped at 25 percent
- [x] Heart sprite and native tests
- [x] Firmware boots, joins Wi-Fi, prints device ID, draws a static heart (builds; not yet flashed)
- [x] `Ssd1306Display` OLED driver, 64x32 logical canvas scaled 2x, I2C scan, idle dim (ADR 0007)
- [x] Display test screen (border, heart, text line) and native tests for scaling and thresholding
- [x] Identify both boards (both classic ESP32-D0WD-V3, see `docs/hardware/bringup-log.md`)
- [x] Flash board A and board B, test screen visible on both (USB power only)
- [x] Check OLED orientation (`HS_OLED_FLIP`) on the real screens (no flip needed)
- [ ] Avatar sprites (two 8x8 placeholders exist; draw real ones with `tools/pixel2header.py`)
- [ ] Simple animations in `Animator` (heartbeat pulse, fade)
- [ ] Phase 1b: `Hub75Display` driver when the 64x32 P2 panel arrives

## Phase 2: Cloud sync (done on the emulator, 2026-11-16)

- [x] Data model and security rules, tested in the emulator
- [x] `sendHeart` callable writes an event to the couple's stream
- [x] App: login and "Send heart" against the emulator
- [x] Web: device list and placeholder editor grid
- [ ] Carried over: create the real Firebase project; add its config to app, web, and `secrets.h`
- [x] Seed the couple and both devices (`tools/seed_couple.py`)
- [x] `CloudClient`: sign in with the device's custom token
- [x] `CloudClient`: listen to `couples/{id}/events` from the partner (REST polling, ADR 0008)
- [x] `CloudClient`: write device heartbeat (`lastSeen`, `online`, firmware version)
- [x] Received `heart` event draws the heart on the other board
- [x] A button or serial command on board A sends a heart; it appears on board B (BOOT button, both directions)
- [x] App: connection check (emulator ports, sign-in, pairing, boards online)
- [x] App to board and board to board hearts, both directions, on real hardware (`docs/hardware/bringup-log.md`)
- [ ] Carried over: Phase 2b signed OTA download and verify (rollback health check already in place)

## Phase 3: App

- [x] Board identity `dev_<deviceId>` with owner claims; rules, `registerDevice`, board-aware `sendHeart` (ADR 0009)
- [x] Firmware BLE setup mode: LE SC only, lockout, Wi-Fi test, token used once from RAM
- [x] Setup protocol 2: numeric comparison + BOOT confirm, paged Wi-Fi list, numbered token chunks with CRC32 (firmware and app)
- [x] App "Set up a board": scan, pair, Wi-Fi list or manual entry, register, send key
- [ ] BLE setup tested on both bench boards (numeric comparison + BOOT, confirm timeout and lockout, full Wi-Fi list, wrong Wi-Fi password, proto mismatch, change networks)
- [ ] Pairing tested on an iPhone (needs a Mac or cloud build and an Apple developer account)
- [ ] Board-id proof of possession (squatting, ADR 0009) and an unregister path
- [ ] Partner invites in the app (seed scripts until then)
- [ ] Push notifications
- [ ] Pixel editor, avatars, settings

## Phase 4: Touch and haptics

- [ ] Touch strip input
- [ ] LRA haptics with DRV2605L
- [ ] `touch` events

## Phase 5: Motion

- [ ] IMU bring-up
- [ ] Gestures (shake, tilt, pick-up)

## Phase 6: Audio

- [ ] Stereo speakers, Bluetooth audio module
- [ ] Speaker DSP on the S3 for the CES-571423-28PMB (ADR 0012, Fs 700 Hz): bass shelf,
      virtual bass (harmonics below Fs), output limiter. Native tests for the filter math.
- [ ] Sound effects for events

## Phase 7: Voice

- [ ] I2S mic capture
- [ ] `voice` events (record, upload, play)

## Phase 8: Power

- [ ] Characterise panel current; revisit the brightness cap
- [ ] LiPo, protection board, USB-C PD power bank chip
- [ ] Wireless charging, 90 percent docked charge stop
- [ ] Backup cell

## Phase 9: Tracking

- [ ] LTE-M/GNSS module bring-up
- [ ] Location sharing with consent controls

## Phase 10: Enclosure and dock

- [ ] Printed enclosure within 3.5 cm, fabric wrap
- [ ] Dock with four magnets and pogo pins
- [ ] IP54 design review

## Phase 11: Final product

- [ ] Release-build gate before burning flash and NVS encryption eFuses (ADR 0009). All must be true:
  - Signed OTA download, verify and rollback tested on real boards
  - BLE Wi-Fi setup works, including changing networks later
  - All hardware final and tested on the S3 boards
  - Rehearsal burn done on a spare S3 (boot, OTA, NVS read-back)
  - Key backup decision made and recorded
- [ ] Final PETG build of both devices
- [ ] Pre-pair, final firmware, gift packaging
