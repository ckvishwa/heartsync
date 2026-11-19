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
- Sealing (IP54): the pad holes go through the wall. Press-seal, pot or O-ring each pad; nothing in the model seals them yet.
- Safety: the pads must stay dead until the device is seated in the dock (the PD charger can feed power back), and current-limited.
- Frame: axis Z, contact face at Z 0 with a 0.2 chamfer, inside end at Z 2.2.
