# 0013: v1 real parts (cell, OLED, GNSS, LTE) and a bare back with a rubber ring

- **Date:** 2026-11-19
- **Status:** Proposed

## Decision

1. Parts for v1, in the assembly from `cad/models/`:
   - cell: LiPol LP1160100 (10,000 mAh, PCM), ordered with a 10 k NTC and a JST lead;
   - OLED: Newhaven NHD-2.7-12864WDW3;
   - GNSS: Taoglas SGGP.12.4.A.02 on a small ground-plane board;
   - LTE: Molex 212570-0100 flex on the TOP wall.
2. The cell is modelled at its **maximum** envelope (101 x 60.5 x 11.3), and the 1.2 mm swell
   gap is measured above that. The board layer drops from Z 14.4 to Z 13.7.
3. Speakers: the CES-571423-28PMB's mounting ears are cut off flush with the box (no earless
   variant exists). A printed cradle (1.5 mm back plate + two arms that bear on the end wall)
   presses a 1 mm foam pad on the speaker back, loading the face gasket.
4. Back: bare PETG, no fabric and no feet. One continuous TPU ring (4 wide, 2.5 in from the
   edge, R6 corners, 1.0 mm channel, 1.5 proud, own STL) covers four M2 low-head screws; an
   engraved ID block (26 x 11, text in `params.csv`) sits bottom-right seen from behind.
   Fabric stays only on the tray's TOP edge. The ring is a press/stretch fit in its channel
   with no adhesive, so it peels off by hand and the case still opens without heat.
5. Lid 2.2 -> 3.0 mm, screws at (+-66, +-31.7) with 2.2 close-fit holes and no counterbore.

## Why

- The parts were the user's picks; each has a STEP from the maker or a model built from its
  datasheet drawing, so the fit check now runs against real geometry.
- A swell gap measured over the nominal 11.0 cell would shrink to 0.9 mm on a +0.3 cell.
- The ears make the speaker 82.5 mm long; the case is 68.1 mm wide inside.
- In a 2.2 lid, the 1.0 ring channel and the 0.8 gasket channel leave 0.4 mm of lid between
  them (0.5 mm diagonally), and the old screw counterbores left 0.45 mm. 3.0 leaves exactly
  1.2 (`min_wall`). With the heads on the ring-channel floor under the ring, no counterbore
  thins the lid. Dropping the back fabric (0.6) and the 1.5 feet keeps the stack at 34.3 mm
  (limit 35).

## Alternatives

- Ring further in (inset 3.4 instead of 2.5) with a 2.2 lid: meets 1.2 but moves the ring off
  the screws and off the user's spec.
- Moving the gasket channel: it must sit under the 2.2 tray wall with a 1.2 land outside, so
  it cannot move inward or outward.
- A shallower gasket channel or a flat gasket: changes the seal design (IP54 target) for 0.8 mm.
- Low-head screws alone: they fix the counterbore section but not the ring-to-gasket section.
- Keeping the ears and turning the speakers: the long axis would have to run along X, which
  breaks the end-firing honeycomb (ADR 0012).

## Consequences

- The Molex 212570 covers 824-960 / 1710-2170 MHz only. If the network needs the 700 MHz LTE-M
  bands, switch to a flex that covers them (Linx ANT-5GLFPC1-UFL-100 fits the same spot; see
  `cad/models/open_parts.md`).
- The fit check lists 36 clashing pairs with these parts (handoff). Most go away with the three
  board plans in `docs/hardware/board-plans.md`; the latching mute, the OLED module against the
  left speaker, the bracket and the H3 boss, and the Wi-Fi antenna touching the OLED need layout
  moves.
- Ear-cutting is a manual step on every speaker; the cradle and ring are two more prints (PETG,
  TPU).
- The SGGP patch needs a ground-plane board (modelled 16 x 13 x 1.0); it overlaps the left
  speaker by 0.7 mm in Z.
