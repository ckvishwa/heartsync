# Same Sky CES-571423-28PMB enclosed speaker

**Status:** official STEP  
**Part number:** CES-571423-28PMB (57.5 x 23 x 14.85 mm box, 2 W, 8 ohm, wire leads with connector)  
**Collected:** 2026-11-19

## Files

- STEP: `ces-571423-28pmb.step` (STEP AP214)
- Datasheet: `ces-571423-28pm_datasheet.pdf` (series datasheet dated 2025-03-19; the PMB is the variant with a connector)

## Source

- Product page: https://www.sameskydevices.com/product/audio/speakers/standard-(41-mm~205-mm)/ces-571423-28pmb
- STEP: https://www.sameskydevices.com/product/resource/3dmodel/ces-571423-28pmb (exported through 3dexchange.net)
- Datasheet: https://www.sameskydevices.com/product/resource/ces-571423-28pm.pdf

## Licence

Same Sky CAD Model Terms (https://www.sameskydevices.com/cad-model-terms): supplied as is, with no warranty; verify before use. The terms have no redistribution clause. Keep the repo private.

## Notes

- **The part is 82.5 mm long, not 57.5.** The 57.5 x 23 x 14.85 box has two mounting ears (dia 5.8 holes, 72.5 mm pitch, 12.2 high); see datasheet p2. The STEP spans X -12.55..69.95, plus the lead stub to X -23.9. The case is about 68 mm wide inside, so the ears do not fit as drawn: cut them off or change the mounting. (`speaker_length` 57.5 in `params.csv` is the box only.)
- The cone is on the 57.5 x 23 face (the STEP's +Z side), so the speaker fires along its 14.85 depth.
- STEP frame: box X -0.05..57.45, Y 0..23, Z 0.05..14.9.
