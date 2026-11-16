# Bring-up log

Bench setup: two ESP32 dev boards on USB power only, each with a 0.96 inch
128x64 monochrome I2C OLED (SSD1306 class). See `pinout.md` for wiring.

## Board identification (esptool `chip_id` / `flash_id`, 2026-11-16)

| Label | Owner (seed) | COM port | Chip | Revision | Flash | PSRAM | MAC | Device ID | PIO env |
|-------|--------------|----------|------|----------|-------|-------|-----|-----------|---------|
| board-A | Alice (`--person a@example.com:Alice:...`) | COM6 (CP210x, USB-C to C cable) | ESP32-D0WD-V3 (classic, dual core, 240 MHz) | v3.1 | 4 MB (mfr 0x68, dev 0x4016), 3.3 V | none embedded; external confirmed at first boot | 20:50:0d:cd:fd:18 | `hs-20500dcdfd18` | `esp32dev` |
| board-B | Bob (`--person b@example.com:Bob:...`) | COM3 (CP210x, USB-A to C cable) | ESP32-D0WD-V3 (classic, dual core, 240 MHz) | v3.1 | 4 MB, 3.3 V | none embedded; external confirmed at first boot | 20:50:0d:cd:63:f4 | `hs-20500dcd63f4` | `esp32dev` |

Notes:

- Labels follow detection order; board-A is the first board that answered. Board-A
  is Alice's board, board-B is Bob's, matching `tools/seed_couple.py`.
- Device ID is `hs-` plus the base MAC in hex, as printed by the firmware at boot.
- Both CP210x bridges report the same USB serial number (`0001`). Windows copes:
  the second board gets a location-based instance ID and its own COM port. COM
  numbers can change when cables or ports move, so **confirm the MAC with esptool
  before every flash**.
- Cables that work (2026-11-16): one USB-A to USB-C, one USB-C to USB-C. The
  cable board-B used first gave no data link (likely charge-only); keep it off the bench.

### Board-B detection attempts (2026-11-16)

User reports both boards are the same model, and OLEDs on 3V3.

| # | Action by user | Ports seen | Board on COM3 (MAC) | Result |
|---|----------------|------------|---------------------|--------|
| 1 | Both boards plugged in | COM3 | 20:50:0d:cd:fd:18 (board-A) | board-B not seen |
| 2 | Swapped USB ports | COM3 | 20:50:0d:cd:fd:18 (board-A) | board-B not seen |
| 3 | Swap cable/board test requested | COM3 | 20:50:0d:cd:fd:18 (board-A) | board-B not seen |
| 4 | Recheck | COM3 | 20:50:0d:cd:fd:18 (board-A) | board-B not seen |
| 5 | Board-B alone, on board-A's cable and port | COM3 | 20:50:0d:cd:63:f4 (board-B) | **board-B identified** |
| 6 | Both boards: one USB-A to C, one C to C cable | COM3 + COM6 | COM3 = board-B (63:f4), COM6 = board-A (fd:18) | **both boards up** |

Resolved: the cable board-B used at first carried no data. With two data cables
both boards enumerate at once. (An earlier note blamed the duplicate CP210x serial
number; attempt 6 disproves that.)

## Wiring check

- Both boards are classic ESP32: OLED SDA on GPIO 21, SCL on GPIO 22 (default Wire pins). Matches.

## First boot (Step 3)

Flashed 2026-11-16 over USB (`pio run -e esp32dev -t upload --upload-port COMx`),
MAC verified with esptool before each upload. Firmware commit `9f21871`
(display code), no `secrets.h` yet.

| Label | Port | MAC checked | Upload | FW | Device ID | Chip (boot log) | PSRAM | Free heap at boot | Display driver | I2C scan | OLED address | Display init |
|-------|------|-------------|--------|----|-----------|-----------------|-------|-------------------|----------------|----------|--------------|--------------|
| board-B | COM3 | 20:50:0d:cd:63:f4 | SUCCESS | 0.1.0 | `hs-20500dcd63f4` | ESP32-D0WD-V3 rev 3, 2 cores, 4096 KB flash | 0 KB | 306744 B | ssd1306, logical 64x32 x2, mono | 1 device | 0x3C | ok, flip=0 |
| board-A | COM6 | 20:50:0d:cd:fd:18 | SUCCESS | 0.1.0 | `hs-20500dcdfd18` | ESP32-D0WD-V3 rev 3, 2 cores, 4096 KB flash | 0 KB | 307352 B | ssd1306, logical 64x32 x2, mono | 1 device | 0x3C | ok, flip=0 |

Both log `wifi: no credentials` (expected until `include/secrets.h` exists) and
`cloud: sync not implemented yet` (Phase 2 stub). Display init takes about 1.4 s
(U8g2 begin). Visual check of the test screen: _pending user confirmation_.
