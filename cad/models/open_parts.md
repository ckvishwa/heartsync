# Open parts: two options each

Collected 2026-11-19 from maker and distributor pages. Prices are single-unit list prices
as found that day (marketplace prices move a lot): check before ordering. **Nothing has been
bought.** "STEP" means a free STEP from the maker or an official library, checked; "not
checked" means the maker may have one behind a login.

## 10,000 mAh LiPo pouch, protection board + NTC, <= 100 x 60 x 12 mm

| | Part | Size (mm) | Price | STEP | Link |
|---|---|---|---|---|---|
| A | LP1160100, 3.7 V 10,000 mAh, PCM, 10 k NTC, Molex 51021-0300 | 11 x 60 x 100 | not listed (a 1160100 with PCM sells for $19.99 on Tindie) | no | https://www.lipobattery.us/cb-iec62133-un38-3-msds-certified-lp1160100-10000mah-3-7v-37wh-lipo-battery-with-pcm-and-wires-and-10k-ntc-and-molex-51021-0300/ |
| B | LP1260100, 3.7 V 10,000 mAh, PCM, 10 k NTC, JST PHR-3 | 12 x 60 x 100 | not listed | no | https://www.lipolbattery.com (LP1260100 datasheet) |

Leaning **A** (11 mm nominal, CB/IEC 62133/UN38.3 paperwork), with these checks before
choosing either (from the hardware safety review):

- **Thickness:** size the swell gap from the datasheet's *maximum* thickness, not the nominal.
  The model allows 12.0 (Z 1..13) + 0.2 insulator + 1.2 gap. B at 12 nominal plus a typical
  +0.3 to +0.5 tolerance eats into the 1.2 mm gap, possibly below the 1 mm minimum.
- **Length:** check whether the 100 mm includes the folded PCM and tabs. The placeholder is
  95 + 5 seal, the Qi2 TX board sits 5 mm off the cell end, and the PD board already
  overhangs the seal end by about 11.5 mm: re-check both gaps against the real drawing.
- **Connector:** the safety rule says a JST connector on the battery. A ships with a Molex
  51021-0300 (PicoBlade); B has a JST PHR-3. Ask for a JST lead on A, or record an
  exception in an ADR. The PD board header must match.
- **NTC:** one LiPol datasheet for LP1160100 says "NTC: no", so confirm it with the seller.
  The cell's 10 k NTC must go to the charger's NTC input, so charging (and Qi2 TX) stops on
  cell temperature, including below 0 °C.

A pouch cell has no STEP: model it from the cell drawing on arrival (PCM fold and tab
positions included).

## OLED

| | Part | Size (mm) | Price | STEP | Link |
|---|---|---|---|---|---|
| A | Newhaven NHD-2.7-12864WDW3, 2.7 in 128 x 64, white | 82 x 47.5 x 5.5 | $38.08 | **yes** (in `oled_nhd-2.7-12864wdw3`) | https://newhavendisplay.com/2-7-inch-white-graphic-oled-module/ |
| B | Newhaven NHD-3.12-25664UCW2, 3.12 in 256 x 64, white | 89.2 x 44 x 5.5 | $38.17 | **yes** (in `oled_nhd-3.12-25664ucw2`) | https://newhavendisplay.com/3-12-inch-white-graphic-oled-module/ |

Cheaper but no STEP: GoldenMorning GME12864-115 (2.7 in, SSD1327, I2C, 82.3 x 52.2 x 2.8,
about $14.90). Recommend **A** (matches `DISPLAY = "2.7"`); it is much thicker than the
bare-glass stand-in.

## SIM7080G board

| | Part | Size (mm) | Price | STEP | Link |
|---|---|---|---|---|---|
| A | Waveshare Pico-SIM7080G-Cat-M/NB-IoT (nano SIM, 1.8 V SIM only) | 76.15 x 24 (73.5 x 24 variant) | about GBP 26 | no | https://www.waveshare.com/pico-sim7080g-cat-m-nb-iot.htm |
| B | Electrodragon SIM7080G module (nano SIM, U.FL) | not listed | $12 to $17 | no | https://www.electrodragon.com/?p=57247 |

Neither fits the 32 x 17.5 slot in the layout (commit `6abad791`). The bare SIM7080G (17.6 x 15.7 x 2.4, about
$16 to $23) on the carrier, or on a small daughter board we design, may be the better route.

## LTE flex antenna

| | Part | Size (mm) | Price | STEP | Link |
|---|---|---|---|---|---|
| A | Molex 212570-0100 cellular flex, U.FL | 40.4 x 15.4 x 0.1 | $5.71 | not checked | https://nz.element14.com/molex/212570-0100/cellular-lte-antenna-2-17ghz-1/dp/3261661 |
| B | Molex 146185-0100 quad-band flex, 100 mm cable | 84 x 15 x 0.1 | $5.70 | not checked | https://www.molex.com/en-us/products/part-detail/1461850100 |

The layout has a 40 x 8 strip on the inside of the top wall. A is the right length but 15.4
wide, so it needs a 16 mm tall spot or has to bend; B is twice too long. Check A's low-band
coverage (LTE-M bands 700/800/900 MHz) against its datasheet before choosing.

## GNSS patch, 12 x 12 mm

| | Part | Size (mm) | Price | STEP | Link |
|---|---|---|---|---|---|
| A | Taoglas SGGP.12.4.A.02 (GPS/GLONASS/Galileo, passive) | 12 x 12 x 4 | $1.85 | not checked | https://www.taoglas.com/datasheets/SGGP.12.4.A.02.pdf |
| B | Taoglas GP.1575.12.4.A.02 (GPS L1, passive) | 12 x 12 x 4 | $2.06 (100 MOQ) | not checked | https://shop.richardsonrfpd.com/Products/Product/GP-period-1575-period-12-period-4A02 |

Both are passive and need a small ground plane. The SIM7080G GNSS input takes a passive
patch with an external LNA, or an active one.

## USB-C PD power-bank board

| | Part | Size (mm) | Price | STEP | Link |
|---|---|---|---|---|---|
| A | IP5328P 18 W bidirectional module (USB-C PD + 2 x USB-A + micro-USB) | 65 x 32.5 | about INR 228 (about $2.75) | no | https://hubtronics.in/ip5328p-battery-charging-module |
| B | SW6206/SW6208 22.5 W PD/QC module | not listed | PKR 700 to 900 (about $2.50 to $3.20) | no | https://digilog.pk/products/sw6206-sw6208-qc4-pd3-0-22-5w-power-bank-module-version-b-fast-charging-digilog-pk |

Both carry ports we do not want (USB-A, micro-USB) and are bigger than the 23.75 x 24.5 slot.
The usual path is the bare IP5328P (LCSC C188809) on our own small board with the Amphenol
waterproof USB-C. Before choosing, check against the charger IC's datasheet:

- the NTC input (value expected, 10 k?) is wired to the cell's NTC;
- a lower charge voltage can be set (pin or I2C) so charging stops near 90 percent; most
  modules charge to a fixed 4.2 V;
- the maximum charge current (18 W class) against the cell's maximum charge current;
- dock pogo pads stay dead until the device is seated (the IP5328P can feed power back
  out of its USB-C/VBUS path).

## Qi2 transmitter coil + driver

| | Part | Size (mm) | Price | STEP | Link |
|---|---|---|---|---|---|
| A | ConvenientPower CPS823x Qi2 MPP TX module (coil + magnet ring, sealed) | coil loop dia 39 (module size not published) | not listed (Alibaba MPP TX PCBAs $6 to $12) | no | https://fcc.report/FCC-ID/K7SWIC008V2/7368098.pdf |
| B | Infineon REF_WLC_TX15W_M1 Qi2-capable 15 W TX reference board | under 43 dia | not listed | not checked | https://www.infineon.com/cms/en/product/evaluation-boards/ref_wlc_tx15w_m1 |

The weakest category: no Qi2 MPP TX part publishes both a dimensioned drawing and a price.
Ask ConvenientPower or Generalplus (AH222-A, Qi2 certified, USB PD 9 V input) for a
datasheet and quote before the coil position is fixed. Also ask for:

- thermal shutdown, foreign object detection, and the coil temperature sensor;
- a way to cut TX from the cell's NTC (the coil ferrite overlaps the cell by 26 mm);
- where its 9 V comes from: USB PD in from the wall, or a boost from the cell (more heat
  next to the cell).

## I2S microphone breakout

| | Part | Size (mm) | Price | STEP | Link |
|---|---|---|---|---|---|
| A | Adafruit 6049, ICS-43434 I2S mic | 16.51 x 12.70 x 2.6 | $8.95 | **yes** (MIT, in `mic_adafruit-6049_ics-43434`) | https://www.adafruit.com/product/6049 |
| B | Generic INMP441 I2S breakout | about 14 dia (varies by seller) | about $2 to $4 | no | (marketplace) |

Recommend **A**: TDK has discontinued the INMP441, and the ICS-43434 is its successor.

## Light sensor breakout

| | Part | Size (mm) | Price | STEP | Link |
|---|---|---|---|---|---|
| A | Adafruit 5378, VEML7700 right-angle, STEMMA QT | 25.4 x 17.78 x 4.5 | $4.95 | **yes** (MIT, in `light_adafruit-5378_veml7700`) | https://www.adafruit.com/product/5378 |
| B | Adafruit 4162, VEML7700 flat | not checked | about $4.95 | no (not in Adafruit's CAD repo) | https://www.adafruit.com/product/4162 |

A has the model, but its sensor looks out of the board edge, so the board stands 17.8 mm
deep behind the front wall. B mounts flat against the wall like the stand-in. Pick B if
depth matters more than having a model.
