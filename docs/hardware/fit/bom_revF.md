# HeartSync BOM, rev F (185 mm, 3.12 in panel, 2 × USB-C + USB-A)

Per device; double for the pair. # = the number on the unfold and the fit map.

| # | Part | Exact part / spec | Qty | Where it goes | Check when fitting |
|---|---|---|---|---|---|
| | **Radio and antennas** | | | | |
| 2 | Wi-Fi/BLE MCU | Espressif ESP32-S3-WROOM-1U-N16R8 (U.FL antenna variant) | 1 | B · on the carrier at X -36..-18, Y 10..30; U.FL at X -21, Y 27 (top edge) | 2.4 GHz only. U.FL must face the top edge, 3 mm clear |
| 3 | Wi-Fi antenna | Ezurio FlexPIFA 001-0014 (2 dBi, MHF1/U.FL, 100 mm cable) | 1 | C · taped to the inside of the front wall, X -52..-12, Y -33..-22, cable end LEFT | Check your cable length (you mentioned 001-0016). Bend radius ≥ 6, coax runs round the panel's left side to the U.FL |
| 4 | LTE-M antenna | Linx/TE ANT-5GLFPC1-UFL-100 (698–960 + upper bands, U.FL) | 1 | D · taped to the inside of the top wall, X -20..+22, Z 12..27 | Replaces the Molex 212570 (no 700 MHz). 9.6 mm from the USB-A, 5 mm from the last button |
| 5 | LTE-M / GNSS modem | SIMCom SIM7080G board (now) → LCC on carrier rev B; nano-SIM or MFF2 | 1 | B · X -58..-26, Y -33..-15.5, board layer | Cable to J3 (VBAT, GND, TXD, RXD, PWRKEY, VDD_EXT). Activate the SIM before you close the case |
| 6 | GNSS patch | Taoglas SGGP.12.4.A.02 (12 × 12 × 4) on a 16 × 13 ground board + U.FL lead | 1 | C · front wall, X -72..-56, Y -34..-21, patch facing the front | 3 mm clear of speaker L. Sky-facing when the device lies on its back |
| | **Display and front** | | | | |
| 7 | Display | 3.12 in SSD1322 256 × 64 bare OLED panel, 88 × 27.8 × 2.15, FPC tail; 12 V VCC boost | 1 | C · front wall, X -90..-2, Y -9.9..17.9; window centre X -46, Y +4 | Measure where the active area sits on YOUR panel (left/right/top/bottom border). If the window is off by > 0.5 mm, send me the numbers |
| 8 | Lens + gasket | Smoked polycarbonate 81.8 × 24.2 × 1.0; 1.5 mm adhesive foam gasket; 1 mm foam ring behind the panel | 1 set | C · in the window pocket, flush with the fabric | Cut the lens to the pocket, not the window. Fabric tucks 1 mm into the groove round it |
| 12 | Qi transmitter | Magnetic Qi module: coil 50 mm + N52 ring 56/44 × 1.5 + driver (option B for the bench, A later) | 1 | C · coil + ferrite against the front wall, centre X +45, Y 0. Driver board vertical at X 68, Y -32..-2 | Runs from USB input only, never from the cell; stops on cell temperature. Ring is 2 mm clear of speaker R in plan: test the phone still snaps |
| 14 | Microphone | TDK ICS-43434 (I2S) on the mic + light board | 1 | C · front wall, port behind the 1.0 mm hole at X -74, Y 29.5 | 0.7 mm clear of the corner screw boss. Seal the port with a gasket ring |
| 15 | Light sensor | Vishay VEML7700 on the same board | 1 | C · behind the 2.0 mm hole at X -69.5, Y 29.5 | Clear window or a light pipe through the fabric |
| 16 | Touch strip | 40 × 5 copper strip PCB (ESP32-S3 touch pins) | 1 | C · under the front wall, X -64..-24, Y 25.5..30.5 (wall 1.2 mm) | Cable to J7 |
| | **Sound and haptics** | | | | |
| 9 | Speaker L | Same Sky CES-571423-28PMB, 57.5 × 23 × 14.85, 8 Ω, ears cut | 1 | D · left end, face 1 mm foam → ePTFE → honeycomb; printed cradle behind | Cable to J4. Polarity mark + |
| 10 | Speaker R | Same Sky CES-571423-28PMB | 1 | D · right end, same stack | Cable to J5 |
| 24 | Acoustic membrane | ePTFE acoustic vent sheet, adhesive back, 58.4 × 25.6 per end | 2 | D · inside each end wall over the whole honeycomb | No wrinkles; press from the centre out |
| 19 | Haptic | 10 mm LRA coin (driver DRV2605L on the carrier) | 1 | D · on the fin near the bottom edge, X 22, Y -29 | Cable to J6 |
| | **Power** | | | | |
| 13 | Cell | LiPol LP1160100, 3.7 V 10,000 mAh, PCM, + 10 k NTC, JST lead | 1 | A · on the lid, X -54.5..46.5, Y ±30; PCM end at +X (right) | Measure its real thickness: the 1.2 mm swell gap is set from 11.3 max. Never press or pierce; no hard edges against it |
| 18 | Power board | Custom board, 42 × 21, with a power-bank chip that has TWO Type-C ports + USB-A out (the IP5328P has only one C) | 1 | B · X 30..72, Y 12..33; all 3 ports mount on it | Pick the chip before ordering: 2 × C in/out, A out, I2C charge limit, NTC input. Hot parts past X 47 (off the cell) |
| 11 | USB-C ×2 | Amphenol 124019572112A, waterproof, mid-mount | 2 | D · top wall at X +52.75 and +66.05, Z 16 | Gasket on the inside rim; plug test both before closing |
| 28 | USB-A | USB Type-A receptacle, mid-mount (a USB 3.0 socket fits the same hole; only the USB 2 / power pins get used) | 1 | D · top wall at X +38.5, Z 16.6; opening 13.7 × 6.3 | Charge-out only. No data beyond USB 2. Not waterproof: needs a rubber flap or plug |
| | **Controls and dock** | | | | |
| 17 | Buttons | 5 × C&K PTS645 momentary tactile (mute is a firmware toggle now) + printed caps 5.2 × 4.6 | 5 | D · top wall, centres X -68 / -58.2 / -48.4 / -38.6 / -28.8, Z 19.7 | Clear of speaker L. Button strip cable to J12, mute LED to J9 |
| 20 | Pogo pads | 4 × 2.5 mm flat pogo target pads | 4 | D · bottom wall, X -12 / -4 / 4 / 12, middle of the face | Dead until docked (power board decides). Seal round each |
| 21 | Dock magnets | N52 disc 6 × 2 | 4 | D · bottom wall pockets, X ±32 / ±70, 1.6 mm skin | Mark polarity; the dock gets the opposite pole |
| | **Boards, shell and fixings** | | | | |
| 1 | Carrier PCB | HeartSync carrier 70 × 45, 2-layer (JLCPCB). On it: MAX98357A × 2, DRV2605L, BMI270, MAX17048, TLV62569, USBLC6, TXS0102, J1–J12 | 1 | B · X -44..26 (moved 8 mm left for the ports), Y -15..30, Z 13.7; bracket at H1/H2, bosses + pins at H3/H4 | Plug every cable into J1–J12 before placing it; nothing pinched under it |
| 22 | Back ring | TPU, printed, 4 wide × 2.5 tall (1.0 in the channel, 1.5 proud), R6 | 1 | Back · 2.5 mm in from the edge, all the way round | Press-fit last; it hides the screws |
| 23 | Screws + inserts | M2 low-head screws (head ≤ 3.8 × 1.3), M2 heat-set inserts | 4 + 4 | Corners X ±80, Y ±31.7 | Melt the inserts in BEFORE any electronics go in |
| 25 | Foam + insulation | 1 mm EVA under the cell; 0.2 mm fish paper/Kapton over it; 1 mm speaker pads | 1 set | A + D | Keep the 1.2 mm gap above the cell empty |
| 26 | Fabric | Front + top wrap, thin knit, contact adhesive | 1 | Front + top edge (see the net) | Cut the window, mic, light, button and USB holes AFTER it's glued |
| 27 | Printed shell | PETG: tray, lid (3.0), bracket, 2 speaker cradles; PLA for the test print | 1 set | Whole shell | First print in PLA: check the 0.8 mm honeycomb webs and the panel window |
