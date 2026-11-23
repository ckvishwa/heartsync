# Ansonia rev A custom boards (rev G shell, 190 x 76 x 35.5)

Status (2026-11-23): **schematics done (ERC 0 errors / 0 warnings on all four), boards outlined and
placed, NOT routed.** Waiting for the placement review (`placement_review.png`) before routing.

## Layout of this folder

| Path | What |
|---|---|
| `carrier/`, `power/`, `front_sensor/`, `front_touch/` | One KiCad 10 project each (`.kicad_pro/.kicad_sch/.kicad_pcb`), ERC/DRC reports, `fab/` snapshots |
| `lib/ansonia.kicad_sym`, `lib/ansonia.pretty` | Project symbols and footprints (sources below) |
| `tools/` | Generators: the Python files ARE the source of the schematics and placement |
| `_vendor/` | Downloaded datasheets / vendor footprints (git-ignored, re-download from the links below) |

Regenerate (KiCad closed):

```
cd Hardware/pcb/tools
python build_sch.py                       # schematics + ERC + netlist cross-check (all boards)
"C:\Program Files\KiCad\10.0\bin\python.exe" lib_build_fp.py      # footprints (only if lib changed)
"C:\Program Files\KiCad\10.0\bin\python.exe" pcb_build.py carrier # board: outline, holes, placement
python snap.py carrier                    # placement PNGs + DRC (refills zones, schematic parity)
```

`designs.py` = circuits (values and their datasheet sources are in the sheet notes), `boards.py` =
outlines, holes, keep-outs, placement in **device mm** (origin = device centre, +X right end, +Y top
edge, seen from the front; KiCad origin (100, 100), Y flipped). Every board has F.Cu facing the front wall.
After routing starts, rebuild with `--keep-placement` (or stop regenerating the PCB and edit in KiCad).

## Boards

| Board | Outline (device mm) | Size | Stack | Notes |
|---|---|---|---|---|
| Carrier | X -62..+28, Y -17.5..+30 | 90 x 47.5 | 4L 1.0 mm (F sig / In1 GND / In2 PWR / B sig+GND) | grew left over the old SIM-board spot; all parts on the front side |
| Power | X 30..73 (Y > -1), X 30..66.5 (Y < -1), Y -16..+33 | 43 x 49 | 4L 1.6 mm, 2 oz outer | notch X <= 43.3, Y >= 27.65 for the top lid boss; USB-C cut-outs in the top edge |
| Front sensor | X -72.5..-59.2, Y 23.5..35.3 | 13.3 x 11.8 | 2L 0.8 mm | smallest that fits the JST SH 8 (vertical) + mic + APDS |
| Touch strip | X -56..-16, Y 27.25..32.25 + tab X -23..-16, Y 21..27.25 | 40 x 5 (+7 x 6.25 tab) | 2L 0.8 mm | 5 mm is too narrow for any JST SH: the tab carries a vertical SH-2 |

### What moved vs the fit map / brief

- **Carrier mounting holes:** H1 (-41, 21) -> (-41, 20.5); H2 (-41, 4) unchanged; **H3 (1.5, 16) -> (-9, 16)**
  (the SIM7080G sits there now); **H4 (4.5, -12) -> (9, -12.5)** (clears the e-paper FPC). The bracket frame must follow.
- **Carrier connectors:** J1 right edge (24.6, 12.5) 20-pin; J4 spk L left edge (-58.7, -7); J6 haptic bottom
  (-50, -14.2); J7 touch (-46.5, 26.6); J8 front sensor (-56, 26.6); J9 mute LED (-58.7, -13.5); J11 panel FPC
  (-25.5, -13.4); J12 buttons (-38.35, 26.6); J13 e-paper FPC (-4, -13.4, DNP); J14 nano-SIM (20.5, -9.5).
  **Dropped:** J2 (cell sense: the PD IC gauges the cell over I2C), J3 (SIM board is now on the carrier),
  J5 (speaker R plugs into the power board, J7 there, next to the amp), J10 (gesture shares J8 with the mic:
  one front board, one cable).
- **Lid screws (rev G):** the two M2 screws at (+37.5, +33.45) and (+45, -33.45) are outside every board;
  power board keeps >= 3 mm from the top boss via the notch; nothing near the bottom boss (board ends at Y -16).
- **USB-C ports:** centres X +52.75 / +66.05 as briefed, but the footprint puts the board edge 0.25 mm further
  out than Amphenol's drawing so the rear shell legs keep 0.3 mm copper-to-edge (Amphenol's layout has 0.05 mm).
  The port mating face therefore sits 0.25 mm further inside: check against the wall opening.

## Key circuit decisions (detail in the schematic sheet notes)

- **3 x TCA9554** (0x20 outputs, 0x21 buttons/status inputs, 0x22 Bluetooth control). The brief's expander list
  needs 20 I/O (6 outputs + 6 inputs + 4 BT PIOs + BT reset, SIM DTR, OLED VCC enable, mute LED); one TCA9554 has 8.
  Outputs that must be off at power-up have 10k pull-downs (TCA9554 inputs float high on 100k).
- **SIM7080G UART is 1.8 V** (VDD_EXT): TXB0104 between it and the ESP32 (TX, RX, STATUS, DTR). PWRKEY via MMBT3904.
- **Bluetooth antenna:** EWM104 pin 46 is a 50 ohm stamp hole and the module has **no antenna** (Ebyte manual 2.1).
  U.FL J17 + pi pads for a 2.4 GHz FPC antenna. Where that antenna goes is open.
- **ESP32 pin map:** checked against the WROOM-1U datasheet, no clash (IO35-37 unused, straps unused, IO19/20 USB).
  Spare: IO1, IO2 (test pads). USB D+/D- reach the ESP32 through J1 from USB-C port 1 for flashing.
- **12 V panel supply:** TPS61040 behind a P-FET switch so VCC floats when off (SSD1322 sec. 8.9).
- **Amp boost:** TPS61088 at 11.9 V, PWM mode, 600 kHz, values from the datasheet design equations (sheet note).
- **Battery path:** PH2.0 J4 -> 8 A fuse -> reverse-battery P-FET (DMP3013SFV) -> BAT_SW (5 V TVS). VSYS comes from
  the PD IC (placeholder); a DNP 0R bridges BAT_SW -> VSYS for bring-up without it.

## Verification status

| Item | Status |
|---|---|
| SIM7080G footprint | Accelerando footprint **checked against SIMCom's land pattern** (SIM7080G/Y7080E HD fig. 4): pitches, inner pads, centre GND pads match; edge pads trimmed 0.3 mm to SIMCom's outer extents; forbidden-area keepout added (position read off the drawing). Pin table from the brief, cross-checked with HD fig. 2. |
| EWM104-BT5125 footprint | **Ebyte's official KiCad file**, pads unchanged; fixed vendor export errors: pads were on B.Cu, outline on Edge.Cuts, duplicate thru-holes. Numbering matches the manual's top view. |
| USB-C 124019572112A footprint | **Built by me from Amphenol drawing C 12401957 sheet 2, read on screen** (CDN blocks downloads). Shell hooks drawn as straight slots (the drawing shows L shapes). **Verify before fab.** 3D model not attached (STEP origin offset unresolved). |
| TAS5805M PWP | KiCad footprint matches TI PWP0028M (3.4 x 9.7 pad, 3.1 x 4.05 mask); vias raised to 0.3 mm. |
| TPS61088 RHL | KiCad `Texas_VQFN-RHL-20`; the TPS61088 datasheet download was blocked, the **-Q1 datasheet (SLVSE52A)** was used for pins and values. Check the RHL land pattern against the TPS61088 drawing. |
| SSD1322 support parts | From the SSD1322 datasheet rev 1.2 fig. 14-1 and sec. 8.6 (IREF = 620k at 12 V). FPC pin 1 direction vs the folded panel tail: **not verified**. |
| E-paper FPC pinout | Generic SSD168x 24-pin assumption, DNP. Panel booster circuit not included. |
| EWM104 PIO1 reset polarity, PIO2-5 button polarity | **Not verified** (needs Ebyte firmware notes). |
| APDS-9960, ICS-43434, DRV2605L, TCA9554, TXB0104, TPS61040, TPS63001 | KiCad symbols/footprints; key values checked against the datasheets (sheet notes). |

## Open items

1. **PD / power-bank IC not chosen** (U1 on the power board is a DNP placeholder, QFN-40 land, 14 x 14 mm reserved).
   Candidates (verify each datasheet before choosing):
   - **Injoinic IP5356M**: 1-cell, one Type-C in/out + one Type-C out (customised), PD/QC, I2C, NTC. Closest to the brief.
   - **Injoinic IP5356 / IP5356H (I2C "_L" variant)**: 1-cell, QC/PD; dual Type-C only as a customised scheme.
   - **TI discrete**: BQ25792 (1-4 cell buck-boost charger, I2C, NTC, NVDC SYS) + TPS25750 (PD controller, I2C)
     for port 1, plus a 5 V boost and a Type-C source switch for port 2. Most parts, best documentation.
   (IP5389 has two bidirectional C ports but is a 2-5 cell part.) Note the Injoinic SoCs have no SYS rail:
   VSYS would then be BAT_SW directly.
2. **Battery connector current:** PH2.0 is rated 2 A; full-power stereo at 12 V PVDD can pull ~7 A from the cell.
   Cap amp power in firmware or use the BAT+/BAT- solder pads (TP1/TP2) with heavy leads. Needs a decision.
3. **ESP32-S3-WROOM-1U-N16R8 is rated 65 C ambient** (module datasheet table 1-2). Keep it away from the amp heat.
4. Bluetooth 2.4 GHz FPC antenna position; GNSS active-patch bias (LNA) not provided (pi pads only).
5. Back e-paper size (5.79 in B/W vs 3.5 in 4-colour) and its booster parts; how its FPC reaches the carrier past the cell.
6. Front sensor and touch strip have no mounting holes (no room): bosses/adhesive in the front wall.
7. The board-to-board cable J1 carries speaker L at up to ~1.5 A peak: 2 contacts per leg (JST SH 1 A each).
8. Silkscreen cleanup, fiducials, and JLCPCB stack-up/impedance (CPWG widths) are done at routing.

## Sources

SIM7080G/Y7080E Hardware Design (SIMCom), Accelerando `SIM7080G.kicad_mod`, Ebyte EWM104-BT5125 user manual
V1.0 + PCB package (cdebyte.com), SSD1322 datasheet rev 1.2 (Solomon Systech), TAS5805M SLASEH5D, TPS61088-Q1
SLVSE52A, TPS61040, TPS63001, DRV2605L, TCA9554, TXB0104 (TI), APDS-9960 (Broadcom), ESP32-S3-WROOM-1/1U
datasheet v1.8 (Espressif, in `cad/models/`), Amphenol drawing C 12401957.
