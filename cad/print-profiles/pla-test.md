# PLA: test prints

For fit checks only. Never for the final build (PLA softens with heat from the
sun, the panel, or the charging coil).

Starting point. Check the filament maker's recommended range, then record what worked.

| Setting | Starting value | What worked |
|---------|----------------|-------------|
| Nozzle temperature | maker's range (commonly around 200 to 215 °C) | |
| Bed temperature | maker's range (commonly around 55 to 60 °C) | |
| Layer height | 0.2 mm | |
| Walls | 3 | |
| Infill | 15 percent | |
| Supports | only where needed | |

Notes:

- Print fit-test slices (a corner, the panel seat, the battery pocket) before a full shell.
- Measure the test print and adjust `fit_clearance` in `params.csv`.
