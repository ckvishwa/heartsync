# 0011: Controller module: ESP32-S3-WROOM-1U (U.FL, external antenna) instead of WROOM-1

- **Date:** 2026-11-19
- **Status:** Proposed

## Decision

U1 on the carrier board is the ESP32-S3-WROOM-1U-N16R8, not the WROOM-1-N16R8. It has the same
chip, memory and pinout, but a U.FL (IPEX MHF1) socket instead of the PCB antenna. A 2.4 GHz flex
antenna sits on the shell wall away from metal, connected by a short U.FL cable. The footprint is
`heartsync:ESP32-S3-WROOM-1U_NoVias`: the stock KiCad 10 `RF_Module:ESP32-S3-WROOM-1U` with the same
pad-41 change as ADR 0010 (a 3x3 grid of 0.3 mm drill vias).

## Why

- In the assembled stack (`cad/fusion/heartsync_assembly.py`) the carrier board sits on the
  10,000 mAh cell. The WROOM-1's PCB antenna would be about 4 mm above the cell's metal-foil pouch,
  with the Qi2 ferrite and magnet ring nearby. Metal that close detunes the antenna and absorbs
  its signal. No board position avoids this, because the board can only go above the cell.
- With the 1U, the antenna can go where the RF environment is best: on the inside of the shell
  wall, away from the cell, the coil and the SIM7080G antennas. Only the cable changes if it moves.
- The PCB antenna needed a copper and parts keepout at the board's top edge. That cost board
  space and pinned U1 to one spot. The 1U body is shorter (18 x 19.2 mm against 18 x 25.5 mm) and
  needs no keepout, which freed room to put J4 (left speaker) on the left edge.

## Alternatives

- **Keep the WROOM-1 and move the board off the cell:** there is no room. The cell fills the shell
  from end to end under the board.
- **Keep the WROOM-1 and add a spacer or shield above the cell:** this adds thickness against the
  35 mm hard limit and still leaves the antenna inside a metal-lined pocket.
- **WROOM-2 or another module with a PCB antenna:** same problem as the WROOM-1.
- **A bare ESP32-S3 chip with our own RF design:** needs RF layout, tuning and certification
  work. Not worth it at this volume.

## Consequences

- **Antenna part:** 2.4 GHz flex antenna with a U.FL/IPEX MHF1 plug and a short cable (about
  50 to 100 mm). Pick one from Espressif's list of antennas tested with the WROOM-1U. The module's
  radio certification is tied to the antenna types it was tested with, so a different antenna
  may need its own testing. **The MPN is still to be chosen**, and the cable length set after the
  Fusion fit check.
- **Board layout:** U1's U.FL socket faces the board's top edge, with 3 mm of clearance around
  it. `replace_parts.py` checks this instead of snapping the antenna to the edge. There is no
  antenna keepout any more.
- **Handling:** U.FL sockets are rated for few mating cycles (about 30). Plug the cable once at
  assembly, and strain-relieve it against the shell.
- **The board STEP has no U1 body:** KiCad 10 ships no 3D model for the WROOM-1U. Add Espressif's
  STEP model to the project footprint before the module's 3.2 mm height counts in the Fusion fit
  check.
- **The old footprint stays:** `ESP32-S3-WROOM-1_NoVias` stays in `heartsync.pretty` (ADR 0010)
  but is no longer used.
- **Firmware is unchanged:** same chip, same flash and PSRAM, same pins. The 1U has no on-board
  antenna, so the radio must never run without the external antenna attached.
