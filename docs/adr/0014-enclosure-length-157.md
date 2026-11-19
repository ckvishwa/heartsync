# 0014: Enclosure length 157 mm, front fabric, thinner tray

- **Date:** 2026-11-19
- **Status:** Proposed

## Decision

1. Outer length 152 -> **157 mm**; width 72.5 and the 35 mm thickness limit stay.
2. The FRONT is fabric now (with the TOP edge, one piece); back, bottom and ends stay bare PETG.
3. The tray drops from 29.8 to **29.4 mm** (lid 3.0 unchanged), so the front fabric (0.6) and the
   raised Qi marking ring under it (0.4) fit: stack **34.9 mm** at the ring, 34.5 elsewhere
   (shell 32.4 + fabric + ring + back ring 1.5).
4. The Qi coil moves to X 47.95 so the display's viewing area ends 2.06 mm before the phone zone
   (upright phone 77 wide centred on the coil) and the coil's magnet ring ends 3.05 mm from the
   right end's outer face (0.85 from its inner face).
5. The freed length goes to the ends: speakers 2.5 mm further out each, GNSS patch 5.6 mm from
   the left speaker, power and SIM boards at least 2 mm from the speakers.

## Why

- The 3.12 in panel (ADR 0015) is 88 mm long and starts 2.5 mm from the left end; with 152 mm
  the phone zone and the coil-to-end rule could not both hold.
- At 29.8 the fabric and the raised ring would make the stack 35.3 mm, over the hard limit.
  The 0.4 mm comes out of empty space above the speakers and the boards (inside height 27.2).

## Alternatives

- Keep 152 and a smaller display: drops the user's 3.12 in pick.
- Gold inlay ring flush with a black front (the old design): the user wants fabric and a raised
  ring under it.
- Thinner back ring or lid to make room: the ring (1.5 proud) is the user's spec and the lid is
  already at the 1.2 mm minimum between its two channels.

## Consequences

- The coil-to-end rule is met against the outer face only; the magnet ring is 0.85 mm from the
  end wall's inner face (the speaker sits below it).
- Screws move to X +-68.5 (10 from the ends, as before); every end-related position in the
  assembly follows `body_length`.
- The fabric net is now FRONT + TOP in one piece (`cad/net/`).
- The dock (not built) must follow the new length.
