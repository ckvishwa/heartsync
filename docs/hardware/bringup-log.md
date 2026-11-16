# Bring-up log

Bench setup: two ESP32 dev boards on USB power only, each with a 0.96 inch
128x64 monochrome I2C OLED (SSD1306 class). See `pinout.md` for wiring.

## Board identification (esptool `chip_id` / `flash_id`, 2026-11-16)

| Label | Owner (seed) | COM port | Chip | Revision | Flash | PSRAM | MAC | Device ID | PIO env |
|-------|--------------|----------|------|----------|-------|-------|-----|-----------|---------|
| board-A | Alice (`--person a@example.com:Alice:...`) | COM3 (CP210x) | ESP32-D0WD-V3 (classic, dual core, 240 MHz) | v3.1 | 4 MB (mfr 0x68, dev 0x4016), 3.3 V | none embedded; external confirmed at first boot | 20:50:0d:cd:fd:18 | `hs-20500dcdfd18` | `esp32dev` |
| board-B | Bob (`--person b@example.com:Bob:...`) | _not detected_ | _pending_ | | | | | | |

Notes:

- Labels follow detection order; board-A is the first board that answered. Board-A
  is Alice's board, board-B is Bob's, matching `tools/seed_couple.py`.
- Device ID is `hs-` plus the base MAC in hex, as printed by the firmware at boot.
- Board-B: no second USB serial device enumerated on 2026-11-16 (only COM3 present).
  Usual cause is a charge-only USB cable. Fix: try a known data cable and another
  port; if the port appears but esptool cannot connect, hold BOOT, tap EN, release BOOT.
  An S3 DevKitC needs the cable in the port labelled UART for serial logs.

## Wiring check

- board-A is a classic ESP32: OLED SDA on GPIO 21, SCL on GPIO 22 (default Wire pins). Matches.

## First boot (Step 3)

_Filled in after flashing: firmware version, chip, free heap, display driver, I2C address._
