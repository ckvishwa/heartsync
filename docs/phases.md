# Phases

## Assumptions (change these when the real answer is known)

- **Bench display:** 0.96 inch 128x64 monochrome I2C OLED (SSD1306 class) on each
  board, address 0x3C or 0x3D, powered from 3V3 (ADR 0007). Driver `ssd1306`.
  The old 8x8 WS2812B driver is kept in env `esp32-s3-small-led`.
- **Logical canvas:** art always draws at 64x32 (the final HUB75 size). The OLED
  scales it 2x and thresholds colour to on/off.
- **OLED I2C pins:** SDA 21 / SCL 22 on classic ESP32, SDA 8 / SCL 9 on ESP32-S3 (`config.h`).
- **Boards:** both are classic ESP32-D0WD-V3, 4 MB (`esp32dev`). board-A (Alice)
  `hs-20500dcdfd18`, board-B (Bob) `hs-20500dcd63f4`. Their CP210x share a USB
  serial number, so plug in one at a time. `esp32-s3-devkitc-1` stays the default env.
- **Firebase project:** none yet. Everything runs on the emulator with project id
  `demo-heartsync`.
- **Device auth:** device signs in as its owner with a custom token (see `architecture.md`).
- **Signing:** ECDSA P-256 (see ADR 0005).

Phases 1 to 10 are prototypes. Phase 11 is the final build.

## Phase 1: Display (current)

- [x] Repo scaffold, docs, ADRs
- [x] `IDisplay` abstraction and `DISPLAY_DRIVER` build flag
- [x] `SmallLedDisplay` driver (FastLED), brightness capped at 25 percent
- [x] Heart sprite and native tests
- [x] Firmware boots, joins Wi-Fi, prints device ID, draws a static heart (builds; not yet flashed)
- [x] `Ssd1306Display` OLED driver, 64x32 logical canvas scaled 2x, I2C scan, idle dim (ADR 0007)
- [x] Display test screen (border, heart, text line) and native tests for scaling and thresholding
- [x] Identify both boards (both classic ESP32-D0WD-V3, see `docs/hardware/bringup-log.md`)
- [ ] Flash board A and board B, test screen visible on both (USB power only)
- [ ] Check OLED orientation (`HS_OLED_FLIP`) on the real screens
- [ ] Avatar sprites (two 8x8 placeholders exist; draw real ones with `tools/pixel2header.py`)
- [ ] Simple animations in `Animator` (heartbeat pulse, fade)
- [ ] Phase 1b: `Hub75Display` driver when the 64x32 P2 panel arrives

## Phase 2: Cloud sync (current)

- [x] Data model and security rules, tested in the emulator
- [x] `sendHeart` callable writes an event to the couple's stream
- [x] App: login and "Send heart" against the emulator
- [x] Web: device list and placeholder editor grid
- [ ] Create the real Firebase project; add its config to app, web, and `secrets.h`
- [ ] Seed the couple and both devices (`tools/seed_couple.py`)
- [ ] `CloudClient`: sign in with the device's custom token
- [ ] `CloudClient`: listen to `couples/{id}/events` where `from != owner`
- [ ] `CloudClient`: write device heartbeat (`lastSeen`, `online`, firmware version)
- [ ] Received `heart` event draws the heart on the other board
- [ ] A button or serial command on board A sends a heart; it appears on board B
- [ ] Phase 2b: signed OTA download and verify (rollback health check already in place)

## Phase 3: App

- [ ] Real pairing flow (BLE setup and Wi-Fi provisioning)
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

- [ ] Final PETG build of both devices
- [ ] Pre-pair, final firmware, gift packaging
