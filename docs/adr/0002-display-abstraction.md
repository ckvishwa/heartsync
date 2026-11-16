# 0002: All drawing goes through a display abstraction

- **Date:** 2026-11-16
- **Status:** Accepted

## Decision

All drawing goes through the `IDisplay` interface (`firmware/src/display/IDisplay.h`).
Drivers implement it: `SmallLedDisplay` now, `Hub75Display` later. The driver is
chosen at compile time by the `DISPLAY_DRIVER` build flag (`small_led` or `hub75`)
in `DisplayFactory.cpp`. No code outside `src/display/` may include or call an LED
library.

For the small LEDs we use **FastLED** rather than Adafruit NeoPixel.

## Why

- The real 64x32 P2 HUB75 panel is not here yet. Work must start on small LEDs and
  move to the panel without rewriting art, animation, or event code.
- An interface with `width()`, `height()`, `setPixel()`, `clear()`, `show()`, and
  `setBrightness()` is the smallest surface both hardware types share.
- The interface has no hardware dependencies, so art and event logic can be tested
  natively against a fake display.
- FastLED over NeoPixel: it has a built-in global brightness and a current limiter
  (`setMaxPowerInVoltsAndMilliamps`), which implements the brightness cap rule
  directly, and it supports more chipsets if the small LEDs turn out not to be WS2812B.

## Alternatives

- **Adafruit GFX as the abstraction:** both LED families have GFX-based libraries,
  but it ties art code to one library's types and is harder to fake in native tests.
- **Runtime driver selection:** unnecessary; a device has one display, and compile-time
  selection keeps the unused driver out of the binary.
- **`#ifdef` in drawing code:** spreads hardware knowledge everywhere. Rejected.

## Consequences

- Sprites must be resolution-aware: an 8x8 heart on the small LED, larger art on
  the panel. `Animator` centres whatever it is given and clips at the edges.
- Per-pixel virtual calls are fine at these sizes (2048 pixels at most).
- Brightness capping lives in the drivers, behind `setBrightness()`.
- Adding a driver: implement `IDisplay`, add a `DISPLAY_DRIVER` value in
  `DisplayFactory.cpp`, add a PlatformIO env. See `firmware/CLAUDE.md`.
