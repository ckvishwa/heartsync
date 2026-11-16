# Bring-up checklist

One part at a time. Run `/bringup-check` to be walked through it. USB power only
until Phase 8. Read `safety.md` before touching anything with a battery.

## Phase 1: boards and small LEDs

### Board A

- [ ] Identify the board model; record it in `pinout.md`
- [ ] `pio run -e <env> -t upload` succeeds
- [ ] Serial at 115200 shows the boot log and the device ID; record the ID in `pinout.md`
- [ ] Wi-Fi connects (after creating `include/secrets.h`)

### Small LED A

- [ ] Identify the LED type, pixel count, and layout; update `config.h` if not 8x8 WS2812B
- [ ] Wire 5V, GND, and data to `HS_PIN_LED_DATA` (board unpowered while wiring)
- [ ] Heart appears, red, the right way up
- [ ] If colours are wrong: fix `HS_LED_COLOR_ORDER`. If rows are mirrored: toggle `HS_MATRIX_SERPENTINE`
- [ ] LED and board stay cool after 10 minutes at the 25 percent cap

### Board B and small LED B

- [ ] Repeat all of the above for board B

## Phase 2: cloud sync

- [ ] Both device IDs registered under the couple (`tools/seed_couple.py`)
- [ ] Each board reports `online` and `lastSeen` in Firestore
- [ ] Heart sent from the app appears on the partner's board
- [ ] Heart sent from board A appears on board B, and the reverse

## Phase 1b: HUB75 panel

- [ ] Panel powered from a bench 5 V supply sized for it (not the dev board's 5V pin)
- [ ] Pins assigned in `config.h` and `pinout.md`
- [ ] `DISPLAY_DRIVER=hub75` build shows the same heart with no changes outside `src/display/`

## OTA (Phase 2b)

- [ ] Signed update installs and marks itself healthy
- [ ] An update that never marks itself healthy rolls back after 60 seconds
- [ ] A tampered or unsigned binary is refused

## Later phases

Add a section per part as each phase starts: touch, DRV2605L and LRA, IMU, light
sensor, speakers and Bluetooth audio, mic, power chain (Phase 8), LTE-M/GNSS, dock.
