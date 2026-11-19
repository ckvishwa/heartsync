# Board plans: SIM on the carrier, custom power board, front sensor board

Status: **plan only, nothing built** (2026-11-19). Model coordinates as in
`cad/fusion/heartsync_assembly.py`: X along the length (+X right end), Y across (+Y = TOP edge),
Z thickness (+Z = FRONT). Board layer Z 13.7..15.3 (above the cell's swell gap). Carrier rev A
sits at X -36..34, Y -15..30 (local origin top-left, world = (-36 + x, 30 - y)).

Clash numbers are from the fit check of the build with the real parts (see `docs/handoff.md`).

## (a) SIM7080G LCC module onto carrier rev B

**Today:** a separate `sim_board` (32 x 17.5, X -58.25..-26.25, Y -33.0..-15.5) with the module,
a nano-SIM holder and two U.FL sockets, cabled to carrier J3 (SM06B: VBAT, GND, TXD, RXD,
PWRKEY, VDD_EXT) on the far right edge at (30.0, 24.75). The cable crosses the whole carrier.

**Plan:**

- Rev B outline: rev A plus a tab off the bottom edge, **X -40..-8, Y -33.0..-15.0** (32 x 18),
  same 1.6 mm board, same layer. Corner radius 1 mm.
- SIM7080G (17.6 x 15.7 x 2.4, LCC) at X -38.0..-20.4, Y -32.2..-16.5, top at Z 17.7.
- SIM: MFF2 eSIM (5 x 6 x 0.9, soldered, 1.8 V) at X -18..-12, Y -24..-19. It needs no holder
  and no door, and the SIM7080G supports only 1.8 V SIMs anyway. A nano-SIM push-push holder
  (12.5 x 13) also fits (X -20..-8) if a removable SIM is wanted.
- U.FL x 2 on the tab's bottom edge, sockets facing -Y:
  - GNSS at (-37.5, -32.0): 25 mm coax to the GNSS ground-plane board at (-60, -27.5).
  - LTE at (-10.0, -16.5) (top-right corner of the tab): the Molex flex cable leaves the antenna
    at (18.8, 33.4, 18.1); about 70 mm route, cable 93 mm (L2).
- Power: VBAT straight from the cell rail already on the carrier (J2 net; SIM7080G takes 2.7 to
  4.8 V, 0.5 A peak). 100 uF + 10 uF + 33 pF at the VBAT pins, short and wide.
- Logic: U9 (TXS0102, 1.8 V <-> 3.3 V) and Q1 (PWRKEY) stay; they move next to the tab.
- No parts on the tab's underside: it sits on the swell gap's top face (Z 13.7) over the cell.
- Keep 5 mm between the tab copper and the FlexPIFA (antenna at Z 24.9..27.4 over X -45..-4.9,
  Y -33.05..-22.05; the tab is 7 to 11 mm below it). The FlexPIFA is rated for mounting near metal;
  check the return loss on the bench.

**Removes:** `sim_board` with its holder, two U.FL sockets and the J3 cable. Clears these clashes:
sim7080g_module x speaker_cradle_L (43.6 mm3), sim_board x speaker_cradle_L (23.2 mm3),
sim_board x speaker_foam_L (5.3 mm3). It also frees X -58.25..-40, Y -33..-15.5, so the GNSS
ground plane can grow.

**Carrier changes:** delete J3, add the tab, two U.FL, the module footprint and the SIM. Re-run DRC
and re-export `cad/heartsync_carrier.step`.

## (b) Custom IP5328P power-bank board shaped to its slot

**Today:** `pd_board` stand-in 23.75 x 24.5 at X 34.5..58.25, Y 8.0..32.5. Clashes:
pd_board x speaker_cradle_R (54.1 mm3), pd_board x usb_c (32.0 mm3: no cut-out for the mid-mount
receptacle), pd_board x speaker_foam_R (14.0 mm3), pd_ip5328p x usb_c (0.11 mm3). The safety
review also flagged hot parts over the cell end.

**Plan** (reference: IP5328P datasheet typical application; QFN40 6 x 6, single 2.2 uH inductor,
10 mOhm sense, NTC input, I2C):

- Outline **X 34.5..55.5, Y 8.0..32.5** (21.0 x 24.5), 4-layer 1.6 mm for heat spreading. The
  right edge stays 0.75 mm off the right speaker cradle's back plate (X 56.25).
- USB-C cut-out for the mid-mount Amphenol 124019572112A: **X 40.6..51.4, Y 25.0..32.5** (body
  10.9 wide, back at Y 25.4). PCB top 0.75 below the receptacle centreline (from the STEP;
  confirm against the Amphenol drawing).
- Hot zone X >= 47 (the cell's max envelope ends at X 46.5): IP5328P at (51.5, 19.0), inductor
  (about 7 x 7 x 3) at (51.5, 12.0), sense resistor and output MOSFET side by side at X 48..55.
  Over the cell (X 34.5..46.5) only the input/output capacitors and connectors.
- Connectors, all JST SH unless noted:
  - **Cell**: JST PH 3-pin (BAT+, BAT-, NTC), top side at X 37..43 on the bottom edge (Y 8),
    entry facing -Y, out of the hot zone. The leads leave the PCM end at X 46.5, Y -21/-25,
    Z 5.7; route them down the cell end and along the bottom wall, away from the inductor.
  - Thermal barrier on the cell's PCM end: Kapton over the end face plus a printed rib (X 47.0..
    48.0, full cell height) between the cell end and the hot parts; the IP5328P and the inductor
    are only 1.5 to 2 mm past the cell's max envelope in X, and the vertical Qi TX board is 5.3 mm
    from the same end.
  - **To carrier J1** (power + USB data + ALERT): left edge at (34.5, 14.0), 4.5 mm from J1 at
    (30.0, 14.25). Make it 8-pin (SM08B) to add the IP5328P SDA/SCL (see below).
  - **Qi TX power**: 2-pin, bottom edge at (54.0, 8.0), to the TX board at X 51.8, Y -32..-2.
    It is fed from the **input** (USB-C VBUS or the dock), never from the IP5328P boost off the
    cell, through a load switch that is ON only when all of these hold: input present, cell NTC
    in range (0 to 45 deg C, the LP1160100 charge window), the coil NTC below its limit, and
    firmware enable. The coil ferrite sits over the cell for 31.5 mm in X (X 15..46.5), 12.5 mm
    above it, with the board layer between: the cell NTC cut-off is a hard requirement, not
    firmware only.
  - **Dock (pogo) input**: 2-pin, bottom edge at (40.0, 8.0); the wires run along the bottom wall
    (3.8 mm channel between the cell, Y -30.25, and the wall, Y -34.05).
- Charge stop at about 90 percent. The IP5328P's charge voltage settings are 4.20 / 4.35 /
  4.40 / 4.50 V, so it cannot stop there by itself:
  - strap the charge-voltage setting to **4.20 V**, so a hung or unflashed ESP32 falls back to
    a normal full charge, never 4.35 or more;
  - the ESP32 stops charging over I2C. **Verify against the datasheet that a charge-disable
    register exists** (Injoinic register maps are often not public). If it does not, add a
    load switch on the charger input that the ESP32 opens;
  - stop on cell voltage (4.08 to 4.10 V), with the MAX17048 percentage as a second check.
- NTC and current: the cell is ordered with a 10 k NTC. **Verify the IP5328P NTC curve**; if it
  expects 100 k, order the cell with that NTC or add a divider, and bench-test hot and cold
  cut-offs. Set the charge current (RSET) to at most 2.0 A, the LP1160100's maximum charge
  current, and confirm the 0 to 45 deg C charge window is enforced.
- No parts on the underside over the cell (X 34.5..46.5): the board sits on the swell gap's top
  face at Z 13.7. The fit check includes the hidden swell-gap keep-out body; nothing clashes
  with it in the current build.
- Dock pads stay dead until the device is seated: a load switch on the pogo input, enabled by a
  seated-detect pin.

**Removes:** the generic module's two USB-A ports, micro-USB and 65 x 32.5 board; the four
clashes above; hot parts over the cell.

## (c) Front sensor board: ICS-43434 + VEML7700 behind the top-left holes

**Today:** Adafruit 6049 (16.5 x 12.7) and 5378 (25.4 x 17.8, right-angle) do not fit. Clashes:
mic x oled 94.6, btn_mute x light 91.5, btn_vol_dn x light 62.2, btn_pwr x light 59.9,
light x mic 42.3, mic x shell_tray 38.2, btn_vol_up x light 32.4, light x speaker_L 16.3,
button_strip_pcb x light 10.1, light x oled 5.2, light x shell_tray 1.0, grille_mesh_L x mic 0.8
(all mm3).

**Free space found:** the NHD-2.7 module's PCB reaches Y 30.17 (top at Z 25.1). Between it and
the top wall (Y 34.05) there is a band **Y 30.4..33.8** from the front wall (Z 27.6) down to the
buttons (bodies top Z 22.7, latching mute 23.2).

**Plan:**

- Board 0.6 mm FR4, **20.0 x 3.4: X -71.5..-51.5, Y 30.4..33.8, Z 23.8..24.4**, parallel to the
  front wall.
- VEML7700 (6.8 x 2.35 x 3.0, top-looking) on the front side at **(-66.5, 32.1)**, top at Z 27.4
  with a 0.2 mm light gasket to the wall.
- ICS-43434 (3.5 x 2.65 x 0.98, bottom port) on the back side at **(-60.0, 32.1)**, Z 22.8..23.8.
  Its port goes through the board and then a 3.2 mm tall foam gasket tube to the wall hole. It
  sits at X >= -62.5 to clear the latching mute (X -70..-63, top Z 23.2); the PWR switch below it
  tops out at Z 22.7 (0.1 mm).
- Front-wall holes move from Y 29.5 to **Y 32.1**: light at X -66.5 (dia 2.0), mic at X -60.0
  (dia 1.0).
- Flex tail, 8-way 0.5 mm pitch (3V3 mic (muted), 3V3, GND, SCK, WS, SD, SDA, SCL). It leaves
  the board's left end, drops at X -73..-71 (between the cavity wall, X -73.8, and the mute
  switch, X -70) to Z 15.5, then runs +X under the button strip at Y 31..33 to an FPC connector
  on the carrier's top edge at about (-34, 29.5) (clear of the H1 boss at (-33, 21)). About 50 mm.
- Carrier rev B: replace J8 (mic, 5-pin, top edge) and J10 (light, 4-pin, bottom edge) with one
  8-pin 0.5 mm FPC connector.

**Removes:** two breakout boards and two harnesses, all 12 sensor clashes above, and the light
sensor standing 17.8 mm deep.

**Seals (IP54):** acoustic mesh (ePTFE) on the mic hole and a clear window or sealed light pipe
in the light hole, both on the inside of the front wall; the gaskets above double as the seal.

**Check:** the band is tight. The board's front-side parts may be at most 3.2 mm tall, and the mic
side clears the switches by only 0.1 mm. Print the board outline as a dummy in the PLA fit test.
