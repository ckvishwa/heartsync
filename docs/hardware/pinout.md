# Pinout

Mirror of `firmware/include/config.h`. **Change both together.** Code never
contains a pin number outside `config.h`.

## Board A / Board B identity

| Board | Model | Device ID | Notes |
|-------|-------|-----------|-------|
| A | _to confirm_ | _printed on serial at boot_ | |
| B | _to confirm_ | _printed on serial at boot_ | |

## ESP32-S3 DevKitC-1 (`env:esp32-s3-devkitc-1`, flag `HS_BOARD_ESP32_S3_DEVKITC`)

| Function | Macro | GPIO | Notes |
|----------|-------|------|-------|
| Small LED data | `HS_PIN_LED_DATA` | 5 | Not a strapping pin. A 330 ohm series resistor near the first LED is recommended. |
| LED power | - | 5V pin | From USB. Current limited in software. |
| Ground | - | GND | Common ground with the LED. |

Avoid on S3: 0, 3, 45, 46 (strapping), 19 and 20 (USB), 26 to 32 (flash),
33 to 37 on octal-PSRAM modules. Verify against the module datasheet.

## Classic ESP32 DevKit (`env:esp32dev`, flag `HS_BOARD_ESP32_DEV`)

| Function | Macro | GPIO | Notes |
|----------|-------|------|-------|
| Small LED data | `HS_PIN_LED_DATA` | 4 | Not a strapping pin. |
| LED power | - | VIN / 5V pin | From USB. |
| Ground | - | GND | |

Avoid on classic ESP32: 0, 2, 5, 12, 15 (strapping), 6 to 11 (flash),
34 to 39 (input only), 16 and 17 on WROVER modules.

## HUB75 panel (Phase 1b)

Not assigned. The panel needs 13 or 14 GPIOs (R1, G1, B1, R2, G2, B2, A to D or E,
CLK, LAT, OE). Assign in `config.h` when the panel arrives and fill this table.

## Later peripherals

I2C (IMU, DRV2605L, light sensor), I2S (mic), touch, UART (LTE-M/GNSS): not
assigned. Add a row here and a macro in `config.h` in the phase that introduces each.
