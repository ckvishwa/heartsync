# Pinout

Mirror of `firmware/include/config.h`. **Change both together.** Code never
contains a pin number outside `config.h`.

## Board A / Board B identity

| Board | Model | Device ID | Notes |
|-------|-------|-----------|-------|
| A (Alice) | ESP32-D0WD-V3 dev board, 4 MB flash (`esp32dev`) | `hs-20500dcdfd18` | COM6 on 2026-11-16 (C to C cable); verify MAC before flashing |
| B (Bob) | ESP32-D0WD-V3 dev board, 4 MB flash (`esp32dev`) | `hs-20500dcd63f4` | COM3 on 2026-11-16 (A to C cable); verify MAC before flashing |

## Bench OLED (both boards)

0.96 inch, 4-pin, I2C, 128x64 monochrome, SSD1306 class. Address 0x3C (0x3D also
accepted; the firmware scans the bus at boot). Pull-ups are on the OLED module.
Power from 3V3, never 5V.

| OLED pin | Classic ESP32 | ESP32-S3 | Macro |
|----------|---------------|----------|-------|
| GND | GND | GND | - |
| VCC | 3V3 | 3V3 | - |
| SCL | GPIO 22 | GPIO 9 | `HS_PIN_I2C_SCL` |
| SDA | GPIO 21 | GPIO 8 | `HS_PIN_I2C_SDA` |

## BOOT button (both boards)

`HS_PIN_BUTTON` = GPIO 0, on-board BOOT button, active low. Input only (strapping
pin: never drive it).

- **Tap** (released within `HS_SETUP_TAP_MAX_MS`, 1 s): send a heart.
- **Hold 5 s while running** (`HS_SETUP_LONG_PRESS_MS`): the OLED counts down,
  then the board wipes Wi-Fi and tokens and restarts into BLE setup (ADR 0009). In
  setup mode a hold clears the pairing lockout.
- **Never hold it while powering on or resetting**: GPIO 0 low at boot enters the ROM
  download mode instead of the firmware.

## ESP32-S3 DevKitC-1 (`env:esp32-s3-devkitc-1`, flag `HS_BOARD_ESP32_S3_DEVKITC`)

| Function | Macro | GPIO | Notes |
|----------|-------|------|-------|
| OLED SDA | `HS_PIN_I2C_SDA` | 8 | I2C. |
| OLED SCL | `HS_PIN_I2C_SCL` | 9 | I2C. |
| BOOT button | `HS_PIN_BUTTON` | 0 | Input only, active low. |
| Small LED data | `HS_PIN_LED_DATA` | 5 | `small_led` driver only. A 330 ohm series resistor near the first LED is recommended. |
| LED power | - | 5V pin | From USB. Current limited in software. |
| Ground | - | GND | Common ground with the LED. |

Avoid on S3: 0, 3, 45, 46 (strapping), 19 and 20 (USB), 26 to 32 (flash),
33 to 37 on octal-PSRAM modules. Verify against the module datasheet.

## Classic ESP32 DevKit (`env:esp32dev`, flag `HS_BOARD_ESP32_DEV`)

| Function | Macro | GPIO | Notes |
|----------|-------|------|-------|
| OLED SDA | `HS_PIN_I2C_SDA` | 21 | Default Wire SDA. |
| OLED SCL | `HS_PIN_I2C_SCL` | 22 | Default Wire SCL. |
| BOOT button | `HS_PIN_BUTTON` | 0 | Input only, active low. |
| Small LED data | `HS_PIN_LED_DATA` | 4 | `small_led` driver only. |
| LED power | - | VIN / 5V pin | From USB. |
| Ground | - | GND | |

Avoid on classic ESP32: 0, 2, 5, 12, 15 (strapping), 6 to 11 (flash),
34 to 39 (input only), 16 and 17 on WROVER modules.

## HUB75 panel (Phase 1b)

Not assigned. The panel needs 13 or 14 GPIOs (R1, G1, B1, R2, G2, B2, A to D or E,
CLK, LAT, OE). Assign in `config.h` when the panel arrives and fill this table.

## Later peripherals

I2C (IMU, DRV2605L, light sensor) will share the OLED bus above. I2S (mic), touch, UART (LTE-M/GNSS): not
assigned. Add a row here and a macro in `config.h` in the phase that introduces each.
