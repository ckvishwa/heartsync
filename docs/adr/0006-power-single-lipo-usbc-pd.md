# 0006: Power is a single LiPo with a USB-C PD power bank chip

- **Date:** 2026-11-16
- **Status:** Accepted

## Decision

Each device runs from one 3.7 V, 10,000 mAh LiPo cell with a protection board,
managed by a two-way USB-C PD power bank chip (charges the cell, and can power a
phone). A wireless charging coil on the back and pogo pins on the dock also charge
it. A 500 mAh backup cell keeps tracking alive. While docked, charging stops at
about 90 percent.

Until Phase 8, all bench work runs from USB only, with LED brightness capped at
25 percent in software.

## Why

- A single cell avoids balancing and keeps protection simple.
- 10,000 mAh fits the footprint behind the panel within the 3.5 cm limit (to be
  verified in CAD) and covers a bright LED panel plus LTE-M.
- A power bank chip integrates charge, boost, and PD negotiation in one part.
- Stopping at about 90 percent while docked extends cell life for a device that
  lives on its dock.

## Alternatives

- **2S pack:** higher voltage for the panel, but needs balancing and a different charger.
- **18650 cells:** safer casing but too thick for 3.5 cm with the panel.
- **Separate charger, boost, and PD ICs:** more flexible, more board work.
- **No battery, dock only:** defeats the portable design.

## Consequences

- The panel's 5 V rail comes from a boost stage; peak current must be characterised
  in Phase 8 before the brightness cap is raised.
- The enclosure needs a swelling gap of at least 1 mm (1.2 mm used), a JST connector
  on the battery, and must open without heat (`docs/hardware/safety.md`).
  *Amended 2026-11-19: was "0.5 to 1 mm"; raised to match `safety.md` and
  `cad/params.csv` (`battery_swell_gap` = 1.2).*
- Heat sources (charger IC, wireless coil) must be kept off the cell.
- The exact chip and cell are not chosen yet: verify against datasheets.
