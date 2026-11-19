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
- U1 = ESP32-S3-WROOM-1U-N16R8 (ADR 0011): U.FL socket, external flex antenna on the shell wall.
  No PCB antenna, so no antenna keepout. U.FL rule: the socket faces a board edge (now the top edge,
  centre at (23.0, 2.96) mm) with 3 mm free of other parts around it; `replace_parts.py` checks it.
- JST-SH connectors sit on board edges, cable entry facing out (except J6, J7: see Known DRC items).
  Rotation sets cable entry: 0 down, 90 right, 180 up, 270 left.
- Speakers: J4 (left) on the LEFT edge, J5 (right) on the right edge, so no speaker cable crosses
  the device.
- Project footprints live in `heartsync.pretty` (loaded by `fp-lib-table`, ADR 0010).
- Rails: +5V (USB / power bank), +3V3 (TLV62569 buck), VBAT (cell), VDD_EXT_1V8 (SIM7080G I/O).
  +5V tracks to amps and buck >= 0.5 mm.

## Fab rules (JLCPCB 2-layer)

- Min track / clearance 0.127 mm, default netclass 0.15 mm clearance, 0.2 mm track. Min drill 0.3 mm.
- These must match Board Setup. If you change one, change both and say so.

## Known DRC items (as of 2026-11-19)

- U1 drill errors are 0. U1 uses `heartsync:ESP32-S3-WROOM-1U_NoVias` (project lib `heartsync.pretty`,
  ADRs 0010 and 0011): stock footprint with nine 0.3 mm pad-41 vias instead of twelve 0.2 mm ones.
  Do not lower the min-drill rule. `ESP32-S3-WROOM-1_NoVias` stays in the library, unused.
- Placement errors (courtyard, keepout, hole) are 0, verified with DRC. After any PLACE edit,
  re-run DRC; an offline check is not proof.
- 3D models: every part has a body in the board STEP except test points and mounting holes.
  U1 uses Espressif's model from `3dmodels/` (see its README); U4, U5 (MAX98357A) and U8 (MAX17048)
  use KiCad's generic 3x3 TQFN-16 and 2x2 DFN-8 bodies. `replace_parts.py` sets all four.
- Starved thermals on GND pads (11): the pour is cut into islands until routing. Recheck after GND vias.
- J9 is on the top edge. Open item: J6 and J7 are off-edge (no room on any edge); J7's cable
  faces right.
- Keep "Footprint has no courtyard defined" as an error, not ignored, or overlaps go unseen.
- Silkscreen overlaps are warnings: fix last (move reference text), after placement is clean.

## Commands (Windows, KiCad 10)

kicad-cli: `C:\Program Files\KiCad\10.0\bin\kicad-cli.exe`

- DRC: `kicad-cli pcb drc --severity-all --all-track-errors -o DRC.rpt heartsync_carrier.kicad_pcb`
- Re-place headless (board CLOSED in KiCad): `"C:\Program Files\KiCad\10.0\bin\python.exe" replace_parts.py heartsync_carrier.kicad_pcb`.
  Saving headless adds a `heartsync_carrier.kicad_sch` entry to `top_level_sheets` in the `.kicad_pro`: revert it (there is no schematic).
- STEP for Fusion: `kicad-cli pcb export step -o ../../cad/heartsync_carrier.step heartsync_carrier.kicad_pcb`
- Gerbers / drill go to `fab_output/` (git-ignored until we decide).

## Rules for agents

- Commit before touching the `.kicad_pcb`. Close the board in KiCad before editing the file on disk,
  or use the KiCad API (IPC) while it is open: never both.
- Order: placement DRC clean -> route power -> I2S -> USB pair -> rest -> DRC clean -> STEP fit check.
- Report DRC as counts by type plus the top real errors. Do not exclude violations without the user's ok.
- Hardware choices (parts, connectors, rails) get an ADR in `docs/adr/`.
