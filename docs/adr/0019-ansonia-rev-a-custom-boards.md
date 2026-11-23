# 0019: Ansonia rev A custom boards (carrier, power, front sensor, touch strip)

Status: Proposed (placement under review, not routed)
Date: 2026-11-23

## Context

The rev G shell (190 x 76 x 35.5, Dayton 70 x 30 speakers, 2 x USB-C) needs its own boards. The brief
fixed the main parts: ESP32-S3-WROOM-1U-N16R8, SIM7080G + nano-SIM, Ebyte EWM104-BT5125(I2S), DRV2605L,
TCA9554, 3.12 in SSD1322 panel with a 12 V boost, TAS5805M + TPS61088, two Amphenol 124019572112A ports,
and a power-bank / PD IC still to be chosen.

## Decision

- Four KiCad 10 projects under `Hardware/pcb/`, generated from Python (`Hardware/pcb/tools/`): the
  schematic, the netlist cross-check and the placement are reproducible. Same pattern as ADR 0010's
  scripted carrier, but with a real `.kicad_sch` (hierarchical, one sheet per block).
- Carrier 4-layer 1.0 mm, 90 x 47.5 (X -62..28, Y -17.5..30); power board 4-layer 1.6 mm 2 oz,
  43 x 49 with a lid-boss notch; front sensor 13.3 x 11.8; touch strip 40 x 5 with a 7 x 6.25 tab.
- Three TCA9554 at 0x20/0x21/0x22 (the I/O list needs 20 pins).
- TXB0104 for the SIM7080G 1.8 V UART; external U.FL for Bluetooth (the module has no antenna).
- Speaker R connects to the power board; speaker L goes through J1 to carrier J4.
- The PD IC is a DNP placeholder until chosen (options in `Hardware/pcb/README.md`).

## Consequences

- Carrier holes H3/H4 moved; the bracket frame must follow.
- PH2.0 cell connector (2 A) cannot carry full-power audio: firmware cap or heavy-lead pads.
- Footprints made or fixed by hand (USB-C from the drawing, Ebyte layer fix, SIM7080G trim) must be
  checked against the vendor drawings before fab.
