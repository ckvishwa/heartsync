# 0016: Custom boards: carrier rev B, front board, power board

- **Date:** 2026-11-19
- **Status:** Proposed

## Decision

Plan (not routed) three boards of our own, shaped to their slots in the 157 mm case. Outlines,
connector positions and net changes are in `docs/hardware/board-plans.md`; the assembly models
each outline with its main parts.

1. **Carrier rev B:** the SIM7080G LCC module, a nano-SIM push-push holder and two U.FL sockets
   (GNSS, LTE) on a tab off the bottom edge (X -40..-5.5, Y -31.5..-15). J3 and the SIM breakout
   board go. J8, J10 and J11 become one 18-way 0.5 mm FPC connector (J16) for the front board.
2. **Front board** (0.8 FR4 behind the panel): panel FPC connector, OLED VCC boost and caps,
   ICS-43434 mic and VEML7700 light sensor behind the top-left holes, one flex to the carrier.
   Three M1.6 screws into front-wall bosses; it clamps the carrier bracket.
3. **Power board**: IP5328P from its reference design, 21.5 x 24.5 with a cut-out for the
   mid-mount USB-C (on this board), cell NTC input, hot parts at X >= 48, past the cell's end.
   The Qi TX is fed from the input only, and the dock pads stay dead until seated.
4. Qi transmitter: buy a magnetic module (coil + magnet ring + driver); no Qi2 certification.
   Candidates in `docs/hardware/board-plans.md` (d).
5. The cell turns round: its PCM (seal) end and leads face -X, so the power board over the
   cell's +X end does not overhang the seal end.

## Why

- The Adafruit breakouts (12 clashes), the generic power-bank module (USB-A ports, 65 x 32.5)
  and the SIM breakout did not fit; our own boards can take the shapes the case leaves.
- One flex to the front replaces three harnesses; the carrier loses a 6-way cable across the
  device.
- With the PCM end at -X, the hot parts and the Qi TX board sit at the cell's plain end, away
  from its seal and protection board.

## Alternatives

- Keep breakout boards and move parts around them: no layout cleared the mic, the light sensor,
  the buttons and the display together.
- Power board past the cell end only (X >= 47): 9.75 mm wide, too narrow for the USB-C cut-out.
- A vertical power board: turns the USB-C on its side in the top edge.

## Consequences

- Three boards to design, order and test instead of breakouts; rev A carrier STEP stays in the
  assembly until rev B is laid out (its J3, J8, J10, J11 are still there).
- The cell's leads (and the NTC lead) run along the top channel to the power board, about 110 mm:
  order the cell with 150 mm leads and a JST PH 3-pin housing.
- Firmware: new pins for OLED VCC enable, IP5328P I2C, dock seated detect and the Qi TX enable;
  update `firmware/include/config.h` and `docs/hardware/pinout.md` together when rev B is drawn.
- Verify before layout: IP5328P charge-disable register, NTC curve (10 k?), RSET <= 2.0 A.
