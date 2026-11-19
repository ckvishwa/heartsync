# 0010: Project footprint library for the carrier board: ESP32-S3-WROOM-1_NoVias (pad 41 vias 0.3 mm)

- **Date:** 2026-11-19
- **Status:** Proposed

## Decision

The carrier board gets its own footprint library, `Hardware/heartsync_kicad/heartsync.pretty`,
which the project `fp-lib-table` loads as `heartsync` (`${KIPRJMOD}/heartsync.pretty`). Its first
footprint, `ESP32-S3-WROOM-1_NoVias`, is the stock KiCad 10 `RF_Module:ESP32-S3-WROOM-1` with the
twelve 0.2 mm thermal vias in pad 41 replaced by nine through-hole pads, also numbered 41: a 3x3
grid, 0.3 mm drill, 0.6 mm pad, 1.2 mm pitch, centred on the 3.9 mm exposed pad at (-1.5, 2.46).
U1 in `heartsync_carrier.py` uses `heartsync:ESP32-S3-WROOM-1_NoVias`.

## Why

- The stock footprint's 0.2 mm vias fail DRC (12 `drill_out_of_range` errors) against the
  JLCPCB 2-layer minimum drill of 0.3 mm. We must not lower the minimum-drill rule.
- KiCad 10's RF_Module library has no variant without thermal vias. `-1U` (U.FL antenna) and
  `-WROOM-2` are other modules, and they carry the same 0.2 mm vias.
- Putting the vias inside the footprint as pads numbered 41 means they travel with U1, take the
  GND net from the netlist, and survive any netlist re-import. Hand-placed board vias would not.

## Alternatives

- **Lower the minimum drill to 0.2 mm:** rejected. It is below the fab rule and costs more as a
  fab option.
- **Stock footprint, then hand-edit the pad drills on the board:** rejected. The edit is lost on
  the next "Update PCB from Netlist", so the layout stops being reproducible.
- **Footprint without vias, plus 0.3 mm vias placed by hand on the board:** workable, but the vias
  are not tied to U1. They do not move with it, and the netlist knows nothing about them.
- **Exclude the DRC errors:** rejected. The board would be ordered with holes the fab cannot drill.

## Consequences

- The project now carries a footprint copy. When KiCad updates its stock footprint, re-make ours
  from it: copy the stock file, remove the 0.2 mm pad-41 holes, add the 3x3 grid.
- Anyone opening the project needs `fp-lib-table` next to the `.kicad_pro`. It is committed with
  the board.
- Fewer vias (9 instead of 12, but larger) under the module's ground pad. Thermal and ground
  return paths are expected to be fine for the ESP32-S3 at our load. Check it on the bench
  (module temperature during Wi-Fi TX).
- The vias are untented on F.Cu (`F.Mask` opening, as in the stock footprint). Check for solder
  wicking during reflow; tent them from B.Cu if it shows up.
