# 0017: One flush TPU strip on the top edge, round-hole end grilles with sunk brass trim frames

- **Date:** 2026-11-20
- **Status:** Proposed

## Decision

1. **Top edge:** the five button holes and caps are replaced by one pocket through the top wall,
   X -70.0..-18.4 (51.6 wide), 9.2 high, icon centre line Z 19.7. A 2 mm tray rib between VOL- and
   VOL+ splits it into two windows (29.96 and 19.64 mm, the longest unsupported bridge when the
   tray prints front-down). One TPU strip fills both windows, face flush with the fabric, and stays
   one piece: its 0.6 inner flange runs continuous behind the rib. The fabric net has two matching
   openings with sealed edges, the rib stays under the fabric.
2. **Keys:** five 0.6 raised icons (mic-off, power, minus, plus, play/pause), evenly spread at a
   10.32 pitch on one centre line. A 0.8 groove ring (5.2 ID, 6.8 OD) is cut round each key from
   the inside of the 2.8 strip, leaving a 1.0 skin on the face. A nub under the TPU reaches the
   switch, so a switch can sit off its icon without moving the icon.
3. **Switches:** all five are low C&K PTS810 tactiles (2.5 high), on a 0.8 strip PCB that sits 0.2
   above speaker_L (the top wall is 5.3 mm from the speaker top, so all five may sit over it).
   Every switch is 1.0 above its icon so the strip PCB clears U1 (top Z 18.5). MUTE is a firmware
   toggle with a red LED (0603 on the strip PCB, light well in the strip with a 0.5 skin), not a
   latching switch.
4. **Ends:** the honeycomb becomes 230 round holes per end (23 x 10, dia 1.6, 2.5 square pitch, web
   0.9), all through the 1.2 mm thinned wall. A brass-tone trim frame, **61 x 26.3** outside (Z 1.2..27.5)
   with its opening equal to the grille pocket, is its own body and sits **sunk flush** in a 0.6
   channel in the end wall. The overall length stays 157. The pocket floor moved from Z 1.2 to 1.8 so
   the frame has a 0.6 border below the grille.

## Why

- One strip is one seal instead of five, and reads as a deliberate control panel on the fabric.
- The rib halves the bridge the pocket would otherwise need; a strip in one piece keeps one seal.
- Low switches over the speaker use the 5.3 mm between the top wall and speaker_L, so the keys are
  evenly spaced instead of squeezed into the right half.
- Round holes print cleanly horizontally and keep a 0.9 web (honeycomb webs were 0.8).
- A sunk frame hides the grille cut edges without adding length.

## Alternatives

- Pocket at X -74.2..-22.6: its left 4 mm lies in the 6 mm corner radius, so the flat strip would
  stand proud there (the pocket starts at -70 instead).
- Keep the latching mute: it is 12.4 deep and cannot sit over the speaker, which crowded the icons
  into the right half of the strip.
- Raised trim frames: simple, but they added 1.2 to the overall length.

## Consequences

- **The frame is 26.3 high, not 27:** with 27 (Z 0.5..27.5) the channel left a 0.45 mm lip at the
  open edge of the tray. 1.2 mm of wall now stays below the channel.
- **Bridge lengths are 29.96 and 19.64 mm, not two 25 mm bridges:** the rib sits between VOL- and
  VOL+, off the pocket centre. Move the rib to X -44.2 only if the icon order or pitch changes.
- **The hardware mic cut-off is gone.** Mute is a firmware toggle: `docs/voice-persona.md` no longer
  claims a hardware mic cut. Option: the switch sets a flip-flop that gates the mic supply.
- New firmware pins (not assigned): MIC_MUTE_BTN, MUTE_LED. Update `firmware/include/config.h` and
  `docs/hardware/pinout.md` together.
- Verify on arrival: the real PTS810 height (2.5), force and travel; the nub must not preload it.
- Test print: Ø1.6 horizontal holes, 0.45 icon features, 0.8 groove rings, strip stiffness (95A, 2.8
  thick with grooves), the 30 mm bridge over the rib window, LED light through the 0.5 skin
  (natural or translucent TPU).
- ADR 0012's honeycomb is superseded for the hole shape; its speaker and membrane choices stand.
