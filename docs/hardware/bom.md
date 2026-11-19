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
| LiPo cell, 3.7 V, 10,000 mAh, with protection board | 2 | to order | Picked: LiPol LP1160100 (100 +-1 x 60 +-0.5 x 11 +-0.3, PCM). Order with a 10 k NTC and a JST lead (datasheet version has no NTC). ADR 0013, `cad/models/cell_lipol_lp1160100`. |
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
| LTE-M/GNSS module | 2 | to order | SIM7080G; plan: LCC on carrier rev B (`docs/hardware/board-plans.md`). SIM: MFF2 eSIM (1.8 V) or nano-SIM. |
| LTE flex antenna | 2 | to order | Picked: Molex 212570-0100 (40.4 x 15.4, U.FL). No 700 MHz bands: see `cad/models/open_parts.md`. |
| GNSS patch | 2 | to order | Picked: Taoglas SGGP.12.4.A.02 (12 x 12 x 4 SMD) on a small ground-plane board. |
| OLED module 2.7 in 128 x 64 | 2 | to order | Picked: Newhaven NHD-2.7-12864WDW3. |
| Waterproof USB-C receptacle | 2 | to order | Amphenol 124019572112A (mid-mount). |
| Lid screws, M2 low-head (head <= 3.8 x 1.3), + M2 heat-set inserts | 8 + 8 | to order | Under the TPU back ring. Length: lid 3.0 + insert 3. |
| Back ring (TPU), speaker cradles (PETG) | 2 + 4 | print | STLs from `export_all()`. |
| Dock: magnets | 8 | to order | Four per dock. Size and grade: verify. |
| Dock: pogo pins and pads | 2 sets | to order | Current rating: verify against datasheet. |
| Filament: PLA (test), PETG (final), TPU (bumpers) | - | to order | See `cad/print-profiles/`. |
| Fabric wrap, gaskets, speaker mesh | - | to order | For IP54 intent. |
