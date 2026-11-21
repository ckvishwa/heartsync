# 0018: Two USB-C ports on the top edge, no USB-A

- **Date:** 2026-11-20
- **Status:** Proposed

## Decision

1. Two Amphenol 124019572112A USB-C receptacles on the top edge, both on the power board, each with
   its own gasket. **No USB-A port anywhere.**
2. **Port 1** (X 53.3) is bidirectional through the IP5328P: it charges the cell and can power a
   phone. **Port 2** (X 40.5) is output only: a current-limited source switch (U4P) behind CC
   pull-ups (Rp), no data lines to the carrier, no sink role.
3. The **combined output is capped**: the IP5328P output current limit is set so port 1 + port 2 +
   Qi TX + the dock together stay inside one budget (set in firmware and by RSET, value to be
   fixed on the bench); port 2 alone is limited by U4P to 1.5 A.
4. The Qi TX is still fed from an input only. With a bidirectional port 1, "input present" must
   mean port 1 is in the **sink** role (or the dock is seated), never VBUS while port 1 sources.

## Why

- A second port lets one cable charge while another device is powered from the cell.
- Output-only is simpler and safer for port 2: no role swap, no PD sink path back into the cell.
- USB-A would need a taller receptacle and a bigger cut in the wall for no benefit.

## Alternatives

- Both ports bidirectional: needs a second PD controller or a port mux.
- One port: the original design; no way to power a phone while charging.

## Consequences

- **LTE gap fails the 7 mm rule at 157 mm:** measured **6.3 mm** from the LTE flex to port 2 (5.8 to
  its gasket, which is 1 mm wider each side). The carrier ends at X 34.0 and speaker_R sits at X 58.75,
  so the two ports (12.2 wide each) fill X 34.4..59.4 with no room to move left. 7 mm needs about
  157.7 mm and **10 mm needs about 161.2 mm** (worst case, gasket), if the carrier and LTE stay
  where they are and the right-hand block (speaker_R, coil, ports) moves out with the length.
- The power board outline is X 34.5..56.6, Y 8.0..26.0; the two port mouths sit just above its top
  edge, so there are no notches. Gaskets are 12.2 wide (pitch 12.8).
- Parts on the power board moved to fit (see `docs/hardware/board-plans.md` (c)).
- Update `docs/hardware/board-plans.md` (c) and the pinout when the board is drawn.
- Verify before layout: IP5328P port mode and output budget registers, the CC pull-up value for a
  1.5 A source, and the Amphenol legs over the board.
