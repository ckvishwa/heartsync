# 0015: Dead-front display with a bare 3.12 in SSD1322 panel

- **Date:** 2026-11-19
- **Status:** Proposed

## Decision

1. Display: a **bare 3.12 in 256 x 64 SSD1322 OLED panel** (88.0 x 27.8 x 2.15 envelope, VA
   78.78 x 21.18, Winstar WEX025664B outline), not a module. It replaces the NHD-2.7 module
   (ADR 0013). Left edge 2.5 mm from the left end, centred at Y 4, FPC on the bottom edge,
   folded behind the panel.
2. Dead front: a window of VA + 0.5 mm each side (79.8 x 22.2) through the front wall, a 1.0 mm
   smoked polycarbonate lens (82.8 x 25.2) on a 1.5 mm adhesive foam gasket in a recess, its
   outer face flush with the fabric, and a 1.0 mm fabric-tuck groove round it. The panel border,
   the FPC and the boards stay behind the wall.
3. The panel sits glass-down on the front wall's inner face. A foam ring behind it (1.45
   compressed) bears on the front board (ADR 0016); its left end, over the left speaker, sits on
   a foam pad on the speaker.
4. The panel's FPC goes into a 30-pin 0.5 mm connector on the front board, which also makes the
   panel's VCC (12 to 15 V boost).

## Why

- The user picked the 3.12 in panel and a dead front.
- A bare panel is 2.15 thick against 6.7 for the NHD-2.7 module, so it clears the speakers and
  the carrier, and the old module clashes (mic, bracket, H3 boss, left speaker) go away.
- The VA sits 2.0 from the top edge and 4.62 from the FPC edge (drawing), so the window is placed
  on the VA, not on the panel centre.

## Alternatives

- Newhaven NHD-3.12-25664UCW2 module: 89.2 x 44 x 5.5 with a PCB and a header; too tall for the
  top band and too deep.
- Lens inside the wall: the user wants it flush with the fabric.
- Tuck groove deeper than the lens recess: the lens ledge would print as a floating island
  front-down; both floors are 0.8 deep, which leaves one 2.7 mm overhang ring round the window.

## Consequences

- The carrier's front-wall bosses at H3 and H4 are gone (the panel covers them); a printed
  bracket frame holds all four carrier holes and the front board clamps it.
- The panel model is from the drawing (`cad/models/oled_wex025664b_panel_312`): verify the
  thickness, the FPC fold and the finger position on arrival.
- Firmware: the SSD1322 needs its own driver behind `IDisplay` (ADR 0002) and a supply sequence
  (logic first, then VCC on an enable pin); the brightness cap (25 percent) still applies.
- Print: the 2.7 mm ledge round the window is a flat overhang on the bed side; check it in the PLA
  test print, or add a 0.3 mm sacrificial skin over the window and cut it out.
