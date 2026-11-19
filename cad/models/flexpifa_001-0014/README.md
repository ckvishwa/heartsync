# Ezurio (Laird) FlexPIFA 001-0014, 2.4 GHz

**Status:** from drawing, VERIFY ON ARRIVAL  
**Part number:** 001-0014 (2.4 GHz FlexPIFA, 100 mm MHF1/U.FL cable, right-hand)  
**Collected:** 2026-11-19

## Files

- STEP: `flexpifa_001-0014_from_drawing.step`
- Datasheet: `flexpifa_2.4ghz_datasheet.pdf` (Figure 1, p2)

## Source

- Product page: https://www.ezurio.com/part/001-0014
- Datasheet: https://www.ezurio.com/documentation/datasheet-24-ghz-flexpifa (PDF copy: https://www.farnell.com/datasheets/3968025.pdf)
- No STEP: Ezurio publishes STEP files only for the 868/915 MHz FlexPIFA (checked 2026-11-19).

## Licence

Ours (made in this repo by `cad/models/from_drawing.py`). Datasheet PDF: copyright of its maker.

## Notes

- It is not a solid 40.1 x 11 x 2.5 block. It is a 0.152 mm FPC, 40.12 x 11, with a 17 x 11 x 2.3 foam spacer under one end. That end folds over (41.25 overall) and is 2.5 thick; the other 23 mm is flat FPC.
- The cable is soldered at the folded short end and leaves along the 11 mm direction, within 2 mm of the end, not from a long side. The coax route in the assembly (`_coax_points()`) starts at that end.
- Frame: X along the length, adhesive (element) face on +Z at Z 2.5, foam at X 23.1..40.1, cable stub dia 1.13 along -Y at X 40.7, across the folded end and 1.0 mm past the edge (12 mm modelled; the assembly routes the rest with bends of R 7 or more, 2026-11-19).
- Check on arrival: foam length and position, fold shape, solder blob, cable exit point.
