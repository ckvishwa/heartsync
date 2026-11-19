# Hardware/heartsync_kicad: carrier board v0.1

Read `README.md` in this folder first (parts, connectors, ladder values).
Pins must match `docs/hardware/pinout.md` and `firmware/include/config.h`.

## Source of truth

- `heartsync_carrier.py` (SKiDL) IS the schematic. There is no `.kicad_sch` to edit.
  Change the circuit there, run `python heartsync_carrier.py`, re-import `heartsync_carrier.net`.
  Never hand-edit the `.net` or the BOM CSV.
- `heartsync_carrier.kicad_pcb` is the board. Placement lives in `replace_parts.py` (PLACE table).
  Change positions in the script, not by dragging, so the layout stays reproducible.
- Fresh netlist import: run `place_board.py` THEN `replace_parts.py`, then save.
- `place_board.py` runs ONCE per netlist import (outline, holes, pours). `replace_parts.py` is safe to re-run.
  Both run inside KiCad's PCB editor scripting console (pcbnew), not from the shell.

## Board facts

- 70 x 45 mm, 2-layer, GND pour on F.Cu and B.Cu, four M2 holes (H1-H4), origin at (100, 100) mm.
- U1 = ESP32-S3-WROOM-1-N16R8, antenna flush with the TOP edge. Nothing (copper, parts, connectors)
  inside its antenna keepout.
- All 12 JST-SH connectors sit on board edges, cable entry facing out.
- Rails: +5V (USB / power bank), +3V3 (TLV62569 buck), VBAT (cell), VDD_EXT_1V8 (SIM7080G I/O).
  +5V tracks to amps and buck >= 0.5 mm.

## Fab rules (JLCPCB 2-layer)

- Min track / clearance 0.127 mm, default netclass 0.15 mm clearance, 0.2 mm track. Min drill 0.3 mm.
- These must match Board Setup. If you change one, change both and say so.

## Known DRC items (as of 2026-11-19)

- U1 pad 41 thermal vias are 0.2 mm drill (below 0.3 mm min). Fix: footprint variant without
  thermal vias, then add 0.3 mm vias by hand. Do not lower the min-drill rule.
- Placement still has courtyard overlaps (incl. H1 inside the U1 antenna keepout). Fix in `replace_parts.py`
  and verify with DRC; an offline check is not proof.
- Keep "Footprint has no courtyard defined" as an error, not ignored, or overlaps go unseen.
- Silkscreen overlaps are warnings: fix last (move reference text), after placement is clean.

## Commands (Windows, KiCad 10)

kicad-cli: `C:\Program Files\KiCad\10.0\bin\kicad-cli.exe`

- DRC: `kicad-cli pcb drc --severity-all --all-track-errors -o DRC.rpt heartsync_carrier.kicad_pcb`
- STEP for Fusion: `kicad-cli pcb export step -o ../../cad/heartsync_carrier.step heartsync_carrier.kicad_pcb`
- Gerbers / drill go to `fab_output/` (git-ignored until we decide).

## Rules for agents

- Commit before touching the `.kicad_pcb`. Close the board in KiCad before editing the file on disk,
  or use the KiCad API (IPC) while it is open: never both.
- Order: placement DRC clean -> route power -> I2S -> USB pair -> rest -> DRC clean -> STEP fit check.
- Report DRC as counts by type plus the top real errors. Do not exclude violations without the user's ok.
- Hardware choices (parts, connectors, rails) get an ADR in `docs/adr/`.
