# 0007: SSD1306 OLED bench display with U8g2, on a 64x32 logical canvas

- **Date:** 2026-11-16
- **Status:** Proposed

## Decision

The bench display is now a 0.96 inch 128x64 monochrome I2C OLED (SSD1306), driven
by `Ssd1306Display` (`DISPLAY_DRIVER=ssd1306`) through `IDisplay`. **We use U8g2
rather than Adafruit SSD1306 because it exposes hardware flip, contrast and
power-save directly, and swapping to the common SH1106 clone is a one-line
constructor change.**

Art always draws on a 64x32 logical canvas (the final P2 HUB75 size). The OLED
driver thresholds colour to on/off and scales 2x to fill 128x64.

## Why

- The 8x8 WS2812B matrix assumed in Phase 1 is not what is on the bench.
- One logical resolution for every driver means art written now runs unchanged
  on the HUB75 panel in Phase 1b.
- Thresholding and scaling live in a hardware-free `MonoCanvas` so they are tested
  natively; the driver only copies its page buffer into U8g2 and sends it.

## Alternatives

- **Adafruit SSD1306 + GFX:** fine, but pulls in Adafruit GFX, has no SH1106
  support, and its rotation is software only.
- **Drawing art at 128x64:** rejected; it would have to be redrawn for the panel.
- **Thresholding in art code:** rejected; art stays colour and display-agnostic.

## Consequences

- `IDisplay` gains `logicalWidth()/logicalHeight()` (replacing `width()/height()`),
  `isColor()`, and `tick()` for driver housekeeping such as idle dimming.
- Idle dim after 30 s and panel off after 10 min (config.h) to limit burn-in.
- The LED brightness cap and FastLED current limiter now apply only to the
  `small_led` driver (env `esp32-s3-small-led`) and later HUB75; the OLED maps
  brightness straight to contrast.
- A missing OLED is logged and the firmware runs headless; it does not fail the
  OTA health check.
