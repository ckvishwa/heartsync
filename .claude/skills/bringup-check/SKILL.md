---
description: Walk the hardware bring-up checklist one part at a time
argument-hint: [part name, optional]
---

Walk me through `docs/hardware/bringup-checklist.md`.

1. Read the checklist and `docs/hardware/pinout.md`.
2. If "$ARGUMENTS" names a part, start there. Otherwise start at the first unchecked item.
3. Take **one part at a time**. For each: state what to wire (pins from `firmware/include/config.h`), what to flash or run, and what I should see. Then stop and wait for my result.
4. On pass, tick the checkbox in the checklist. On fail, help me debug before moving on.
5. Before any step that involves a battery, read `docs/hardware/safety.md` and refuse to continue if we are before Phase 8.
