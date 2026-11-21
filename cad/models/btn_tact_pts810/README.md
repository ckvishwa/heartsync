# C&K PTS810 low tactile switch (MUTE, PWR, VOL-, VOL+, PLAY)

**Status:** KiCad library STEP  
**Part family:** C&K PTS810 SJM 250 SMTR LFS class (4.6 x 3.2 mm, 2.5 mm high, SMT)  
**Collected:** 2026-11-20

## Files

- STEP: `sw_spst_pts810_kicad.step` (KiCad 10 `Button_Switch_SMD.3dshapes/SW_SPST_PTS810.step`)
- Datasheet: not saved. Get it from the C&K site in a browser (their server refuses scripted downloads).

## Why this part

- All five top-edge switches sit over speaker_L: the top wall to the speaker top is only 5.3 mm.
  Strip PCB 0.8 + switch 2.5 + nub 1.1 + TPU flange 0.6 = 5.0 (0.2 clear above the speaker).
- Replaces the PTS645 (4.3 high) and the latching PS-7054DVB (12.4 deep). MUTE is now a firmware
  toggle with a LED (ADR 0017), not a hardware latch.

## Notes

- Envelope from the STEP: 4.6 x 3.2 x 2.5, plunger top 2.5 above the PCB. **Verify the real
  part's height, force and travel against the datasheet before ordering** (the model is a KiCad
  approximation; ~1.0 N class force, short travel: the TPU nub must not preload it).
- CC-BY-SA 4.0 with the KiCad libraries exception: https://www.kicad.org/libraries/license/
