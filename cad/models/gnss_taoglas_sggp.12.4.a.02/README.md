# Taoglas SGGP.12.4.A.02 GNSS patch, 12 x 12 x 4 (picked)

**Status:** from drawing, VERIFY ON ARRIVAL  
**Part number:** SGGP.12.4.A.02 (GPS/GLONASS/Galileo, passive, SMD, 12 x 12 x 4 mm)  
**Collected:** 2026-11-19

## Files

- STEP: `sggp.12.4.a.02_from_drawing.step`
- Datasheet: `SGGP.12.4.A.02_datasheet.pdf` (SPE-15-8-034-D; drawing p9)

## Source

- Datasheet: https://www.taoglas.com/datasheets/SGGP.12.4.A.02.pdf
- Product page (no STEP link found, 2026-11-19): https://taoglas.com/product/sggp-12-4-a-02-gpsglonass-smd-mount-patch-12mm-2

## Licence

Ours (made in this repo by `cad/models/from_drawing.py`). Datasheet PDF: copyright of its maker.

## Notes

- SMD part: it must be soldered to a ground-plane PCB (feed pad underneath). The assembly adds a 16 x 13 x 1.0 `gnss_board` behind it; a bigger ground plane performs better (see the datasheet's test board).
- Frame: X/Y centred, Z 0 = solder face, top electrode at Z 4.
