# 0011: Controller module: ESP32-S3-WROOM-1U (U.FL, external antenna) instead of WROOM-1

- **Date:** 2026-11-19
- **Status:** Proposed

## Decision

U1 on the carrier board is the ESP32-S3-WROOM-1U-N16R8, not the WROOM-1-N16R8. It has the same
chip, memory and pinout, but a U.FL (IPEX MHF1) socket instead of the PCB antenna. The antenna is
an **Ezurio FlexPIFA 001-0014** on the inside of the front wall, connected by its 100 mm MHF1
cable (see "External antenna"). The footprint is
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

- **Antenna part: Ezurio FlexPIFA 001-0014** (chosen by the user 2026-11-19, see "Chosen
  antenna" below). It is a different type from Espressif's certified monopole, so extra EMC
  testing may be needed (section 10.2 note below).
- **Board layout:** U1's U.FL socket faces the board's top edge, with 3 mm of clearance around
  it. `replace_parts.py` checks this instead of snapping the antenna to the edge. There is no
  antenna keepout any more.
- **Handling:** U.FL sockets are rated for few mating cycles (about 30). Plug the cable once at
  assembly, and strain-relieve it against the shell.
- **3D model:** KiCad 10 ships none for the WROOM-1U. The project carries Espressif's STEP in
  `Hardware/heartsync_kicad/3dmodels/` (CC-BY-SA 4.0, attribution in its README), so U1's body
  is in the board STEP for the Fusion fit check.
- **The old footprint stays:** `ESP32-S3-WROOM-1_NoVias` stays in `heartsync.pretty` (ADR 0010)
  but is no longer used.
- **Firmware is unchanged:** same chip, same flash and PSRAM, same pins. The 1U has no on-board
  antenna, so the radio must never run without the external antenna attached.

## External antenna

Source: *ESP32-S3-WROOM-1 & WROOM-1U Datasheet* v1.8 (2026-03-02), section 10.2 "Dimensions of
External Antenna Connector", and section 7 (RF characteristics).

- **Connector:** first-generation external antenna connector, compatible with Hirose U.FL,
  I-PEX MHF I and Amphenol AMC.
- **Antenna used for certification:** one antenna only, a first-generation **monopole**,
  Espressif material code **TFPD05H08750011**, gain **2.33 dBi**. The datasheet gives no list of
  other tested antennas. Certificates: https://espressif.com/en/support/documents/certificates.
- **Recommended requirements:** 2.4 GHz band, 50 ohm impedance, maximum gain not above
  2.33 dBi, and a connector matching section 10.2. RF figures in section 7 are measured at the
  antenna port with 50 ohm external antennas.
- **Different type or gain:** "If you use an external antenna of a different type or gain,
  additional testing, such as EMC, may be required beyond the existing antenna test reports for
  Espressif modules. Specific requirements depend on the certification type." A flex antenna is
  a different type from the certified monopole, so **any flex antenna may need extra testing**,
  even with gain at or below 2.33 dBi. Gain at or below 2.33 dBi keeps that testing smallest.

Candidates (2.4 GHz flex, U.FL/MHF1, cable at most 100 mm). Gains are vendor free-space peak
figures, and the parts are not yet verified against current datasheets. Vendors note that a
real enclosure lowers peak gain by 1 to 2 dB.

| Part | Peak gain | Cable | Notes |
|---|---|---|---|
| Ezurio (Laird) 2.4 GHz FlexPIFA, 001-0014 | 2 dBi | 100 mm, MHF1 (confirm on the datasheet) | Only candidate at or below 2.33 dBi. A PIFA tolerates mounting near metal or on curved surfaces. Thicker than a plain flex (about 2.5 mm). |
| Taoglas FXP73.07.0100A (Blue Diamond) | 2.5 dBi | 100 mm, 1.13 mm coax, I-PEX MHF I | 47 x 7 x 0.1 mm. 0.17 dB above the certified gain. |
| Molex 146153-0100 | about 2.8 to 3.0 dBi (sources differ) | 100 mm, MHF | Above the certified gain. 50 mm version 146153-0050 also exists. |

### Chosen antenna: Ezurio FlexPIFA 001-0014

- **Part:** 40.1 x 11.0 x 2.5 mm, 2.4 GHz only, 2 dBi peak (at or below the certified
  2.33 dBi), 100 mm cable, MHF1 (U.FL compatible).
- **Mounting:** on the inside of the front wall, element facing out, ground plate toward the
  board, long sides at least 5 mm clear of metal in the wall plane. The factory adhesive is on
  the ground plate, which faces the board in this orientation, so the element side needs its own
  fixing (double-sided tape or a clip) to the wall. Route the cable away from the long side,
  never over the element.
- **Position** (`cad/fusion/heartsync_assembly.py`, model axes in mm): X 36..47, Y -19..21.1,
  Z 25.1..27.6, long axis along Y, over the Qi2 TX board. The top-edge strip next to U1 was
  tried first and rejected: its long side was 1.0 mm from the OLED glass.
- **Fit check clearances** (minimum distance, mm): GNSS patch 10.0 and speaker_R 10.9 (in the
  wall plane); LTE flex antenna 7.0 (end to end); button strip 5.9; carrier connector J5
  4.2, PD and Qi2 TX boards 5.6 (all behind the ground plate); cell 8.6; Qi2 ferrite 23.7.
  The cell is below the 10 mm first asked for; the front wall is the furthest point from it
  that the 11 mm antenna width allows.
- **Cable:** from U1's U.FL socket at (-13.0, 27.0) the route is about 55 mm, so about 45 mm
  of the 100 mm cable is slack. Dress the slack along the carrier, away from the antenna.
- **Open:** bench RF check in the closed shell (return loss, range) before the enclosure
  is final.
