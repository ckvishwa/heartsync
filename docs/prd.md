# Product requirements: heartsync

> **TODO:** the full PRD lives in Claude Docs. Paste it below the summary, replacing
> this note. Until then, this summary is the source of truth for the repo.

## Summary

A gift: **two matching, cloud-synced pixel-art devices** for a couple. Each device
shows pixel art and two small pixel avatars, and the two stay in sync through the
cloud, so a heart, a touch, or a drawing sent from one appears on the other.

### The device

- Horizontal, fabric-wrapped, 3D-printed box, about 16 x 7.5 x 3.2 cm. **Hard limit: 3.5 cm thick.**
- The whole front is a 64x32 P2 HUB75 RGB LED panel.
- Inside: ESP32-S3, 10,000 mAh single LiPo with protection board, two-way USB-C PD
  power bank chip, wireless charging coil on the back, stereo speakers with a
  separate Bluetooth audio module, IMU, light sensor, touch strip, LRA haptics with
  DRV2605L, I2S mic, LTE-M/GNSS module, 500 mAh backup cell.
- A dock with four magnets and pogo pins.
- Build target: IP54 (designed for, not certified).

### The system

- Two devices pair as one "couple" through Firebase.
- A Flutter app (iOS and Android) and a small web dashboard control them.
- Both people use an iPhone and an Android phone, so accounts are per person, not per phone.
- Firmware updates arrive over the air, signed, with rollback.

### What exists today

2 ESP32 dev boards and 2 small LED displays. The real P2 panel is not here yet.
Everything must run on the small LEDs first and move to the HUB75 panel later
without rewrites. All drawing goes behind a display abstraction.

### Current goal

Phases 1 and 2 of 11: each board shows pixel art on its small LED, and a heart
sent from one board appears on the other through Firebase. See [phases.md](phases.md).

### Privacy

Cycle data is health data. Sharing with the partner is on by default (the couple
agreed), with an on/off toggle that she controls. See [protocol.md](protocol.md).

---

## Full PRD

_Paste the full PRD from Claude Docs here._
