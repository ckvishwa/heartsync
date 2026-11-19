# heartsync carrier board v0.1 (KiCad)

Put this folder at `D:\SyncD\hardware\kicad\`.

| File | What it is |
|---|---|
| `heartsync_carrier.py` | The whole circuit as Python (SKiDL). Edit this, not the netlist. |
| `heartsync_carrier.net` | Generated netlist: 67 parts, 52 nets. Import into KiCad. |
| `heartsync_carrier_bom.csv` | Parts list with part numbers and notes |
| `place_board.py` | Run inside the KiCad PCB editor: outline, holes, placement, antenna keepout, GND pours |

## Steps

1. `pip install skidl` (only needed to regenerate after edits), then `python heartsync_carrier.py`.
2. KiCad: new project `heartsync_carrier`, open the PCB editor.
3. File > Import > Netlist > `heartsync_carrier.net` > Update PCB. All footprints come from the
   standard KiCad library, so none should be missing.
4. Tools > Scripting Console:
   `exec(open(r"D:\SyncD\hardware\kicad\place_board.py").read())`
   It prints ok / FAIL per step.
5. Board Setup: set your fab's rules (JLCPCB 2-layer: 0.127 mm track/space, 0.3 mm drill).
6. Route. Power first (+5V to the amps and buck, 0.5 mm+), then I2S, USB pair, the rest.
   The Freerouting plugin can do a first pass; check it by eye after.
7. Inspect > Design Rules Checker until clean. File > Export > STEP, then check fit in Fusion.

There is no schematic sheet: the Python file is the schematic. To change the circuit, edit
the Python, run it again, and use Import Netlist again (KiCad keeps your placement and tracks
for parts that did not change).

## What is on the board

- ESP32-S3-WROOM-1-N16R8, antenna flush with the top edge, keepout under the antenna
- TLV62569 buck: 5 V to 3.3 V, 2 A
- 2x MAX98357A (left / right from one GPIO through R5, R6/R7), powered from 5 V
- DRV2605L haptic driver (LRA), BMI270 IMU (I2C 0x68), MAX17048 fuel gauge (on VBAT)
- USBLC6-2SC6 ESD on USB D+/D-
- TXS0102 level shifter (1.8 V SIM7080G to 3.3 V ESP32) and a BSS138 for SIM PWRKEY
- RESET and BOOT buttons, 7 test points (5V, 3V3, GND, VBAT, UART0 TX/RX, 1V8)
- 12 JST-SH connectors, all on the board edges

## Connectors

| Ref | Pins | To |
|---|---|---|
| J1 | 5V, 5V, GND, GND, D+, D-, ALERT | Power bank / USB-C module |
| J2 | VBAT, GND | Battery (fuel gauge and SIM supply) |
| J3 | VBAT, GND, TXD, RXD, PWRKEY, VDD_EXT | SIM7080G module (1.8 V I/O) |
| J4, J5 | +, - | Left / right speaker |
| J6 | +, - | Haptic LRA |
| J7 | T1, T2, T3, GND | Touch strip |
| J8 | MIC_3V3, GND, SCK, WS, SD | INMP441 mic (power cut by mute switch) |
| J9 | 3V3 out, MIC_3V3 back | Mute slide switch |
| J10 | 3V3, GND, SDA, SCL | VEML7700 light sensor |
| J11 | 3V3, GND, SCK, MOSI, CS, DC, RST | OLED (SPI) |
| J12 | 3V3, GND, LADDER, POWER | Button strip |

Button strip ladder (on the strip, each button to GND through its resistor, 10k pull-up on
this board): Vol- 0 ohm (0 V), Vol+ 3.3k (about 0.8 V), Play 10k (about 1.65 V).

## Check before ordering

- Every chip's pinout against its datasheet (taken from the official KiCad 10 symbols; the
  MAX17048 from its datasheet; the BMI270 from a community symbol).
- J1 ALERT: the power bank module's interrupt must be open-drain and at most 3.3 V.
- J3: if your SIM7080G board already has 3.3 V level shifting, bridge the TXS0102 or skip it.
- J11: the 2.7in OLED controller and connector are not chosen yet; J11 is a cable header for now.
- JST-SH orientation: rotate each connector so its cable entry faces the board edge.
- MAX98357A SD_MODE levels with R5-R7 (left > 1.4 V, right 0.77-1.4 V).
