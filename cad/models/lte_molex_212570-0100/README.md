# Molex 212570-0100 side-fed cellular flex antenna (picked, see the band warning)

**Status:** official STEP (TraceParts, via molex.com)  
**Part number:** 212570-0100 (824-960 / 1710-2170 MHz, 40.4 x 15.4 x 0.1 flex, 100 mm 1.13 cable, U.FL)  
**Collected:** 2026-11-19

## Files

- STEP: `212570-0100.step` (as supplied) and `212570-0100_cable_cut.step` (flex + 6.6 mm of cable, used by the assembly)
- Drawing: `2125700100_sales_drawing.pdf`

## Source

- Product page: https://www.molex.com/en-us/products/part-detail/2125700100

## Licence

Molex/TraceParts download terms; no licence text ships with the file. Keep the repo private.

## Notes

- **Band gap:** 824-960 and 1710-2170 MHz only. It misses the 700 MHz LTE-M/NB-IoT bands (B12, B13, B28, B85) that the SIM7080G uses in many networks. Check the carrier's bands before ordering.
- Fits the TOP wall: placed at X -28.2..12.2, Z 11.9..27.3, adhesive on the wall (fit check: no clash).
- Frame: flex in the XZ plane, X 0..40.4, Z -15.2..0.2, adhesive on -Y, solder joint up to Y 1.4; the cable leaves the +X end at Z -6.0.
- Price 2026-11-19: $1.3 to $3.2 (Mouser, Arrow, DigiKey).
