# Hardware safety

These rules are not negotiable. The `hardware-safety-reviewer` agent checks changes
against them.

## Phase gate

- **Phase 1 to 7 bench work runs from USB only.** No LiPo wiring until Phase 8.
- LED brightness is capped in software at 25 percent
  (`HS_BRIGHTNESS_CAP_PERCENT`) and current is limited (`HS_LED_MAX_MILLIAMPS`)
  until power is characterised in Phase 8.
- The HUB75 panel is never powered from a dev board's 5V pin. Use a bench supply.

## Battery

- Single 3.7 V LiPo cell **with a protection board** (over-charge, over-discharge,
  over-current, short circuit).
- **JST connector on the battery.** The cell is never soldered directly to the
  board and can be unplugged before any work.
- **Swelling gap:** 0.5 to 1 mm of free space over the cell's face in the
  enclosure (`battery_swell_gap` in `cad/params.csv`). Nothing sharp faces the cell.
- **Charge stop at about 90 percent while docked,** to extend cell life.
- **No heat to open the case.** No glue that needs a heat gun, no heat-set step
  near the cell after it is installed. The case opens with screws or clips.
- Keep the cell away from the charger IC, the wireless charging coil, and the
  panel's driver ICs, or put a gap or barrier between them.
- Charge temperature limits and maximum charge current: verify against the cell
  datasheet. Do not charge below 0 °C.

## Handling

- Never charge unattended during prototyping. Charge on a non-flammable surface.
- Stop using a cell that is swollen, dented, punctured, or hot.
- Unplug the battery before soldering or changing wiring.
- Do not short the pogo pins: the dock contacts must be dead until the device is seated,
  or current-limited. Design this in Phase 10.

## Enclosure

- Hard limit: 3.5 cm thick.
- IP54 is a design target, not a certification: gasket the seam, mesh the speaker
  and mic openings, and seal or plug the USB-C port. Do not seal the case airtight
  around the cell without considering venting.

## Radio and location

- LTE-M antenna placement and SAR are out of scope for the prototype; keep the
  antenna away from the body side where practical.
