# 0001: Controller is the ESP32-S3

- **Date:** 2026-11-16
- **Status:** Accepted

## Decision

The device controller is an ESP32-S3, programmed with PlatformIO and the Arduino
framework in C++17. The default target is `esp32-s3-devkitc-1`. The board stays
configurable because the two dev boards on the bench may be classic ESP32.

## Why

- Wi-Fi and BLE on one chip, which covers cloud sync and app pairing.
- Enough GPIO and the parallel output capability that the HUB75 DMA library uses.
- Native USB, I2S for the mic, I2C for the IMU, haptics driver, and light sensor.
- Mature Arduino libraries for everything on the parts list, and OTA with rollback.

## Alternatives

- **Classic ESP32:** works for Phases 1 and 2 and is supported as a build env, but
  has fewer usable pins and no native USB.
- **RP2040 / Pico W:** weaker Wi-Fi stack and OTA story, no BLE library parity.
- **ESP-IDF without Arduino:** more control, slower to prototype. Can be revisited.
- **Linux SBC:** too much power draw and boot time for a battery device.

## Consequences

- All pins go in `firmware/include/config.h`, one section per board, so switching
  boards is a build-env change.
- The partition table is sized for 4 MB flash so both board families work.
- HUB75 takes many pins on the S3; the pin budget must be checked in
  `docs/hardware/pinout.md` before each new peripheral.
