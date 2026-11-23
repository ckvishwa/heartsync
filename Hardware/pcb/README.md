# Ansonia rev A custom boards (rev G shell, 190 x 76 x 35.5)

Status (2026-11-23, after placement review 1): **schematics done (ERC 0 errors / 0 warnings on all four), boards
outlined and placed with the review changes, NOT routed yet.** Routing (RF + power by hand, then the rest) is next.
DRC now = unrouted + silkscreen + starved-thermal items only (no courtyard, edge, drill or hole errors).

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
| Power | X 30..73 (Y > -1), X 30..66.5 (Y < -1), Y -16..+33 | 43 x 49 | 4L 1.6 mm, 2 oz outer | plain outline (lid notch removed: the lid is clipped, no screws); USB-C cut-outs in the top edge |
| Front sensor | X -72.0..-60.4, Y 24.0..34.3 | 11.6 x 10.3 | 2L 0.8 mm | 8 solder pads (1.2 mm pitch, back side) replace the JST: smaller than before (13.3 x 11.8) |
| Touch strip | X -56..-16, Y 27.25..32.25 | 40 x 5 | 2L 0.8 mm | no tab: 2 solder pads on the back at the right end |

### What moved vs the fit map / brief

- **Carrier mounting holes:** H1 (-41, 21) -> (-41, 20.5); H2 (-41, 4) unchanged; **H3 (1.5, 16) -> (-9, 16)**
  (the SIM7080G sits there now); **H4 (4.5, -12) -> (9, -12.5)** (clears the e-paper FPC). The bracket frame must follow.
- **Carrier connectors:** J1 right edge (24.6, 12.5) 20-pin; J4 spk L left edge (-58.7, -7); J6 haptic bottom
  (-50, -14.2); J7 touch (-46.5, 26.6); J8 front sensor (-56, 26.6); J9 mute LED (-58.7, -13.5); J11 panel FPC
  (-25.5, -13.4); J12 buttons (-38.35, 26.6); J13 e-paper FPC (-4, -13.4, DNP); J14 nano-SIM (20.5, -9.5).
  **Dropped:** J2 (cell sense: the PD IC gauges the cell over I2C), J3 (SIM board is now on the carrier),
  J5 (speaker R plugs into the power board, J7 there, next to the amp), J10 (gesture shares J8 with the mic:
  one front board, one cable).
- **Lid (review 1):** no screws any more (gasket + 8 snap clips at Z 0..4 + a hook into each speaker box). The boss
  notch and keep-outs are deleted; the power board is a full rectangle again.
- **Review-1 changes:** J1 is now 22-pin (adds QI_EN, PWR_KEY; footprint `ansonia:JST_SH_SM22B...` made from KiCad's
  SM20B, **verify against the JST drawing**); J5 dropped (NTC on J4); IMU U12 added; J13 e-paper fitted with booster.
- **USB-C ports:** centres X +52.75 / +66.05 as briefed, but the footprint puts the board edge 0.25 mm further
  out than Amphenol's drawing so the rear shell legs keep 0.3 mm copper-to-edge (Amphenol's layout has 0.05 mm).
  The port mating face therefore sits 0.25 mm further inside: check against the wall opening.

### Connector rule (review 2)

Wires are soldered straight to the small remote boards/parts (front sensor, touch strip, buttons, haptic LRA, mute LED): no connector on
that end. The carrier keeps one JST SH per remote (J8 front sensor 8-pin, J7 touch 2-pin, J12 buttons 6-pin, J6 haptic 2-pin, J9 mute LED
2-pin) so it can come out. Kept as connectors: U.FL x 4 antennas, FPC for the OLED (J11) and e-paper (J13), carrier-to-power J1, speakers
(carrier J4, power J7). Wire pads: `ansonia:WirePads_1x08_P1.20mm` (1.0 x 2.0 mm) and `_1x02_P1.60mm`.
Battery: **Amass MR30PW-M** on the power board J4 (left edge, mating face flush with X 30) plus a 2-pin SH (J5) for the NTC. The MR30 is a
3-pole part (the spec sheet I found: 15 A, 3.5 mm pitch, 3 x d1.9 holes + 2 x d1.0 locating holes); BAT+ on pin 1, BAT- on pin 3, pin 2
open. The 2-pin Amass part is the XT30: say if you meant that. Footprint holes are from the Amass drawing, body outline and the
locating-hole row position (10 mm from the pins) are my reading of it: **verify before fab**. The BAT solder pads were removed.

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
- **Amp boost:** TPS61088 at **9.0 V** (499k / 76.8k), PWM mode, 600 kHz, values from the datasheet equations (sheet note). Amp limit 4 W/ch (see power budget).
- **Battery path:** MR30 J4 (BAT+ pin 1, BAT- pin 3) -> 8 A fuse -> reverse-battery P-FET (DMP3013SFV) -> BAT_SW (5 V TVS). Pack NTC on
  JST SH J5. VSYS comes from the PD IC (placeholder); a DNP 0R bridges BAT_SW -> VSYS for bring-up.
- **IMU (U12 LSM6DSOX, LGA-14):** I2C 0x6A (SA0 = GND, CS = VDDIO), INT1 -> ESP32 IO3 (RTC GPIO3, 100k pull-down so it is low at boot;
  IO3 is the JTAG-source strap, left at its default), INT2 -> TCA9554 0x21 P7. Placed at (-10, 8) mid-board, far from the speaker magnets.
  I2C map, no clash: 0x20/21/22 TCA9554, 0x2C TAS5805M, 0x39 APDS-9960, 0x5A DRV2605L, 0x6A LSM6DSOX; the power IC's address is TBD.
  Symbol is a modified KiCad LSM6DSL (identical LGA-14 pinout); pins 10/11 (OCS_Aux, SDO_Aux) are left open: confirm in the LSM6DSOX datasheet.
- **Qi TX:** separate 24 x 32 mm module on J6 (4-pin SH: 2 x QI_VIN 9 V, 2 x GND), P-FET (AO3401A) from PVDD switched by QI_EN
  (expander 0x22 P6 over J1, 10k pull-down). PVDD must be running first (firmware order: boost on, then Qi).
- **E-paper (J13 fitted):** Waveshare 3.97in raw panel (800 x 480, SSD1677, 24-pin 0.5 mm FPC). Pinout and booster (R1 2.2R sense,
  R2 1M, Q1 AO3400A, L1 10uH, D1-D3 MBR0530, C1-C10) taken from Waveshare's *3.97inch e-Paper User Manual v1.0*, sec. 5 and 9. **Caveat:**
  that manual is the two-colour panel; Waveshare's wiki and product page (the (G) red/yellow/black/white manual and the driver-board schematic)
  returned HTTP 403, so the (G) panel's pinout/booster are **not verified**. BS (pin 8) = GND (4-wire SPI).
  FPC route (plan, not checked against the cell position in the fit map): the 24-pin tail leaves the panel's bottom edge, runs along the
  rear wall under the carrier's bottom edge (the carrier ends at Y -17.5, J13 enters from -Y) and folds once into J13; the cell and
  power board are on the +X side, so the tail should not cross the cell. Measure the tail length and fold radius on the real panel.
- **Bluetooth antenna:** 2.4 GHz FPC antenna on the inside of the BOTTOM wall, X +38..+64, Z 15..28 (above the pogo pads and the magnets
  at X +32/+70), far from the Wi-Fi PIFA (X -52..-12) and the LTE flex (top wall). J17 stays at the module (X -50): the U.FL
  cable is ~110 mm (about 1 dB at 2.4 GHz for 1.13 mm coax, estimate). It is near the Qi ferrite: test RSSI on the bench.
- **Front sensor acoustics:** the ICS-43434 library footprint already carries the 0.5 mm sound-port NPTH; it lands on (-69.5, 31.25),
  the front-wall hole. A ring-gasket outline (OD 3.6, ID 1.6) is drawn on F.Fab around it: foam/silicone ring between the PCB and the wall,
  airtight. APDS-9960 package centre at (-64, 31.25); its optical-window offset inside the package is not checked.

## IP5568 evaluation (review item 2): rejected, IP5356M + separate Qi board stays

Read from the Injoinic IP5568 datasheet V1.31 (42 pages; mirror via flux.ai, not injoinic.com):
- **NTC:** yes, two (NTC1 pin 14 battery, NTC2 pin 30 coil), 20 uA bias, 100k B3950 + 120k (p. 23-24).
- **I2C:** **none.** The 65-pin list has no SDA/SCL; the interfaces are fast-charge, LED, key and digital tube (p. 1-2, pin table p. 5-7). Fails.
- **Ports:** 2 x USB-A (VOUT1/VOUT2), USB-B in, **one** Type-C DRP. A second Type-C would be VOUT2 re-wired with our own Rp:
  possible, but 5 V only when more than one output is on (p. 16).
- **Qi TX:** 5/7.5/10/15 W, WPC 1.2.4, integrated full bridge, but it **runs whenever the chip is on** (p. 25, no host enable), and 10/15 W only
  when VOUT1/VOUT2/VBUS are all off, 15 W only with 12 V on VIN (p. 16-17). The reference coil is a WPC A11 type with its own resonant
  capacitor; whether our 50 mm coil works needs the coil's L/R, which the datasheet does not give: not confirmed.
- **Verdict:** fails on I2C and host control of the Qi TX, and the coil is unconfirmed. Use **IP5356M + the separate Qi TX module**
  (the review's fallback). The charger IC on the power board is still the DNP placeholder (IP5356M datasheet to be re-read for pins,
  I2C address and NTC before the footprint is made).

## Power budget (review item 3)

- Amp: PVDD 9 V, **4 W per channel** (Dayton CE70-30P-8, 8 ohm, 5.66 Vrms): about 2 x 4 W / 0.85 = 9.5 W from PVDD, ~10.5 W from the cell.
- Qi TX 15 W at 9 V = 1.7 A from PVDD (~17 W from the cell). USB-C out up to 22.5 W + 5 V port 2.
- **Amp + Qi + USB-C out must not all run at maximum together**: the sum is about 50 W, ~13 A at 3.7 V, far above any 1S pack limit.
  Firmware must cap the sum (priority: amp > USB-C out > Qi; reduce Qi first).
- **Needs from you: the cell's PCM (protection board) continuous and peak discharge current limit.** The 8 A fuse and the pad/trace sizing
  assume at most ~8 A; if the PCM trips lower, the firmware cap must be lower.
- TAS5805M limit: configure AGL / digital volume ceiling for <= 5.66 Vrms before unmuting (firmware task, not written yet).

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
2. **Battery connector current:** resolved by the heavy BAT pads; open: the cell's PCM current limit (see power budget).
3. **ESP32-S3-WROOM-1U-N16R8 is rated 65 C ambient** (module datasheet table 1-2). Keep it away from the amp heat.
4. Bluetooth 2.4 GHz FPC antenna position; GNSS active-patch bias (LNA) not provided (pi pads only).
5. E-paper (G) panel pinout and booster unverified (see above).
6. Front sensor and touch strip have no mounting holes (no room): bosses/adhesive in the front wall.
7. The board-to-board cable J1 carries speaker L at up to ~1.5 A peak: 2 contacts per leg (JST SH 1 A each).
8. Silkscreen cleanup, fiducials, and JLCPCB stack-up/impedance (CPWG widths) are done at routing.

## Sources

SIM7080G/Y7080E Hardware Design (SIMCom), Accelerando `SIM7080G.kicad_mod`, Ebyte EWM104-BT5125 user manual
V1.0 + PCB package (cdebyte.com), SSD1322 datasheet rev 1.2 (Solomon Systech), TAS5805M SLASEH5D, TPS61088-Q1
SLVSE52A, TPS61040, TPS63001, DRV2605L, TCA9554, TXB0104 (TI), APDS-9960 (Broadcom), ESP32-S3-WROOM-1/1U
datasheet v1.8 (Espressif, in `cad/models/`), Amphenol drawing C 12401957.

## Still unverified (flagged, review item 10)

- USB-C 124019572112A footprint (built from the drawing read on screen).
- TPS61088 values and footprint (taken from the -Q1 datasheet SLVSE52A).
- EWM104 PIO1 reset / PIO2-5 button polarity.
- Panel (SSD1322) FPC pin 1 after the fold; e-paper (G) pinout and booster (two-colour manual used).
- JST SH 22-pin footprint (extended from SM20B), cell connector pin order, LSM6DSOX pins 10/11, APDS-9960 window offset.
