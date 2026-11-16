# Fusion 360 scripts and notes

## import_params.py

Loads `cad/params.csv` into the active design's **user parameters**, creating or
updating one parameter per row. Sketches and features should reference these
parameters by name, so the whole model follows the CSV.

To run it: Fusion 360, Utilities, Add-Ins, Scripts and Add-Ins, the green plus next to
"My Scripts", choose this `fusion` folder, then Run `import_params`.

Rows with value `0` are skipped and listed at the end (they are unknown values
that still need a datasheet).

**Status:** written against the Fusion 360 Python API but not yet run in Fusion
(no design exists yet). Test it on an empty design first.

## Model notes

- No model yet. Enclosure and dock are Phase 10.
- Name bodies by part and material, for example `shell_front_petg`, `bumper_tpu`.
- Export STL/3MF to `cad/exports/`. Never edit exports by hand.
