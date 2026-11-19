# Same Sky CES-571423-28PMB enclosed speaker

**Status:** official STEP  
**Part number:** CES-571423-28PMB (57.5 x 23 x 14.85 mm box, 2 W, 8 ohm, wire leads with connector)  
**Collected:** 2026-11-19

## Files

- STEP: `ces-571423-28pmb.step` (STEP AP214, as supplied)
- STEP, ears cut: `ces-571423-28pmb_ears_cut.step`: the box only (X -0.08..57.48), ears and lead stub removed in Fusion (intersection with the box). Used by the assembly with a printed cradle
- Datasheet: `ces-571423-28pm_datasheet.pdf` (series datasheet dated 2025-03-19; the PMB is the variant with a connector)

## Source

- Product page: https://www.sameskydevices.com/product/audio/speakers/standard-(41-mm~205-mm)/ces-571423-28pmb
- STEP: https://www.sameskydevices.com/product/resource/3dmodel/ces-571423-28pmb (exported through 3dexchange.net)
- Datasheet: https://www.sameskydevices.com/product/resource/ces-571423-28pm.pdf

## Licence

Same Sky CAD Model Terms (https://www.sameskydevices.com/cad-model-terms): supplied as is, with no warranty; verify before use. The terms have no redistribution clause. Keep the repo private.

## Notes

- **The part is 82.5 mm long, not 57.5.** The 57.5 x 23 x 14.85 box has two mounting ears (dia 5.8 holes, 72.5 mm pitch, 12.2 high); see datasheet p2. The STEP spans X -12.55..69.95, plus the lead stub to X -23.9. The case is 68.1 mm wide inside, so the ears do not fit.
- No variant without ears: the series is CES-571423-28PM (wire leads), -28PMA and -28PMB (leads with a connector); all three have the two panel-mount flanges (checked 2026-11-19). The assembly uses the ears-cut model; the ears are cut off the real part (flush with the box) and a printed cradle with a foam pad holds it against the face gasket.
- The cone faces the STEP's **-Z** side (the flange face at Z 0.05 has the openings); the back (+Z) is a closed plain box. The leads leave the -X end at Z about 6.4.
- STEP frame: box X -0.05..57.45, Y 0..23, Z 0.05..14.9.
