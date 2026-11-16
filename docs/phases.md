# Phases

## Assumptions (change these when the real answer is known)

- **Small LED type:** 8x8 WS2812B (NeoPixel-style) matrix, 64 LEDs, GRB, one data
  pin, serpentine wiring, powered from the board's 5 V pin over USB. If it is a
  strip, set `HS_MATRIX_HEIGHT` to 1 in `firmware/include/config.h`.
- **LED data pin:** GPIO 5 on ESP32-S3, GPIO 4 on classic ESP32 (`config.h`).
- **Board:** `esp32-s3-devkitc-1` by default; `esp32dev` env exists for classic ESP32.
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
- [ ] Confirm the LED type, size, colour order, and data pin on both boards
- [ ] Flash board A and board B, heart visible on both (USB power only)
- [ ] Check serpentine vs progressive wiring and rotation with a test pattern
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
