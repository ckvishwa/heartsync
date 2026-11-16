# Bill of materials

Status is one of: **have**, **ordered**, **to order**. Quantities are for two devices.
No part numbers or prices are recorded until they are checked: where a value is
not confirmed it says "verify against datasheet".

| Part | Qty | Status | Notes |
|------|-----|--------|-------|
| ESP32 dev board | 2 | have | Exact model unconfirmed (S3 DevKitC-1 or classic ESP32). Record it in `pinout.md`. |
| Small LED display | 2 | have | Assumed 8x8 WS2812B matrix. Confirm type, size, colour order. |
| USB cable and 5 V supply | 2 | have | Bench power for Phases 1 to 7. |
| 64x32 P2 HUB75 RGB LED panel | 2 | to order | 128 x 64 mm active area expected; verify against datasheet. |
| ESP32-S3 module for final board | 2 | to order | Flash and PSRAM size: verify against datasheet. |
| LiPo cell, 3.7 V, 10,000 mAh, with protection board | 2 | to order | Dimensions drive the enclosure; verify against datasheet. JST connector. |
| Two-way USB-C PD power bank chip / module | 2 | to order | Part not chosen; verify against datasheet. |
| Wireless charging receiver coil and module | 2 | to order | Verify against datasheet. |
| Backup cell, 500 mAh | 2 | to order | Verify against datasheet. |
| Speakers (stereo pair) | 4 | to order | Size and impedance: verify against datasheet. |
| Bluetooth audio module | 2 | to order | Part not chosen. |
| IMU | 2 | to order | Part not chosen. |
| Ambient light sensor | 2 | to order | Part not chosen. |
| Capacitive touch strip | 2 | to order | May use ESP32-S3 touch pins. |
| LRA haptic actuator | 2 | to order | Verify against datasheet. |
| DRV2605L haptic driver | 2 | to order | I2C. |
| I2S MEMS microphone | 2 | to order | Part not chosen. |
| LTE-M/GNSS module | 2 | to order | Part, antenna, and SIM: verify against datasheet. |
| Dock: magnets | 8 | to order | Four per dock. Size and grade: verify. |
| Dock: pogo pins and pads | 2 sets | to order | Current rating: verify against datasheet. |
| Filament: PLA (test), PETG (final), TPU (bumpers) | - | to order | See `cad/print-profiles/`. |
| Fabric wrap, gaskets, speaker mesh | - | to order | For IP54 intent. |
