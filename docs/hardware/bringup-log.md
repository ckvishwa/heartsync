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
(U8g2 begin). Visual check (user, 2026-11-16): **pass on both boards.** Border, 2x heart and
"HEARTSYNC 0.1.0" visible, orientation correct (`HS_OLED_FLIP` stays 0), idle
dimming after 30 s works.

**Step 3 result: board-A PASS, board-B PASS.**

## Phase 2 sync (Step 4, 2026-11-16)

Network: open 2.4 GHz hotspot "DeltaForce " (trailing space in the SSID), PC
10.143.236.144 running the emulators on 0.0.0.0, phone on the same network.
Home network "Peace" refused the boards at the auth step (reason 2) and was not used.

| Test | Result | Evidence |
|------|--------|----------|
| Both boards sign in (custom token, then refresh token) | PASS | `state=polling uid=alice partner=bob` / `uid=bob partner=alice` |
| Heartbeat (`lastSeen`, `online`, fw) | PASS | device docs updated every 60 s; app shows both online |
| BOOT on board-A sends a heart, board-B shows it | PASS | user observed |
| BOOT on board-B sends a heart, board-A shows it | PASS | user observed |
| App as Bob sends a heart, board-A (Alice) shows it | PASS | 5 events from bob 18:27:39-18:27:58Z, board-A logged 5x `heart from bob` |
| App as Alice sends a heart, board-B (Bob) shows it | PASS | events 18:27:15Z, 18:28:17Z; user observed on board-B |

Fixes on the way: uid read from the ID token (custom-token sign-in has no
`localId`); app Firebase options from `--dart-define-from-file` because the
Android SDK rejected the API key `demo-key` ("Please set a valid API key").

Board-to-board serial evidence: board-B `BOOT button pressed` then `heart sent`,
board-A `heart from bob`; board-A `heart sent`, board-B `heart from alice`.
Defect found: board-A's first press logged `sendHeart failed (status -11)` (HTTP
read timeout, 3 s) although the server created the event (board-B received it),
so the screen said NOT SENT. Fixed: `sendHeart` now has its own 10 s timeout.

## Phase 3 BLE setup, protocol 2 (2026-11-16, partial)

Firmware `5f39d40` (numeric comparison + BOOT confirm, paged Wi-Fi list, token
frames with CRC32) flashed over USB: board-B on COM3 (MAC `20:50:0d:cd:63:f4`
checked first), board-A on COM7 (MAC `20:50:0d:cd:fd:18` checked first). App
`91e1da2` and later on the Samsung S24, main profile and Dual App profile (user
95). PC 10.143.236.144; emulators re-seeded at 22:05Z after a restart had wiped
Auth.

| Test | Result | Evidence |
|------|--------|----------|
| App proto 2 refuses a proto 1 board | PASS | before board-B was reflashed, the app showed "Update the board firmware: it uses an older setup protocol (1, this app needs 2)" and disconnected; the board went back to SET UP |
| Board-B (new firmware) in setup mode shows the code and waits for BOOT | PASS | serial `pairing: code shown, waiting for a BOOT tap`; emulator host 10.143.236.144 |
| Registry refuses another person's board | PASS (by accident) | phone signed in as Alice, chose board-B: "This board is registered to someone else."; Auth emulator showed Alice as the last login |
| Board-B set up as Bob: pair (codes, Pair, BOOT), Wi-Fi list, password, register, key, sign-in | PASS (outcome) | user report; serial afterwards `mode=normal wifi=1 heap=158208 min=149664`; device doc heartbeating |
| Board-A set up as Alice | PASS (outcome only) | **setup not captured on serial** (it finished before the capture began); verified by outcome: `mode=normal wifi=1`, `heartbeat ok (online, fw 0.1.0)` |
| App as Bob sends hearts, board-A shows them | PASS | board-A serial: 16x `heart from bob` |
| BOOT tap on board-A sends a heart | PASS | board-A `BOOT tap: sending heart`, `heart sent`; 15 events from alice in the cloud (last 22:33:06Z) |
| Board-B shows Alice's hearts | NOT CAPTURED | events exist in the cloud; board-B serial was not being read at the time |
| No secrets in board-A serial | PASS | no `eyJ` (token), no password text in a 100 s capture |
| Heap with Wi-Fi up after setup | PASS | board-A 158240 free, min 148252; board-B 158208, min 149664 |

Not yet run (remaining Phase 3 checks): Wi-Fi list count against the board's
scan, wrong Wi-Fi password, BOOT tap with nothing pending, no BOOT tap (25 s
reject), change networks, proto mismatch with the new firmware, lockout. Also not
yet recorded: Wi-Fi scan and connect while a BLE link is up (the setups above
show it works on esp32dev, but the scan count was not compared).

### Remaining checks, run 2026-11-16 evening (stopped part-way)

Network moved from the "DeltaForce " hotspot to "Peace" (2.4 GHz, WPA2): PC
10.0.0.18, phone 10.0.0.52. The user updated `secrets.h`; both boards reflashed
(MACs checked) and boot logs show `emulator 10.0.0.18`. App rebuilt for 10.0.0.18.

| Step | Result | Evidence |
|------|--------|----------|
| 1 Wi-Fi list count | PASS | board-B `Wi-Fi scan: 15 networks, 2 pages`; app showed 15 |
| 2 Wrong Wi-Fi password | PASS (board) | board-B 17:57:09 `Wi-Fi test failed (auth)` (reason 15, 4-way handshake); retry with the right password 17:57:31 `Wi-Fi "Peace" works; saved`, signed in, normal mode on Peace (ip 10.0.0.3) |
| 2 App after a wrong password | FAIL, fixed in `a43fa28` | the app went back to the list and forgot the network; now a network page keeps it, with the reason on top. Re-run on the phone still pending |
| 3 BOOT tap with nothing pending | NOT RUN | |
| 4 No BOOT tap (25 s reject) | NOT RUN | |
| 5 Change networks | PASS (in passing) | board-B moved from "DeltaForce " to "Peace" by hold + setup |
| 6 Proto mismatch | PASS (earlier today) | see above; not repeated with the new firmware |
| 7 Lockout | NOT RUN | |
| Secrets grep (serial + logcat) | NOT RUN | logs saved in the session scratchpad only |

Also found: the Dual App profile (user 95) had no Nearby devices permission and the
app said "Turn on Bluetooth"; fixed in `a43fa28` (asks for the permission). The
Dual copy does not have that build yet (adb dropped during install). Wireless adb
turns off when the phone changes Wi-Fi network.

