# Pogo target pad (device side, our own part)

**Status:** from params (no bought part)  
**Part number:** none chosen: dia 2.5 x 2.2 brass, gold plated, through the bottom-edge wall  
**Collected:** 2026-11-19

## Files

- STEP: `pogo_pad_from_params.step`
- Datasheet: none: our part; dimensions come from `pogo_pad_d` and `wall_thickness` (2.2) in `params.csv`

## Source

- `cad/params.csv`

## Licence

Ours (made in this repo by `cad/models/from_drawing.py`). Datasheet PDF: copyright of its maker.

## Notes

- Not a purchased part yet. If you want a bought target (Mill-Max target contacts, or gold PCB pads on a small flex), choose one and replace this model.
- Sealing (IP54): each pad seals on a silicone washer (OD 4.0, ID 2.5, 0.5) on the wall's inner face; the pad's 0.4 flange compresses it, and the pads' solder tails sit in a small pogo board screwed to two bottom-wall bosses (2026-11-19).
- Safety: the pads must stay dead until the device is seated in the dock (the PD charger can feed power back), and current-limited.
- Frame: axis Z, contact face at Z 0 with a 0.2 chamfer, wall inner face at Z 2.2, flange Z 2.7..3.1 (dia 4.0), solder tail to Z 4.6 (dia 1.0).
