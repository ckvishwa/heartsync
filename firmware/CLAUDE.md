# firmware

ESP32 firmware. PlatformIO, Arduino framework, C++17. PlatformIO is in the repo `.venv`.

## Commands (run in `firmware/`)

- `pio run`: build the default env (`esp32-s3-devkitc-1`, SSD1306 OLED).
- `pio run -e esp32dev`: classic ESP32 with OLED. `pio run -e esp32-s3-small-led`: old
  WS2812B matrix. `pio run -e esp32-s3-hub75`: HUB75 stub build.
- `pio run -t upload && pio device monitor`: flash and watch serial (115200).
- `pio test -e native`: host unit tests, no hardware.

## Conventions

- Draw only through `IDisplay`. Display library calls stay inside `src/display/`.
- Art draws on the 64x32 logical canvas (`logicalWidth()/logicalHeight()`), never at
  the OLED's 128x64. Mono thresholding happens in the driver, not in art.
- Pins and hardware constants only in `include/config.h`, mirrored in `docs/hardware/pinout.md`.
- `art/` and `events/` are hardware-free (no `Arduino.h`) and compiled by the `native` env.
  New pure logic goes in a hardware-free module with a test under `test/test_<name>/`.
- Log with `LOGI/LOGW/LOGE(tag, fmt, ...)` from `util/Log.h`.
  Format: `[  millis][L][tag] message`. Never log secrets or cycle data.
- Stubs carry a header comment naming the phase that fills them in.

## Adding a display driver

1. Implement `IDisplay` in `src/display/<Name>Display.{h,cpp}`; LED drivers clamp brightness to `HS_BRIGHTNESS_CAP_PERCENT`.
2. Add `HS_DISPLAY_ID_<name>` in `config.h` and a branch in `DisplayFactory.cpp`.
3. Add an env in `platformio.ini` with `-DDISPLAY_DRIVER=<name>` and its `lib_deps`.
4. Guard the `.cpp` with `#if HS_DISPLAY_IS_<NAME>` so other builds skip it.

## Gotchas

- **ISRs:** short, `IRAM_ATTR`, no logging, no heap, no I2C/SPI. Set a flag, handle it in `loop()`.
- **Watchdog:** never block `loop()` for long; no `while (!connected)` waits. Wi-Fi is non-blocking.
- **Memory:** app slot is 1.75 MB (4 MB flash). Avoid `String` churn and large stack buffers; FastLED's `show()` briefly disables interrupts.
- **OTA:** `ota::reportHealthy()` must run within 60 s of boot or the device rolls back. Never add an update path without signature verification.
- **Secrets:** `include/secrets.h` is git-ignored and off-limits to agents. Without it the build uses `secrets.example.h` and warns.
- **Serial on S3 DevKitC:** logs go to the port labelled UART, not the native USB port.
- LED brightness is capped at 25 percent and current at 400 mA until Phase 8 (LED drivers;
  the OLED maps brightness to contrast). USB power only.
