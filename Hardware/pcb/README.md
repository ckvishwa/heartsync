# Ansonia rev A custom boards (rev G shell, 190 x 76 x 35.5)

Status (2026-11-23, after review 3): **schematics done (ERC 0 errors / 0 warnings on all four), placement done, routing INCOMPLETE:**
only the touch strip is routed; the carrier has its RF lines only; the power board and most of the carrier are not routed. See "Routing status".
DRC/ERC reports are in each board folder (`<board>_DRC.rpt`, `<board>_ERC.rpt`).

## Routing status (honest summary)

| Board | State |
|---|---|
| front_touch | **routed**, GND stitched; DRC: only `copper_sliver` from the hatched pour. Gerbers/BOM/CPL in `fab/` (still unverified by a fab DFM check). |
| front_sensor | routed with GND in the autorouter; **6 connections still open** (GND pads/zone islands, `front_sensor_DRC.rpt`). Gerbers withheld. |
| carrier | **only the three RF lines are routed** (hand-routed, DRC clean: no shorts/clearance; `tools/handroute.py`). The other 262 connections are **unrouted**. Freerouting 2.1.0 stalls at 110 unrouted (168 with the 0.5 mm power widths) and never ends, so no result could be imported. Gerbers withheld. |
| power | placement + In2 BAT_SW plane only: **unrouted** (210 connections). Freerouting not run on it (same stall expected). Gerbers withheld. |

What I would do next (not done): fan out the fine-pitch parts by hand (ESP32, SIM7080G, TCA9554s, TPS61088, IP5356M), pour +3V3/VSYS on In2 on the carrier,
hand-route PVDD / QB / IP_LX / BAT_* on the power board, then autoroute the remainder with a hard pass limit (the jar ignores `-mp`).
Tools: `tools/handroute.py`, `tools/route.py` (Freerouting 2.1.0 jar via DSN/SES, GND poured not routed, width cap per board), `tools/stitch.py`
(GND / pad stitching vias, pruned by DRC), `tools/export.py` (schematic PDF, Gerber+drill zip, JLCPCB BOM/CPL, renders).
Freerouting v2.5.0's CLI crashes (native-image serialization error) and v2.3+ needs Java 25, so the v2.1.0 jar from the project's GitHub release
(66,978,394 bytes, git-ignored `_vendor/freerouting/`) is used. RF width 0.2 mm is an estimate: recompute with the JLCPCB impedance calculator
for the real 1.0 mm 4-layer stack-up. Pi-match shunt pads (DNP) are connected by the autorouter later, not yet.

## DRC / ERC summary (reports in each board folder)

| Board | ERC err / warn | DRC items (refilled zones, schematic parity on) |
|---|---|---|
| carrier | 0 / 0 | silk_edge_clearance 6, silk_over_copper 151, silk_overlap 98, starved_thermal 3, unconnected_items 262 |
| power | 0 / 0 | isolated_copper 15, silk_edge_clearance 1, silk_over_copper 163, silk_overlap 103, starved_thermal 12, unconnected_items 220 |
| front_sensor | 0 / 0 | silk_over_copper 8, silk_overlap 6, starved_thermal 2, unconnected_items 6 |
| front_touch | 0 / 0 | copper_sliver 4 |

No courtyard, edge, drill, short or hole errors remain on any board; `unconnected_items` is the unrouted work above, the rest is silkscreen and starved thermals (cosmetic / to review).

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
- **Battery path:** MR30 J4 (BAT+ pin 1, BAT- pin 3; DNP 4x4 pads TP1/TP2 as an 18 AWG alternative) -> 8 A fuse -> reverse-battery P-FET
  (DMP3013SFV) -> BAT_SW (5 V TVS). Pack NTC on JST SH J5. **The IP5356M's VSYS pins are its internal 5-12 V DC-DC bus, not a system rail**:
  the system rail VSYS is the battery (BAT_SW) through a fitted 0R. Consequence: the system loads bypass the IC, so its fuel gauge does
  not see them and charge termination sees battery current net of the load. J1 now says VSYS = 3.0-4.2 V.
- **IMU (U12 LSM6DSOX, LGA-14):** I2C 0x6A (SA0 = GND, CS = VDDIO), INT1 -> ESP32 IO3 (RTC GPIO3, 100k pull-down so it is low at boot;
  IO3 is the JTAG-source strap, left at its default), INT2 -> TCA9554 0x21 P7. Placed at (-10, 8) mid-board, far from the speaker magnets.
  I2C map, no clash: 0x20/21/22 TCA9554, 0x2C TAS5805M, 0x39 APDS-9960, 0x5A DRV2605L, 0x6A LSM6DSOX; the power IC's address is TBD.
  Aux pins, from ST DS12814 rev 3 table 2 (p. 9), Mode 1 (aux SPI not used): pin 2 SDx and pin 3 SCx "Connect to VDDIO or GND" -> GND;
  pin 10 OCS_Aux "Leave unconnected" -> no connect; pin 11 SDO_Aux "Connect to VDD_IO or leave unconnected" -> VDDIO. (The pins have
  internal pull-ups, register bit "disable pull-up on OCS_Aux and SDO_Aux".) Symbol: modified KiCad LSM6DSL, identical LGA-14 pinout.
- **Qi TX:** separate 24 x 32 mm module on J6 (4-pin SH: 2 x QI_VIN 9 V, 2 x GND) with its **own TPS61088 boost (U7) and an LC filter**,
  see "Qi supply decision". Enable = QI_EN (expander 0x22 P6 over J1), which is U7's EN pin with a 10k pull-down.
- **E-paper (J13 fitted):** Waveshare 3.97inch e-Paper (G), 800 x 480, SSD2677, 24-pin 0.5 mm FPC. **Verified** against Waveshare's
  *3.97inch e-Paper (G) User Manual v1.0* (pin table sec. 5: identical to your list, pin 5 = VSH2) and the *3.97inch e-Paper HAT+ (G)* driver-board
  schematic (R1 2.2R, R2 1M, Q1 AO3400, L1 10uH, D1-D3 MBR0530, C1 4.7uF/25V on pin 5 VSH2, C2 1uF/50V on VDDIO+VCI, C4 1uF on VDD,
  C6-C9 4.7uF on VSH1/VGH/VSL/VGL, C10 1uF on VCOM, C3/C5 4.7uF). The two-colour panel has the same circuit. Pins 1/4/6/7 are NC, each its own
  net; pin 8 BS1 = GND (4-wire SPI). Differences to know: **BUSY is active low** (low = busy), **operating temperature 0..40 C**.
  FPC route (plan, not checked against the cell position in the fit map): the 24-pin tail leaves the panel's bottom edge, runs along the
  rear wall under the carrier's bottom edge (the carrier ends at Y -17.5, J13 enters from -Y) and folds once into J13; the cell and
  power board are on the +X side, so the tail should not cross the cell. Measure the tail length and fold radius on the real panel.
- **Bluetooth antenna:** 2.4 GHz FPC antenna on the inside of the BOTTOM wall, X +38..+64, Z 15..28 (above the pogo pads and the magnets
  at X +32/+70), far from the Wi-Fi PIFA (X -52..-12) and the LTE flex (top wall). J17 stays at the module (X -50): the U.FL
  cable is ~110 mm (about 1 dB at 2.4 GHz for 1.13 mm coax, estimate). It is near the Qi ferrite: test RSSI on the bench.
- **Front sensor acoustics:** the ICS-43434 library footprint already carries the 0.5 mm sound-port NPTH; it lands on (-69.5, 31.25),
  the front-wall hole. A ring-gasket outline (OD 3.6, ID 1.6) is drawn on F.Fab around it: foam/silicone ring between the PCB and the wall,
  airtight. APDS-9960 package centre at (-64, 31.25); its optical-window offset inside the package is not checked.

## IP5356M charger (review 3, item 1) - datasheet V1.00 read (IP5356M-datasheet-en-V1.00.pdf)

- **Cell count / power:** 1 cell (4.2/4.3/4.35/4.4 V), charge up to 18 W / 5 A at the battery, boost 5 V 3.1 A, 9 V 2.22 A, 12 V 1.67 A (p. 1).
- **Ports:** 2 USB-A, USB-B in, Micro/lightning in, **1 Type-C in/out** (PD2.0/3.0, PPS) and "1 USB C input/output port + 1 USB C output port
  (customize)" (p. 1). The datasheet's customised-model table (p. 10: LBZ, DBZ, DBZ_4V35, LCL, DCL1W, DCL1W_4V35) has **no dual-Type-C model
  and no part number for it**: ask Injoinic (service@injoinic.com) for the exact orderable name.
- **I2C:** only the `_L` (LED) models: **IP5356M_LBZ** (orderable at LCSC as **IP5356M_LBZ_CB, C46550232**) and IP5356M_LCL (with lightning).
  Pins: LED2 (pin 1) = SDA, LED1 (pin 40) = SCL, LED3 (pin 2) = INT; fig. 20 on p. 30: 3.3k from each of SDA/SCL to the IC's VCC and 510k from
  INT to ground; the IC enters I2C mode by itself from that wiring; INT is Hi-Z in standby and high when working. **The I2C slave address
  and the register map are NOT in this datasheet** (separate Injoinic document): not found. This design uses exactly fig. 20 and removes
  the carrier's 10k PWR_INT pull-up (it would hide the standby state).
- **NTC:** pin 22 sources 20 uA / 80 uA through the 10k NTC, 100 nF at the pin; if the NTC is absent a 10k to ground is required (p. 29-30, fig. 18).
  The pack's 10k NTC goes to J5. An unplugged J5 reads as "cold" and stops charging (safe).
- **Second Type-C (what I built):** port 2 = VOUT2 (pins 34/35, DPA2/DMA2 pins 32/33) to the J3 Type-C, 2.2 uF + 0.1 uF, Rp 22k from VBUS2 to
  CC1 and CC2 (1.5 A). Only 5 V when more than one port is on. **Open risk:** a real Type-C sink waits for VBUS before drawing current, but VOUT2
  turns on only when the IC detects a load: whether a plain Rd sink wakes it is not in the datasheet. The customised part may solve it: ask Injoinic.
- **Wiring used (datasheet fig. 25):** L1 2.2 uH LX to BAT, BST 0.1 uF to LX, VCC 2.2 uF, VSYS 6 x 22 uF (+0.1 uF), BAT 22 uF + 0.1 uF, VBUS 2 x 2.2 uF + 0.1 uF,
  FCAP (pin 10) 22.1k = 9.9 Ah (R x 0.448 mAh), KEY = PWR_KEY (J1 pin 22 and a carrier test pad), VIN/DPB/DMB (Micro-B), CL (lightning), VOUT1/DPA1/DMA1 (USB-A 1),
  LED4/LED6 left open. D+/D- of the Type-C (DPC/DMC) share the node with the ESP32's USB lines: flag, it may need series resistors or a
  jumper if charge detection and ESP USB flashing disturb each other.
- **Package:** QFN-40 6 x 6 0.5 mm, exposed pad; the KiCad 4.6 x 4.6 EP footprint is used: check against the Injoinic drawing (not in the PDF text I read).

IP5568 (review 2) was rejected: no I2C pins, Qi TX not host-controllable (runs whenever the chip is on, 10/15 W only with all USB ports off,
15 W only at 12 V on VIN), coil unconfirmed (datasheet V1.31 p. 1-2, 16-17, 25).

## Qi supply decision (review 3, item 4): own boost, not the amp's PVDD

- TPS61088 peak switch limit at R_ILIM 49.9k in FPWM (MODE = GND): **7.2 A min / 8.7 A typ / 10.5 A max** (SLVSE52A electrical table); 10 A is the part's
  headline rating only in PFM.
- Amp 2 x 4 W (9.4 W at PVDD) + Qi module ~18 W (15 W TX) = 28 W at 9 V = 3.1 A out = **9.4 A in at 3.3 V** (90 %): above the 7.2 A minimum.
  Qi alone: 6.3 A average + 1.6 A ripple: also too close. So the Qi module does not hang on PVDD.
- Chosen: **second TPS61088 (U7), same circuit as the amp boost, 9.0 V output, EN = QI_EN**, then an LC filter (1 uH + 2 x 10 uF) on the rail that goes to J6.
  Its switching noise stays off PVDD (and the speakers). Charger-path alternative (the IC's 9 V PD output) rejected: it is the port-1 connector rail.
- The cell budget (below) still limits the sum; the second boost only fixes the converter limit and the noise coupling.

## Power budget (review 3, item 2): design for 5 A continuous / 8 A peak from the cell

Cell power at 5 A and 3.3 V (worst case) = 16.5 W; base system (ESP32, SIM idle, display, sensors, IC) taken as 1.5 W; conversion 90 % (amp chain 85 % x 90 %).

| Load | Output power | From the cell | At 3.3 V | Firmware rule |
|---|---|---|---|---|
| Base system | - | 1.5 W | 0.45 A | always on |
| Amp 2 x 4 W (PVDD 9 V) | 8 W | 10.5 W | 3.2 A | gain is cut when Qi or USB-C out is active |
| Qi TX 5 W profile | 5 W | ~7 W | 2.1 A | allowed with the amp at reduced gain |
| Qi TX 10 W profile | 10 W | ~14 W | 4.2 A | leaves ~1 W for the amp: amp muted |
| Qi TX 15 W profile | 15 W | ~21 W | 6.4 A | **not on battery** (over 5 A): only with VBUS present, and then the cell is bypassed by the IC input path |
| USB-C out 5 V 3 A | 15 W | ~16.5 W | 5.0 A | amp muted; limit to 10 W (9 V 1.1 A) when the amp or Qi is on |
| USB-C port 2 5 V 1.5 A | 7.5 W | ~8.5 W | 2.6 A | counted in the sum |

Priority (firmware): **charging other devices first** (USB-C out, Qi), then the amp: the amp gain is cut so that
`P_cell_total <= 16.5 W` (about 5 A at 3.3 V; use the measured battery voltage: I_cell <= 5 A). Peak 8 A is allowed for bursts only (SIM TX, amp
transients, < 100 ms); F1 (8 A fast) protects the path. The amp's per-channel limit of 4 W (5.66 Vrms into 8 ohm) is set in the TAS5805M
(AGL / digital volume ceiling) before unmuting. Examples: Qi 5 W (7 W) + base (1.5 W) -> 8 W left -> about 5.7 W electrical -> 2.8 W per channel; the amp
alone: full 4 W per channel. **The pack's PCM limit is still unknown: if it is below 5 A the table scales down.**

## Verification status

| Item | Status |
|---|---|
| SIM7080G footprint | Accelerando footprint **checked against SIMCom's land pattern** (SIM7080G/Y7080E HD fig. 4): pitches, inner pads, centre GND pads match; edge pads trimmed 0.3 mm to SIMCom's outer extents; forbidden-area keepout added (position read off the drawing). Pin table from the brief, cross-checked with HD fig. 2. |
| EWM104-BT5125 footprint | **Ebyte's official KiCad file**, pads unchanged; fixed vendor export errors: pads were on B.Cu, outline on Edge.Cuts, duplicate thru-holes. Numbering matches the manual's top view. |
| USB-C 124019572112A footprint | **Built by me from Amphenol drawing C 12401957 sheet 2, read on screen** (CDN blocks downloads). Shell hooks drawn as straight slots (the drawing shows L shapes). **Verify before fab.** 3D model not attached (STEP origin offset unresolved). |
| TAS5805M PWP | KiCad footprint matches TI PWP0028M (3.4 x 9.7 pad, 3.1 x 4.05 mask); vias raised to 0.3 mm. |
| TPS61088 RHL | KiCad `Texas_VQFN-RHL-20`; the TPS61088 datasheet download was blocked, the **-Q1 datasheet (SLVSE52A)** was used for pins and values. Check the RHL land pattern against the TPS61088 drawing. |
| SSD1322 support parts | From the SSD1322 datasheet rev 1.2 fig. 14-1 and sec. 8.6 (IREF = 620k at 12 V). FPC pin 1 direction vs the folded panel tail: **not verified**. |
| E-paper (G) FPC pinout + booster | Verified against the Waveshare (G) panel manual and the HAT+ (G) driver-board schematic (see above). BUSY active low, 0..40 C. |
| IP5356M | Pins, I2C wiring (fig. 20), NTC, application circuit (fig. 25) from the datasheet V1.00. I2C address, dual-Type-C part number, EP size: not found. |
| LSM6DSOX aux pins | From DS12814 rev 3 table 2 (quoted above). |
| EWM104 PIO1 reset polarity, PIO2-5 button polarity | **Not verified** (needs Ebyte firmware notes). |
| APDS-9960, ICS-43434, DRV2605L, TCA9554, TXB0104, TPS61040, TPS63001 | KiCad symbols/footprints; key values checked against the datasheets (sheet notes). |

## Open items

1. **Charger:** IP5356M_LBZ_CB (see above). Open: its I2C address/registers, the dual-Type-C part number (ask Injoinic), the port-2 wake-up question.
2. **Battery connector current:** MR30 (15 A); open: the cell's PCM current limit (see power budget).
3. **ESP32-S3-WROOM-1U-N16R8 is rated 65 C ambient** (module datasheet table 1-2). Keep it away from the amp heat.
4. Bluetooth 2.4 GHz FPC antenna position; GNSS active-patch bias (LNA) not provided (pi pads only).
5. E-paper FPC route past the cell: plan only, measure on the real panel.
6. Front sensor and touch strip have no mounting holes (no room): bosses/adhesive in the front wall.
7. The board-to-board cable J1 carries speaker L at up to ~1.5 A peak: 2 contacts per leg (JST SH 1 A each).
8. Silkscreen cleanup, fiducials, and JLCPCB stack-up/impedance (CPWG widths) are still to do after routing.
9. Power board: leftover passives are placed on B.Cu (`allow_back`): check the height behind the board; the 4 DNP/alt parts and heights are not checked against the fit map.

## Sources

SIM7080G/Y7080E Hardware Design (SIMCom), Accelerando `SIM7080G.kicad_mod`, Ebyte EWM104-BT5125 user manual
V1.0 + PCB package (cdebyte.com), SSD1322 datasheet rev 1.2 (Solomon Systech), TAS5805M SLASEH5D, TPS61088-Q1
SLVSE52A, TPS61040, TPS63001, DRV2605L, TCA9554, TXB0104 (TI), APDS-9960 (Broadcom), ESP32-S3-WROOM-1/1U
datasheet v1.8 (Espressif, in `cad/models/`), Amphenol drawing C 12401957.

## Still unverified (flagged, review item 10)

- USB-C 124019572112A footprint (built from the drawing read on screen).
- TPS61088 values and footprint (taken from the -Q1 datasheet SLVSE52A).
- EWM104 PIO1 reset / PIO2-5 button polarity.
- Panel (SSD1322) FPC pin 1 after the fold.
- JST SH 22-pin footprint (extended from SM20B), MR30 footprint outline, APDS-9960 window offset, IP5356M EP size and I2C address.
- RF line width (0.2 mm estimate) and the 1.0 mm stack-up.
