# JST SH 1.0 mm: SM0xB-SRSS-TB headers and SHR-0xV-S-B housings

**Status:** headers: KiCad library STEP; housings: from drawing, VERIFY ON ARRIVAL  
**Part number:** SM02B/SM04B/SM05B/SM06B/SM07B-SRSS-TB (side entry, as on the carrier) and SHR-02/04/05/06/07V-S-B  
**Collected:** 2026-11-19

## Files

- STEP (headers): `sm0Nb-srss-tb_kicad.step` (KiCad 10 library, the same models as in `cad/heartsync_carrier.step`)
- STEP (housings): `shr-0Nv-s-b_from_drawing.step`
- Datasheet: `jst_sh_series_eSH.pdf` (series catalogue; housing table p2, headers p3)

## Source

- Series page: https://www.jst-mfg.com/product/detail_e.php?series=231
- Catalogue: https://www.jst-mfg.com/product/pdf/eng/eSH.pdf
- Header STEPs: KiCad 10 `Connector_JST.3dshapes/JST_SH_SM0NB-SRSS-TB_1x0N-1MP_P1.00mm_Horizontal.step`

## Licence

Header STEPs: CC-BY-SA 4.0 with the KiCad libraries exception (designs that use the model are not Adapted Material). https://www.kicad.org/libraries/license/ Housing STEPs: ours. Catalogue PDF: copyright JST.

## Notes

- JST's own 3D files (one zip per part) need a form with company, address, phone and email, and their licence forbids copying them or showing them to third parties, so they are not here. The KiCad models are built from JST's drawings by the KiCad library team, not by JST.
- SHR frame: X across the circuits (centred), Y depth 0..2.8, Z 0 = mating face, wires leave at Z 5. Body A+2 wide (A = n-1), protrusions to A+4. The protrusion size (1.0 x 2.0 x 1.1) and the mating-face side are read off the drawing, not dimensioned: check on arrival.
- The housings are not placed in the assembly yet (they were never stand-ins). Each sticks out about 5 mm from its header plus the wire bend, so add them to the fit check, especially J4 and J5 at the board edges.
