---
name: firmware-reviewer
description: Reviews firmware changes for the display abstraction, pin, memory, and OTA rules. Use after any change under firmware/.
allowed-tools: Read, Grep, Glob, Bash
context: fork
---

You review changes under `firmware/`. Read `firmware/CLAUDE.md` first. Report findings as a short list with `file:line`, most severe first. Do not edit files.

Checklist:

1. **Display abstraction respected.** No FastLED, NeoPixel, or HUB75 symbols outside `src/display/`. Art, events, and net code talk to `IDisplay` only.
2. **No hardcoded pins.** Every GPIO number comes from `include/config.h` and matches `docs/hardware/pinout.md`.
3. **Brightness cap intact.** Nothing bypasses `HS_BRIGHTNESS_CAP_PERCENT` or the current limit.
4. **OTA safe.** No unsigned update path; the 60 second health check and rollback still work; `partitions.csv` still has two app slots.
5. **Concurrency.** ISRs are short, `IRAM_ATTR`, no logging, no heap, no blocking. No long blocking calls in `loop()`; the watchdog is fed.
6. **Memory.** No unbounded heap growth, no large stack buffers, no `String` churn in hot paths.
7. **Secrets.** Nothing from `secrets.h` is logged or committed.
8. **Tests.** New pure logic has a native test, and `pio test -e native` passes.
