# Bare 3.12 in 256 x 64 SSD1322 OLED panel (Winstar WEX025664B class), picked

**Status:** from drawing, VERIFY ON ARRIVAL  
**Part number:** WEX025664B (white) or any 88.0 x 27.8 SSD1322 COF panel with the same 30-pin FPC
(Raystar REX025664B, FocusLCDs O25664B list the same outline)  
**Collected:** 2026-11-19

## Files

- STEP: `wex025664b_panel_from_drawing.step` (built by `../from_drawing.py`, `panel_312()`)
- Drawing: `WEX025664B_drawing.pdf` (Winstar outline drawing, one page)

## Source

- Drawing: https://www.promelec.ru/UPLOAD/fck/file/winstar1/WEX025664B.pdf

## Licence

Model: ours. Drawing PDF: copyright of Winstar. Keep the repo private.

## Notes (from the drawing)

- Panel 88.0 +-0.3 x 27.8 +-0.3, cap glass 88.0 x 25.8, polarizer 87.0 x 24.8.
- VA 78.78 x 21.18, 4.61 from the left edge and **2.0 from the top** edge (the edge away from the
  FPC); AA 76.778 x 19.178 at 5.61 / 3.0. The bottom ledge under the VA is 4.62 wide.
- Thickness 2.05 on the drawing; the model uses **2.15** (the envelope we were given).
- FPC on the bottom edge: 60.0 wide at the panel, starting 14.0 from the left edge (centred),
  tapering to the 30 fingers (P0.5 x 29 = 14.5, 15.5 over the outer pads), 20.0 long, 0.3 thick,
  0.8 max with the stiffener (4.0 long). The side view shows it folded behind the panel.
- Recommended connector for this FPC class: Hirose FH19C-30S-0.5SH (FocusLCDs note); check the
  contact side (the drawing marks it) before choosing top or bottom contact.
- Pins: VCC on 3 and 29 (OLED panel supply, about 12 to 15 V: verify the panel's VCC range on its
  full datasheet), VDD/VDDIO/VCI logic, IREF, VCOMH, VSL, VLSS caps. Interface select BS0/BS1.
- Frame: X 0..88 left to right, Y 0..27.8 with the FPC edge at Y 0, Z 0 = viewing face, panel
  toward +Z (0..2.15), FPC folded behind it (Z 2.15..2.45, fingers to 2.95).
- Check on arrival: thickness, FPC fold length and finger position, contact side.
