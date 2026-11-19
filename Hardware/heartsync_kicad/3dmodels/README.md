# 3D models for project footprints

| File | Used by | Source |
|---|---|---|
| `ESP32-S3-WROOM-1U.step` | `heartsync:ESP32-S3-WROOM-1U_NoVias` (U1) | Espressif `kicad-libraries`, `3dmodels/espressif.3dshapes/ESP32-S3-WROOM-1U.STEP`, commit `d5b68fd9269c` (2026-11-16) |

Licence: CC-BY-SA 4.0 with the KiCad library exception (designs made with the models are not
"Adapted Material"). Copyright Espressif Systems. See
https://github.com/espressif/kicad-libraries/blob/main/LICENSE.md.

Footprints reference these files as `${KIPRJMOD}/3dmodels/<file>`. The Espressif footprint's
origin is 0.15 mm lower than KiCad's stock `RF_Module:ESP32-S3-WROOM-1U`, so our offset is
(-9, -9.6, 0) instead of Espressif's (-9, -9.75, 0).
