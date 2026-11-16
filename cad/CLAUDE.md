# cad

Enclosure and dock. Fusion 360, driven by `params.csv`. Enclosure work is Phase 10;
until then this folder only holds parameters and notes.

## Source of truth

- **`params.csv` is the source of truth for every dimension.** Change a value
  there, then run `fusion/import_params.py` inside Fusion 360 to update the model's
  user parameters. Never type a dimension straight into a sketch.
- Rows with value `0` and status `verify against datasheet` are unknown. Do not
  guess them: measure the part or read its datasheet.
- **Never hand-edit files in `exports/`.** They are generated from Fusion
  (STL/3MF) and git-ignored. Only release exports are committed, with `git add -f`.

## Hard limits

- **Thickness: 3.5 cm maximum** (`body_thickness_max`). Check the full stack-up
  (fabric, wall, panel, PCB, battery, swelling gap, wall, coil, fabric) before any
  change that adds depth.
- **Battery swelling gap: 0.5 to 1 mm** (`battery_swell_gap`). Nothing sharp
  faces the cell. See `docs/hardware/safety.md`.
- The case must open **without heat**: screws or clips, no glue near the cell.

## Materials (`print-profiles/`)

- PLA: fit tests only. It softens in a warm car or near a charging coil.
- PETG: final enclosure and dock.
- TPU: bumpers and feet.
- Profiles are starting points; record what actually worked for the printer used.

## Gasket and IP54 notes

- IP54 is a design target, not a certification.
- Seam gasket channel: `gasket_width`, `gasket_compression`. Keep the channel continuous.
- Mesh over speaker and mic openings; a plug or sealed connector for USB-C.
- Pogo pins and magnets must not break the seal: seat them in blind pockets.
- Do not seal the battery cavity airtight without considering venting.

## Commands

No build step. Validate the CSV by importing it in Fusion; the script reports bad rows.
