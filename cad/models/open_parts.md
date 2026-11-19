# Open parts: two options each

## Picked (2026-11-19), in the assembly

| Part | Pick | Notes |
|---|---|---|
| Cell | LiPol **LP1160100** (100 +-1 x 60 +-0.5 x 11 +-0.3) | Modelled at its max envelope; swell gap measured above 11.3. Order with a 10 k NTC (wired to the IP5328P NTC input), **150 mm leads** and a JST PH 3-pin housing (the LiPol datasheet says NTC: no). PCM end faces -X in the case (ADR 0016) |
| OLED | **Bare 3.12 in SSD1322 panel** (Winstar WEX025664B class), dead front (ADR 0015) | 88 x 27.8 x 2.15, model from the drawing in `oled_wex025664b_panel_312`; replaces the NHD-2.7 module (2026-11-19) |
| GNSS | Taoglas **SGGP.12.4.A.02** | SMD: needs a ground-plane board (16 x 13 modelled) |
| LTE flex | Molex **212570-0100** | Fits the top wall (X -28.2..12.2, Z 11.9..27.3, no clash). **But it covers 824-960 / 1710-2170 MHz only: no 700 MHz LTE-M bands** (B12/B13/B28/B85). See the alternative below |

**LTE alternative with the 700 MHz bands, same spot:** Linx (TE) **ANT-5GLFPC1-UFL-100**, flex
with a 100 mm U.FL cable, 698-960 MHz plus the upper bands. Sources disagree on its size
(39 x 15 x 0.2 or 42 x 12 x 0.2), and both fit the 40.4 x 15.4 spot. Its low-band efficiency is
low (about 18 %, -8 dBi peak), as any 40 mm antenna is at 700 MHz. Pick by carrier: keep the
Molex if the network uses only B3/B5/B8/B20, take the Linx if it needs B12/B13/B28/B85. A 90 to
96 mm flex (Ezurio Revie Flex, Taoglas FXUB63) performs better but does not fit the top wall.

Collected 2026-11-19 from maker and distributor pages. Prices are single-unit list prices
as found that day (marketplace prices move a lot): check before ordering. **Nothing has been
bought.** "STEP" means a free STEP from the maker or an official library, checked; "not
checked" means the maker may have one behind a login.

## 10,000 mAh LiPo pouch, protection board + NTC, <= 100 x 60 x 12 mm

| | Part | Size (mm) | Price | STEP | Link |
|---|---|---|---|---|---|
| A | LP1160100, 3.7 V 10,000 mAh, PCM, 10 k NTC, Molex 51021-0300 | 11 x 60 x 100 | not listed (a 1160100 with PCM sells for $19.99 on Tindie) | no | https://www.lipobattery.us/cb-iec62133-un38-3-msds-certified-lp1160100-10000mah-3-7v-37wh-lipo-battery-with-pcm-and-wires-and-10k-ntc-and-molex-51021-0300/ |
| B | LP1260100, 3.7 V 10,000 mAh, PCM, 10 k NTC, JST PHR-3 | 12 x 60 x 100 | not listed | no | https://www.lipolbattery.com (LP1260100 datasheet) |

**A was picked** (see the top of this file). Resolved by the LiPol drawing:

- **Thickness:** 11 +-0.3, so the model uses 11.3 (Z 1.0..12.3) + 0.2 insulator + 1.2 gap; the
  board layer moved down to Z 13.7.
- **Length:** 100 +-1 includes the folded PCM, so the model uses 101 (X -54.5..46.5). The vertical
  Qi TX board is 4.5 mm off the cell end (5.3 to its far face); the PD board's hot parts move to
  X >= 47 with a barrier (`docs/hardware/board-plans.md`).
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

## Qi transmitter: magnetic modules (coil + magnets + driver), no Qi2 certification needed

Moved to `docs/hardware/board-plans.md` section (d) (2026-11-19): three modules checked against
the front-coil space of the 157 mm case (dia <= 56 at X 47.95, 2.8 to about 3.9 deep) and the
driver slots. Recommendation there: a generic 15 W Qi TX PCBA (24 x 32 x 2.0) with a 50 mm coil and
an N52 ring, its PCBA flat under the coil.
