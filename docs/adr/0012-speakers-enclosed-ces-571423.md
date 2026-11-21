# 0012: Speakers: enclosed Same Sky CES-571423-28PMB, end-firing through a honeycomb grille

- **Date:** 2026-11-19
- **Status:** Proposed (hole shape superseded by ADR 0017: round holes, not hex)

## Decision

Each end of the case holds one Same Sky CES-571423-28PMB enclosed speaker (57.5 x 23 x
14.85 mm, 8 ohm, 2 W nominal / 3 W max, 100 dB at 2 W / 0.1 m, resonance 700 Hz). It fires
out of the end wall through a 237-hole hex honeycomb (1.8 mm across flats, 2.6 mm pitch), with
an ePTFE acoustic membrane over the whole honeycomb and a 1 mm foam gasket from the speaker
face to the membrane. The end wall is thinned to 1.2 mm in front of the speaker to give the
depth. The wire leads end in a JST SH 2-pin housing that plugs into J4 (left) and J5 (right).

## Why

- An open-back driver (PUI AS04008CO, Fs about 405 Hz) needs a sealed back box. The free
  space at each end gives about 10 to 12 cm3 of net air. With its Vas of 39.8 cm3 that box
  lands at about 770 Hz even with zeolite, with Qtc about 4. The enclosed part starts at
  700 Hz and is already sealed, with no box, zeolite or epoxy coating to build.
- It is the largest enclosed rectangular speaker that fits the end space (no 4 ohm version
  of this size was found; the MAX98357A drives 8 ohm).
- The membrane keeps dust and water out (IP54 target) and lets the case breathe.

## Alternatives

- **Open-back 40 x 20 x 5.8 driver + self-built sealed box + zeolite:** too little volume,
  see above, plus sealing work.
- **CES-303206-240L40-67 (30 x 20 x 6.1, 4 ohm, IP67):** fits easily but its range starts at
  1.28 kHz (resonance 1.6 kHz), so much thinner sound.
- **Slot grille:** replaced by the honeycomb (more open area, 47.9 percent).

## Consequences

- The speakers fill both end corners, so the lid screws sit at (+-66, +-31.8) and the lid
  tongue is interrupted behind each speaker. The gasket channel stays continuous.
- speaker_R sits 1.5 mm under the front Qi2 coil ferrite; speaker_L sits 0.3 mm under the
  GNSS patch. Both are tight; check on the first print.
- The speaker sits 1 mm below the honeycomb centre (the GNSS patch needs the room above the
  left speaker).
- The honeycomb webs are 0.8 mm, under the 1.2 mm minimum wall: they are a deliberate
  exception (2 layers of a 0.4 nozzle line each). Check them on the PLA test print.
- Firmware: bass shelf, virtual bass and a limiter on the S3 (`docs/phases.md`, Phase 6).
- Not confirmed from the datasheet: that the -28PMB connector is a JST SHR-02V-S-B, and the
  lead length. DigiKey lists the -28PMB range as 560 Hz to 20 kHz (the -28PM 700 Hz).
