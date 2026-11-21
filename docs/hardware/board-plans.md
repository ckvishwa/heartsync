# Board plans: carrier rev B, front board, power board, Qi TX

Status: **plan only, not routed** (2026-11-19, ADR 0016). The assembly
(`cad/fusion/heartsync_assembly.py`, phase 4) models every outline below with its main parts,
and the fit check runs against them.

Model coordinates: X along the length (+X right end), Y across (+Y = TOP edge), Z thickness
(+Z = FRONT), origin at the case centre, Z 0 = lid inner face. Case 157 x 72.5 (ADR 0014).
Board layer Z 13.7..15.3 (above the cell's 1.2 swell gap). Front wall inner face Z 27.2.
Carrier rev A sits at X -36..34, Y -15..30 (KiCad origin top-left: world = (-36 + x, 30 - y)).

## (a) Carrier rev B

**Outline:** rev A (70 x 45) plus a tab off the bottom edge, **X -40.0..-5.5, Y -31.5..-15.0**
(34.5 x 16.5; KiCad x -4..30.5, y 45..61.5), same 1.6 mm board and layer, R1 corners. The tab
stays 0.65 mm off the pogo board (Y -32.15) and 18 mm off the left speaker cradle.

**On the tab** (no parts on the underside: it sits over the swell gap):

| Ref | Part | Centre (X, Y) | Size | Notes |
|---|---|---|---|---|
| U10 | SIMCom SIM7080G, LCC | (-27.7, -23.35) | 17.6 x 15.7 x 2.4 | replaces the SIM breakout and J3 |
| J13 | nano-SIM push-push holder | (-11.8, -24.5) | 12.5 x 13 x 1.4 | 1.8 V SIM only (SIM7080G); MFF2 eSIM footprint as an option |
| J14 | U.FL, GNSS | (-38.3, -29.5) | 3 x 3 | 25 mm coax to the GNSS ground board at (-50, -27.5) |
| J15 | U.FL, LTE | (-7.0, -16.5) | 3 x 3 | Molex 212570 cable (100 mm): about 85 mm route from the top wall |
| C20-C22 | 100 uF + 10 uF + 33 pF | (-38.2, -18.8) | | at the VBAT pins, short and wide |

U9 (TXS0102, 1.8 V <-> 3.3 V) and Q1 (PWRKEY) move next to the tab.

**Connectors:**

| Ref | Change | Position (world) | Pins |
|---|---|---|---|
| J3 | **delete** (SIM now on the board) | | |
| J8, J10, J11 | **delete**, replaced by J16 | | |
| J16 | **new**: 18-way 0.5 mm FPC (one flex to the front board) | under the front board's J2F at about (-3, 13) | see below |
| J1 | 7 -> **8 pins**: add I2C_SDA, I2C_SCL; drop one GND | right edge (30.0, 14.25) | +5V x 2, GND, USB D+, D-, ALERT_N, SDA, SCL |
| J2 | keep (VBAT sense) | | |

J16, 18 ways: 3V3, MIC_3V3, VBAT, OLED_SCK, OLED_MOSI,
OLED_CS, OLED_DC, OLED_RST, OLED_VCC_EN, MIC_SCK, MIC_WS, MIC_SD, I2C_SDA, I2C_SCL, GND x 4.
Use an 18-way 0.5 mm FPC (Hirose FH12-18S-0.5SH class); the model's connector block is sized for
it (13.0 wide).

**Net changes:**

- Remove nets on J3 (SIM_TXD/RXD, SIM_PWRKEY, VDD_EXT now stay on the board, VBAT to U10).
- New: `OLED_VCC_EN` (ESP32 output, panel VCC after logic; candidate IO3), `QI_EN` (candidate
  IO45, pulled down so the TX is off at boot), `DOCK_SEATED` (input; candidate IO46, a strap pin:
  check the boot levels). Update `docs/hardware/pinout.md` and `firmware/include/config.h`
  together when rev B is drawn.
- U.FL nets `GNSS_RF`, `LTE_RF`: 50 ohm coplanar, short, keep 5 mm from the FlexPIFA.
- Re-run DRC, re-export `cad/heartsync_carrier.step`; the assembly then drops `carrier_tab_revB`.

## (b) Front board (new)

**Outline:** 0.8 mm FR4 at **Z 22.8..23.6**, behind the panel. Main part X -58.0..12.0,
Y -9.9..17.9 (X -58..-50.2 only to Y 17.0, clear of the mute switch pins), a sensor tab
X -50.2..-38.6 up to Y 22.2, a bottom-right extension to X 14.5. Three ears with M1.6 screws into
front-wall bosses (dia 3.8): (-55.0, -13.6), (12.5, -12.0) (over carrier H4), (9.5, 20.0).

It backs the panel's foam ring (1.45 compressed), clamps the carrier bracket (0.1 gap), and keeps
every part out of the window (the lens recess ends at the panel border).

**Parts:**

| Ref | Part | Centre (X, Y) | Face | Notes |
|---|---|---|---|---|
| J1F | Hirose FH19C-30S-0.5SH (panel FPC) | (-32.0, 6.35) | front | under the folded FPC's fingers (Y 2.1..6.1) |
| U1F | 12 to 15 V boost (OLED VCC), SOT-23-6 | (-6.0, 9.0) | front | from VBAT; enabled by OLED_VCC_EN; verify VCC range on the panel datasheet |
| L1F | 10 uH, 2520 | (-1.5, 9.0) | front | parts <= 1.2 tall under the panel (back face Z 25.05) |
| U2F | ICS-43434 I2S mic, bottom port | (-48.0, 20.8) | back | port through a 0.8 board hole, foam tube to the wall hole, ePTFE membrane on the wall |
| U3F | VEML7700 | (-42.5, 20.8) | front | looks out through the 2.0 light hole and its clear window; foam light ring |
| J2F | 18-way 0.5 mm FPC to carrier J16 | (-3.0, 13.4) | back | one flex, about 25 mm |
| C1F.. | VCC caps, VDD/VCI caps, IREF resistor, VCOMH/VSL parts per the SSD1322 reference | front, inside the foam ring | | |

**Nets:** SPI (OLED_SCK, OLED_MOSI, OLED_CS, OLED_DC, OLED_RST) to the panel, I2S (MIC_SCK, MIC_WS,
MIC_SD) and MIC_3V3 (switched by the mute button) to the mic, I2C_SDA/SCL and 3V3 to the VEML7700,
VBAT and OLED_VCC_EN to the boost. Replaces J8 (mic), J10 (light) and J11 (OLED).

Front holes moved to the sensor tab: mic (dia 1.0) at (-48.0, 20.8), light (dia 2.0) at
(-42.5, 20.8). Touch strip pocket X -39..1, Y 20..25 (1.2 wall in front of it).

## (c) Power board (new)

**Outline (ADR 0018):** **X 34.5..56.6, Y 8.0..26.0**, board layer Z 13.7..15.3 (the carrier ends at
X 34.0). The two mid-mount Amphenol 124019572112A USB-C ports sit just above the top edge: port 2
(output only) at X 40.5, port 1 (bidirectional) at X 53.3; PCB top 0.75 below each port's
centreline. 4-layer for heat spreading. Right edge 2.1 mm off the right speaker cradle. No USB-A.
The board sits over the cell's +X end (the folded end; the seal / PCM end is at -X), hot parts at
X >= 49.

**Parts** (IP5328P datasheet typical application):

| Ref | Part | Centre (X, Y) | Size | Notes |
|---|---|---|---|---|
| U1P | IP5328P, QFN40 6 x 6, port 1 charger / boost | (46.3, 18.0) | 6 x 6 x 0.9 | hot |
| L1P | 2.2 uH | (53.0, 16.5) | 7 x 7 x 3 | hot |
| R1P | 10 mOhm sense, 0805 | (44.8, 23.5) | | hot |
| Q1P | output switch, DFN 3.3 | (48.5, 23.0) | | hot |
| C1P-C3P | in / out caps | (41.0, 14.5 / 16.5 / 18.5) | 3.2 x 1.6 | over the cell: caps and connectors only |
| U4P | port 2 source switch, current limit 1.5 A, with CC pull-ups (Rp) | (41.5, 23.3) | SOT-23 class | output only, no data to the carrier |
| U2P | Qi TX load switch | (51.8, 23.3) | SOT-23 | input-fed (port 1 in the sink role, or dock), QI_EN and the NTC window |
| U3P | dock pad switch, **true reverse blocking** (back-to-back FETs or an ideal-diode controller; a plain load switch leaks through its body diode) | (55.0, 23.4) | SOT-23 class | on only with DOCK_SEATED |
| J1P | JST PH **S3B-PH-SM4-TB** (SMD, side entry), cell (BAT+, BAT-, NTC) | (36.8, 21.0) | 4.5 x 9.9 x 4.8 | SMD: no pins toward the cell; leads come up from the top channel |
| J2P | JST SH SM08B to carrier J1 | (40.0, 10.1) | bottom edge, 10 x 4.25 | +5V x 2, GND, D+, D-, ALERT_N, SDA, SCL |
| J3P | JST SH SM04B: dock in (2), Qi TX out (2) | (49.5, 10.1) | bottom edge | dock wires along the bottom channel |

**Nets:** VBUS, CC1, CC2, D+, D- (port 1); VBUS2, CC1_2, CC2_2 (port 2, output only, no data); BAT+, BAT-, NTC (cell, 10 k: verify the IP5328P NTC
curve; if it expects 100 k, add the divider or order the other NTC); 5V out (to carrier J1);
I2C_SDA/SCL (IP5328P register access), ALERT_N (open drain, <= 3.3 V); DOCK_IN, DOCK_SEATED;
QI_PWR, QI_EN.

**Safety review 2026-11-19 (fixes in the plan):**

- Nothing through-hole over the cell (X <= 46.5): J1P is SMD; the USB-C's shell legs must land
  at X > 46.5 or be trimmed flush and insulated (verify on the Amphenol drawing).
- Over the cell only caps and connectors; U2P/U3P moved to the right prong. Inner copper planes
  stop at X 46.5. Phase 8: thermocouple on the cell under the board, worst case 2 A charge +
  Qi TX + 5 V out.
- "Input present" for the Qi TX comes from the charger's charging status or a sense point
  before a reverse-blocking stage and is valid only while port 1 is in the **sink** role (port 1 is
  bidirectional now, ADR 0018): the Qi TX is never fed from VBUS while port 1 sources, so the cell
  can never feed it (verify the role flag in the IP5328P datasheet). Port 2 is source-only.
- The combined output of port 1, port 2, Qi TX and the dock is capped; port 2 alone at 1.5 A.
- The board needs its own mount (two bosses from the front wall or a clip on the bracket frame):
  the device lies on its back, so nothing may let it sag onto the swell gap.
- The 90 percent stop is firmware; if the ESP32 is off or hung while docked the cell charges to
  4.20 V (100 percent). Keep the ESP32 awake while docked, or accept that fallback.

**Rules carried over:** charge voltage strapped to 4.20 V; the ESP32 stops charging at 4.08 to
4.10 V (about 90 percent) over I2C, MAX17048 as a second check (verify the charge-disable
register; else a load switch on the charger input); RSET <= 2.0 A (LP1160100 maximum); Qi TX fed
from the input only, gated on cell NTC, coil NTC, input present and firmware enable; dock pads dead
until seated; no parts on the underside over the cell.

**The cell turns round** (phase 3): PCM end and leads at -X (X -54.5), leads (and the NTC lead)
along the top channel above the side ribs to J1P, about 110 mm: order the cell with **150 mm
leads** and a JST PH 3-pin housing.

## (d) Qi transmitter: magnetic modules (coil + magnet ring + driver), no Qi2 certification

Space at the front coil: dia <= 56 (ring groove), centred X 47.95; depth 2.8 behind the wall now
(ferrite Z 24.4..25.2), at most about 3.9 over the right speaker (its top is Z 23.3) and 3.1 over
the power board's cell connector. Driver slot today: the vertical 30 x 20 board at X 51.8,
Y -32..-2; a flat board can also sit under the coil at Z about 21..23, X 22..46, Y -26..-2 (clear of
the LRA, the carrier and the power board).

| | Module | Size | Fit | Link |
|---|---|---|---|---|
| A | Huagon Charging 15 W magnetic TX module (coil + N52 ring + PCBA; non-certified version) | coil dia 55 (custom sizes), PCBA 40 x 30 x 3 | coil fits; PCBA too big for the 30 x 20 slot, fits flat under the coil only if they cut it to about 30 x 24 (they offer custom shapes) | https://www.huagoncharging.com/product/qi-2-magnetic-fast-wireless-charging-module-magnet-transmitter-receiver-15w-fast-qi-2-two-magnetic-wireless-charger-module.html |
| B | Generic 15 W Qi TX PCBA with a 50 mm coil (WPC 1.2.3), plus an N52 ring OD 56 / ID 44 x 1.5 | PCBA 24 x 32 x 2.0 (seller listing) | coil + ring fit the groove; PCBA fits flat under the coil (X 22..46, Y -26..-2) or turned in the vertical slot if it is 20 tall: verify | https://www.newegg.com/p/2S7-07JP-1M3R3 |
| C | Sealed coil + magnet-ring module (ConvenientPower MPP type) with our own driver from a TI / NXP 15 W reference design on the vertical slot | coil module about dia 54; driver ours | coil fits if <= 2.8 deep; driver shaped to the slot | https://texim-europe.com/getfile.ashx?id=122357 |

Buying requirement for all three: foreign-object detection (a coin or keys on the coil) and an
over-temperature shutdown, confirmed in the datasheet. If the PCBA lies flat under the coil it is
over the cell (7 mm of air): prefer the vertical slot at X 51.8 when it fits.

Recommend **B** for the first build (cheapest, flat PCBA fits under the coil), then A if a
custom-shaped module is worth the MOQ. None is Qi2-certified; the phone charges at the Qi (BPP or
EPP) rate the module supports. All three need the thermal and NTC rules above.

## Fit check against these plans

See `docs/handoff.md` for the run: the phase-4 build includes all three boards, the bracket frame
and the front board, and the fit check is clean (0 clashing pairs).
