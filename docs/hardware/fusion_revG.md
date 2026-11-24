# Ansonia rev G in Fusion 360: digital clone, clash list, changes

Built 2026-11-23 by `cad/fusion/ansonia_revG.py` (direct modelling, one run about 2.5 min), from the rev G
net, fit map and BOM (`docs/hardware/fit/*revG*`) and the four rev A boards at commit `36561403`.
**Result (option B, below): 16 clashing part pairs** (592 bodies, 65 parts); the first pass had 18 (MR30 and J7
are gone). The other 16 are the rev G drawings as drawn and stay real until a drawing or board changes.

## Option B: compressed layer used as speaker back volume (2026-11-23)

### Step 1: the stack, measured (Z from the lid's inner face)

| Layer | Z | Thickness | Source |
|---|---|---|---|
| lid | -3.0..0 | 3.0 | |
| foam | 0..1.0 | 1.0 | |
| cell (max envelope) | 1.0..12.3 | 11.3 | |
| insulator + swell gap | 12.3..13.7 | 0.2 + 1.2 | |
| carrier / power board | 13.7..14.7 / 13.7..15.3 | 1.0 / 1.6 | |
| tallest carrier part | to 17.9 | 3.2 | **ESP32-S3-WROOM-1U** (KiCad STEP). Next: JST SH headers 2.96 (STEP), U.FL 2.5 (STEP), EWM104 2.5 (no model: assumed), SIM7080G 2.4 (no model: datasheet) |
| tallest power part, as placed | to 21.8 | 6.5 | **MR30PW-M J4** (no KiCad model: 6.5 read off the Amass drawing), then **PH J7** 6.0 (no model: estimate) |
| tallest power part, MR30 off + J7 as SH | to 18.3 | 3.0 | **SRP7028A inductors L1-L3** (no model: Bourns 3.0 max), then SH J5/J6/J7 2.95 (STEP), USB-C 2.9 above the board (Amphenol STEP, Z 18.2) |
| air | | 1.0 | your rule |
| front layer over the carrier | 27.15..30.3 | 3.15 | OLED panel 2.15 + foam 1.0 |
| front layer over the power board | 27.5..30.3 | 2.8 | Qi ferrite 0.8 + coil 1.0 + magnet ring 1.0 |
| front wall | 30.3..32.0 | 1.7 (was 2.2) | |

- Free air above the carrier: 27.15 - 17.9 - 1.0 = **8.25**. Above the power board under the Qi: 27.5 - 21.8 - 1.0 =
  **4.7** with the MR30 and PH on the board, **8.2** after the change below.
- Lower-profile parts: the MR30 is now off the board and J7 is a JST SH (2.95). The 3.0 inductors carry the
  TPS61088 / IP5356M peaks (7-10 A); 2.0 mm parts with that saturation current are rare, so they stay. The ESP32
  module (3.2) and the USB-C (2.9) have no thinner option in the same footprint.
- **Minimum overall thickness the electronics allow:** 30.8 with the parts as committed (MR30 + PH on the power
  board, 2.2 wall); **26.8** with the MR30 off, J7 as SH and the 1.7 wall (lid 3.0 + 13.7 + 1.6 + 3.0 + 1.0 + 2.8 +
  1.7, the carrier side gives the same 26.75). The Dayton driver (30 tall) is what keeps the shell at 35.0.
- Board standoffs: the board layer stays at Z 13.7 (option B keeps the 30.3 interior). The bracket lost its H1/H2
  posts and bars: chamber L carries H1/H2 bosses down to the carrier; the bracket keeps H3, H4 and the H3-H4 bar.

### Step 2: option B at 35.0 (your choice)

- **Front wall 1.7:** shell 3.0 + 30.3 + 1.7 = **35.0** (37.5 with fabric, Qi marking ring and back ring; see
  safety.md). Lens pocket 0.8 deep leaves **0.9** under the lens ledge, the tuck groove floor **0.7**: the lens
  pocket still works. The touch-strip pocket is now 0.5 deep (1.2 wall kept over the strip) and the strip stands
  0.3 proud inside. Ribs 1.5 x 2.0 on the inner face: a bar above the OLED (Y 19.2..20.6, X -70..13), a bar below
  the OLED FPC fold (Y -13.6..-12.2, X -70..5), and an arc round the Qi magnet ring (dia 57..60, X 15.5..71.3).
  A plain 1.7 PETG plate is (2.2/1.7)^3 = 2.2x as flexible as 2.2; behind the window it is backed by the bonded
  OLED glass, at the Qi by the 2.8 stack. Not measured: press-test the first print.
- **Back-box chambers** (PETG, wall 1.2, sealed, glued to the speaker box's back wall with a 0.5 gasket over a
  window in that wall; inner pillars dia 3 keep the printed floor bridges under 15 mm):

| | Chamber | Air added | Back volume before -> after |
|---|---|---|---|
| L | X -71.3..-26, Y -17..22.5, Z 18.9..27.05 (notched X -37..-26 below Y -8.5 for the OLED FPC drop to J11) | 8.4 cc + 0.4 window | **23.2 -> 32.0 cc** (x1.38) |
| R | X 29..71.3, Y 0.5..30.4 + top-wall band X 33..70.1, Y 30.4..35.4 + bottom band X 29..67, Y -30.3..0.5; Z 19.3..27.0 | 12.3 cc + 0.2 window | **23.2 -> 35.8 cc** (x1.54) |

  "Before" = box cavity + plate opening - magnet - 1.0 cc basket frame (estimate; the Dayton Vas is unknown).
  The 1.2 walls take a lot of an 8 mm layer (inner height 5.85 / 5.3): 1.0 walls would add about 15 %.
  Zeolite: L fits bags up to about 30 x 20 x 5, R up to 30 x 25 x 5 (between the pillars).
- **Clearances of the chambers:** Wi-Fi 6.14, GNSS patch 6.25, GNSS board 5.75, LTE 17.7 (L) / **5.00** (R), BT
  5.20, Qi ferrite **0.50**, coil 1.30, magnet ring 2.30, Qi TX board 0.50, OLED (incl. folded FPC) 0.30, carrier
  parts 1.0 under the floor (0.09 next to the H1/H2 bosses), power parts 1.0, USB-C 1.10, shell 0.40. No clash.
- Left free on purpose: the band X -26..29 over the carrier for the Wi-Fi/GNSS/LTE coax runs to the U.FLs, the
  OLED and e-paper FPCs (J11, J13) and the H3/H4 bracket; the strip Y 22.5..30 over the carrier's top connectors.
  The Wi-Fi coax now runs: PIFA end (-53, -29) -> along Y -20 at Z 20 -> up the middle band to the U.FL (-21, 27),
  about 90 of its 100 mm. BT coax (J17, -50, 19) runs under chamber L's floor (1.7 over the U.FL) to the bottom band.
- **J7 -> JST SH 2-pin** (SM02B-SRSS-TB, 1 A per pin vs about 0.7 A at 4 W / 8 ohm): in CAD only, **the power board
  still has the PH footprint** (board session). Box R is 2.7 from the SH body; its +X cable exit is still blocked by
  the box wall: turn J7 to take the cable from +Y or -Y.
- **MR30 off the power board** (CAD only, **the board still has J4**): 2 x 18 AWG pigtail soldered to TP1/TP2
  (46.8, -13/-8), over the board's bottom edge and back under the board at Z 10.3 into a female MR30; the cell's
  male MR30 mates in the pocket beside the cell. Mated pair assumed 16 x 26.5 x 8 (verify) at X 51..67, Y -30..-3.5,
  Z 0.5..8.5. **Pocket clearance:** cell lead stub 0.50, power-board post (64.5, -1) 0.50, Qi TX board 0.50,
  power-board back-side parts 4.62, magnet (+70) 4.40, BT antenna 8.51. Pigtail 51 mm: 1.3 from the cell end,
  0.39 under the power board. Cell leads (AWG22 per the cell drawing) 20 mm to the male end (coil the rest of the 100 mm), 0.38 over
  clip +50. The X room is the tight one (21 mm between the cell end and the Qi board for a 16 mm pair): a narrower
  pair or the pair along Y with the Qi board moved 2 mm would help. TP1/TP2 on the back side at X >= 48 would let
  the pigtail drop straight down (the back-side keep-out ends at X 47). The power-board posts moved to (50, 10),
  (64.5, -1), (69.5, 30), (56, 31) to free the pocket.

### Safety review of option B (hardware-safety-reviewer, commit 81407abc)

No phase-gate rule broken (CAD and docs only). Open, for the user to decide:

1. **Thickness basis:** safety.md now measures 35.0 on the shell (as asked); `cad/params.csv`
   (`body_thickness_max`), `cad/CLAUDE.md`, ADR 0014 and `docs/prd.md` still count fabric, Qi ring and back ring inside
   the 35, which makes rev G 37.5. Needs an ADR either way. 35.0 nominal leaves no margin for print growth or gasket
   squeeze.
2. **MR30 pair is a hard stop 0.5 from the cell's lead exits**, with nothing holding the cell: a drop drives the PCM
   end into it. The moved post (50, 10) is 1.5 from the cell end face. Needs a soft-lined fence between the cell end
   and the pocket (or the Qi board moved 2 mm) and the real MR30 size.
3. **Genders:** the cell (always live) now carries the male pins. Put the female (shrouded) MR30 on the cell.
   safety.md still says "JST connector on the battery".
4. **Cell leads:** 0.38 over clip arm +50 and 0.6 from its ledge, in the path of every lid close; 80 mm of spare lead
   to coil (not modelled). Fitting a connector to a live cell needs a written procedure (one lead at a time,
   heat-shrink each), or buy the cell with the MR30 and lead length fitted.
5. **Pigtail:** on 4 x 4 SMD pads that can peel; add strain relief and sleeving at the board edge (Y -16). Check
   which half the power board stays with when the lid opens (no service loop yet), and whether the charger puts
   voltage on BAT with USB in and no cell.
6. **Heat:** chamber R boxes the power board in (1.0 over the inductors, 0.5 under the ferrite); PETG softens at
   about 75-80 C. Thermocouple test (USB charge + Qi + full audio) on the cell end, charger IC, inductors, chamber R
   floor and ferrite before trusting it. The cell NTC still cannot be plugged in.
7. **Venting:** the chambers take about 30-35 cc of the case's free air (the outer boxes); no vent yet.
8. **Screws:** H1/H2 now also clamp chamber L, so the back-side M2 heads in the swell gap have one more reason to
   stay: fasten from the front instead.
9. Minor: the cell-lead / cell overlap is whitelisted (start the lead at the stub tip instead); chamber glue must be
   room-temperature cure and not needed to open the case.

## Safety blockers (hardware-safety-reviewer, 2026-11-23)

Read these before the fit problems further down: they touch the cell.

1. **Thickness:** now **35.0** on the shell (front wall 1.7, safety.md updated); 37.5 with fabric, Qi marking ring
   and back ring, which the old HeartSync stack counted inside the 35. Say if the limit should include them.
2. **Swell gap at the carrier screws:** M2 heads at Z 12.4..13.7 over the cell top 12.3 (clash #14). Wafer heads do
   not fix it. Nothing hard may sit in Z 12.5..13.7 over the cell: move H1..H4 off the cell or fasten from the front.
3. **Power-board back-side parts over the cell:** 14 parts 0.32..0.67 above the insulator (check 2). The planned
   keep-out to X 47 leaves only 0.5 past the cell end and nothing stops the cell sliding in X.
4. **Nothing holds the cell:** no cradle or fence is modelled. Hard neighbours: clip arms 1.75 away in Y, the
   e-paper FPC 0.85 (would be pinched against a clip arm), power post (49, -14) about 0.5 from the cell end, LRA rib
   about 4.5. Glue near the cell is not allowed, so it needs a soft-lined cradle.
5. **The cell sits on the e-paper glass**, which spans a through-window with 1.4 of lid under its edge; cell weight,
   drops and swelling press on it through 1 mm EVA. A cracked panel puts glass against the cell: add a rigid plate
   between them or move the panel.
6. **Battery leads:** only two short stubs are modelled; the 180 deg route round the power board (MR30 faces -X,
   away from the cell) was not clash-checked. The cell drawing gives **AWG22 UL1007, 100 mm** leads; the brief says
   18 AWG: pick one. Turning J4 (X 29.5..44.2, entirely over the cell) to face the cell end removes the U-turn and the
   clash with J14 (#8).
7. **Cell NTC:** power J5's cable exits 2.7 mm from the top wall (check 7), so the NTC that stops charging and the Qi
   transmitter on cell temperature cannot be plugged in as placed.
8. **Heat at the cell end:** IP5356M U1 spans X 46.5..52.5 and its inductor L1 X 44..53, i.e. 2.5 over the cell,
   against the BOM rule "hot parts past X 47". The Qi coil covers the cell for 28 mm, 15 above it with ferrite
   between. The BOM says Qi runs from USB only; `Hardware/pcb/README.md` allows 5-10 W from the cell: decide.
9. **No vent** for the gasket-sealed cell cavity (safety.md asks for it to be considered); USB-C sealing is not
   modelled. **No safe way to open:** the pry notch does not reach the seam, so people will pry the long side,
   tool pointing at the cell 5.5 mm inside the wall.
10. Paper checks (not CAD): per the cell README the cell is 4 A continuous discharge and 2 A max charge, but the
    power budget designs for 5 A / 8 A and the IP5356M can charge at 5 A (set it to 2 A or less); the battery
    connector (MR30) disagrees with safety.md ("JST") and the cell README, which still names the IP5328P.

The 1.2 mm swell gap is nominal only: no tolerance stack across posts, bracket and gasket squeeze was done.

## How to rebuild

1. Boards: `bash cad/fusion/export_boards.sh` (default: the last committed placement, `HEAD`; `worktree` uses the
   files on disk). It writes `cad/boards/<board>.step` (device mm, Z 0 = board back face). Then
   `"C:/Program Files/KiCad/10.0/bin/python.exe" cad/fusion/board_standins.py <dir with the .kicad_pcb files>`
   refreshes `standins.json` (boxes for parts without a KiCad 3D model) and `connectors.json` (cable connectors).
2. Fusion, MCP script tool or Scripts and Add-Ins: load `cad/fusion/run_revG.py` and call `go("build")`, then
   `go("exports")` and `go("shots")` (see its docstring). A build opens a **new** document and closes earlier
   unsaved builds of this script. The report goes to `cad/fusion/_out/build_report.txt` + `_clashes.json`
   (git-ignored, rerun to get them).
3. Dimensions: `cad/params_revG.csv` (rev G only; `params.csv` still holds the old 157 mm HeartSync for
   `heartsync_assembly.py`). Positions of bought parts and boards: the `REAL` table and `build_real()`.

The board STEPs are imported as they are, so a placement change is: re-export, rebuild. The open Fusion tab is
**not saved to the cloud**; `cad/exports/revG/ansonia_revG.f3d` is the design file. Say if you want it saved as
"Ansonia rev G" in the Fusion project.

## Outputs

| What | Where |
|---|---|
| Assembly STEP (zipped, 29 MB unzipped) | `cad/exports/revG/ansonia_revG_assembly.step.zip` |
| Fusion design | `cad/exports/revG/ansonia_revG.f3d` |
| 3MF per printed part (oriented for the A1, centred, on Z 0) | `cad/exports/revG/*.3mf`, notes in `exports.txt` |
| Screenshots | `cad/renders/revG/`: `revG_exploded.png`, `revG_section_middle_Y0.png`, `revG_section_speaker_L_X-82.png`, `revG_back_epaper.png`, `revG_iso_front.png` |

| 3MF | Size on the plate | Orientation, supports |
|---|---|---|
| front_shell_PETG | 190 x 76 x 32.9 | front face down, no supports. **But the 0.4 raised Qi ring is then the only thing touching the plate**: print the ring as a separate 0.4 part (or a 0.4 raft / supports under the face). Clip ledges are 2.4 overhangs; USB-C and button windows are short bridges |
| lid_PETG | 190 x 76 x 16.7 | back face down, no supports; bridges 4 (ring channel), 18 (plate recess), 1.5 (cover ledge) |
| speaker_box_L/R_PETG | 29.9 x 66.8 x 18 | back wall down, no supports; the front plate is a 2-3 mm inward ledge (add a 45 deg chamfer) |
| carrier_bracket_PETG | 55 x 38 x 15.6 | carrier side down; bars bridge 16-34 mm at 11 mm height: supports under the bars if they sag |
| button_strip_TPU | 51.4 x 9 x 3.4 | icons up; tree supports under the strip (the nubs hang 1.5 below it) |
| back_ring_TPU | 184.9 x 70.9 x 2.5 | flat, no supports |
| trim_L/R_PLA-silk | 71.2 x 31.2 x 0.6 | flat, no supports (0.8-1.2 wide bars: fragile) |
| signature_plate_PLA-silk | 51.8 x 17.8 x 0.8 | text up, no supports; placeholder text until the scan arrives |
| spk_chamber_L_PETG | 45.3 x 40.0 x 12.4 | top face down, H1/H2 bosses up; floor bridges <= 15 mm between inner pillars; no supports (sealed) |
| spk_chamber_R_PETG | 42.3 x 65.7 x 7.7 | top face down; floor bridges <= 15 mm between inner pillars; no supports (sealed) |

Not printed (bought or cut): lens (smoked PC 81.4 x 23.8 x 1.0), IR window (4.9 x 3.4 PC), e-paper cover
(89.2 x 54.6 x 0.5 PC), gasket cord, ePTFE, foams.

## Check 1: interference, all bodies

Pairwise interference between every two parts whose boxes overlap (one call over all bodies returns nothing:
the Amphenol USB-C model breaks it). Same-part overlaps ignored; 3 expected contacts left out (USB-C legs in the
power board cut-out 0.19 mm3 each, e-paper FPC inside J13). Coordinates in device mm.

| # | Pair | Volume | Overlap (X / Y / Z) | Why |
|---|---|---|---|---|
| 1 | lid (tongue + end hook) x speaker L | 176.9 mm3 | X -92.6..-90.8, Y +-27.9, Z 0.25..5.0 | The driver is 30 tall in a 30.3 cavity with its face at X -92.8 (as drawn), so it stands on the lid's tongue and the end hook (drawn at X 90.8..92.8) |
| 2 | lid x speaker R | 176.9 | mirror of 1 | same |
| 3 | gasket cord x speaker L | 83.3 | X -92.75..-91.65, Y +-27.0, Z 0.5..2.0 | same cause: the seal line runs under the driver flange |
| 4 | gasket cord x speaker R | 83.3 | mirror | same |
| 5 | foam gasket (driver -> box) L x lid tongue | 30.9 | X -90.8..-89.8, Y +-33.4, Z 0.3..2.5 | same cause |
| 6 | same, R | 30.9 | mirror | same |
| 7 | gasket cord x lid end hooks | 22.8 | X +-(91.65..92.6), Y +-4, Z 0.5..2.0 | the drawn hooks stand in the gasket groove: the seal is broken at both hooks |
| ~~8~~ | **fixed in option B (MR30 off the board)**: MR30 plug x nano-SIM J14 (carrier) | 67.9 | X 19.0..27.85, Y -12.8..-3.2, Z 15.3..16.1 | the battery plug mates from -X at X 30, i.e. over the carrier's right edge where J14 sits (plug bottom Z 15.3, J14 top Z 16.1). Plus 31 mm3 with power J4's own courtyard (mating zone, ignore) |
| ~~9~~ | **fixed in option B (J7 as SH, 2.7 clear)**: speaker box R x power J7 (PH speaker connector) | 75.0 | X 71.8..73.15, Y 4.4..13.6, Z 15.3..21.3 | J7 sits at the board edge, under the box's back wall |
| 10 | OLED panel x speaker box L | 68.4 | X -73.0..-71.8, Y -9.9..17.9, Z 28.15..30.2 | the fit map's "0.3 from speaker L" is to the driver (X -73.3); the sealed box adds its 1.5 back wall (to -71.8) |
| 11 | power board x speaker box R | 63.2 | X 71.8..73.0, Y -1..33, Z 13.7..16.9 | board outline to X 73 vs box back wall from 71.8 (incl. C 1206 at X 71.8..72.3 and an 0402) |
| 12 | front shell x speaker L | 5.5 | X -92.3..-91.3, Y +-35, Z 9.6..20.9 | the 70 mm racetrack lobes reach Y +-35 where the R6 corners pull the inner wall in (R 3.8) |
| 13 | front shell x speaker R | 5.5 | mirror | same |
| 14 | cell insulator x 4 carrier screw heads | 4.5 | Z 12.4..12.5 at H1..H4 | M2 low heads (1.3) under the carrier sit in the swell gap: all four holes are over the cell |
| 15 | power board x Qi TX board | 3.1 | X 67.5..69.5, Y -1..0 | TX board drawn at Y 0..-32, board notch only from Y -1 (one 0805 at Y -0.12 too) |
| 16 | GNSS ground board x speaker box L | 1.7 | X -72.0..-71.8, Y -33.4..-22.75 | GNSS board drawn from X -72; the box ends at -71.8 |
| 17 | front sensor board x speaker box L | 1.3 | X -72.0..-71.8, Y 24..33.4 | board outline from X -72 |
| 18 | USB-C 2 x speaker box R | 0.15 | X 71.8..72.15, Y 31.8..32.6 | receptacle flange (12.2 wide) reaches X 72.15 |

Touching only (0 volume): lid / speaker boxes. Expected contacts: USB-C legs in the board cut-outs, e-paper FPC in
J13, cell leads continuing the cell's lead stubs, chamber L's H1/H2 bosses and screws on the carrier.

## Check 2: power board back side vs cell

At commit `36561403` the power board has **14 back-side parts at X < 47** (over the cell): R23, R24, C66, C42, C68,
C43, C74, C65, C73, C17, C67, C14, C20, C11 (0402/0603 at X 35.25..45.5). Their bottoms are Z 12.82..13.17,
i.e. **0.52..0.87 above the cell top (12.3), 0.32..0.67 above the insulator**: the 1.2 swell gap is eaten. The
working copy of `Hardware/pcb/tools/boards.py` (another session, not committed) adds a `cell_under_no_back_parts`
keep-out for X 30..47: re-export and rebuild once that placement is committed. Lowest back-side part overall:
Z 12.82 at X 59..60.6 (not over the cell). Cell to power board (min): 0.51.

## Check 3: boards vs speaker boxes, Qi TX vs box R

| | Min distance |
|---|---|
| Power board vs speaker box R | **overlap 1.2** (#11) |
| Power J7 (PH) vs box R | **overlap 1.35** (#9), C 1206 / 0402 overlap 0.5 / 0.2 |
| USB-C 2 vs box R | **overlap 0.35** (#18) |
| Carrier vs speaker box L | 9.8 |
| Qi TX board vs speaker box R | 2.3 |
| Qi magnet ring (OD 56) vs speaker box R | 0.3 |
| OLED / GNSS board / front sensor vs box L | **overlap 1.2 / 0.2 / 0.2** (#10, #16, #17) |
| Button PCB vs box L | 1.8 |

## Check 4: 5 mm metal clearance round the antennas

| Antenna | Within 5 mm |
|---|---|
| Wi-Fi FlexPIFA (front wall, X -53.1..-11.9 incl. cable stub) | GNSS ground board **3.18**, GNSS patch 4.86 |
| GNSS patch + ground board | Wi-Fi PIFA **3.18** (stub), 4.22, 4.24 |
| LTE flex (top wall, X -14..28) | power board **3.20**, touch strip board **3.85** |
| BT FPC (bottom wall, X 38..64) | Qi TX board **4.95** |

The cell, carrier, magnets and speakers are all more than 5 mm from every antenna. The Wi-Fi and GNSS antennas
are 3.2 mm apart at X -56..-53 (Wi-Fi cable end vs the GNSS ground board).

## Check 5: clips, magnets, pogo pads, hooks, e-paper

- Clip arms (X -50/-10/20/50 +-3, Y +-32.0..33.2, Z 0..5) vs magnet bosses (X +-32/+-70, boss dia 9): nearest is
  clip +50 (X 47..53) vs the +32 boss (to X 36.5): 10.5 mm.
- The lid's nearest metal to the magnets is the tongue, **1.5 mm** below them (tongue top Z 2.5, magnet Z 4..10).
- Clip X -10 vs pogo pad X -12: they overlap in X but are 6.9 apart in Z (clip top Z 5, pad flange from Z 11.8).
- End hooks (|X| 90.8..92.6) vs e-paper pocket (X -60.4..36.4): 30.4 mm (left), 54.4 (right). Clip arms vs the
  pocket edge (Y +-28.22): 3.8. The hooks themselves clash with the drivers and break the gasket (#1, #2, #7).
- Dock (rev I, `dock_i.py`): pogo X +-4/+-12 and magnets X +-32/+-70 match; dock Y 21.7 / 28.5 = device Z 13.8 /
  7.0 with the back ring on the pod (dock Y = 35.5 - device Z). The dock is not modelled in this pass.

## Check 6: e-paper FPC route

Modelled as a 13 x 0.15 strip (assumed position X -10.5..2.5; the real tail position on the panel is not known):
panel bottom edge Y -28.12 -> 0.4 deep groove in the lid face to Y -31.25 -> up beside the cell to Z 15.35 ->
over the carrier into J13 (Y -15.6). **34 mm.** Clearances: cell 0.85, clip arm at X -10 0.75, tongue 2.2,
lid groove 0.05. To open the lid: about 5 mm to clear the tongue and clips, about 40 mm more to lay the lid
beside the shell, so plan a 24 p 0.5 mm extension of 60-80 mm (or a ZIF-to-ZIF jumper) and a fold that stays
outside the cell's footprint. J13's cable side is clear.

## Check 7: cable routes

| Cable | Route, length | Result |
|---|---|---|
| Speaker L (2 w) | box hole (-71.8, 0, 26) -> carrier J4 (-58.7, -7): ~31 mm | J4 exit clear |
| Speaker R (2 w) | box hole (71.8, 0, 26) -> power J7 (68, 9): ~22 mm | option B: J7 as SH is 2.7 from the box, but its +X cable exit still hits the box wall: turn J7 |
| Battery 2 leads (brief 18 AWG, cell drawing AWG22) | cell PCM end (+X, X 46.5..50.5) -> round the power board's bottom edge (Y -16) -> MR30 plug from -X at X 19..30: ~75 mm with a 180 deg turn | first pass: plug hit J14 (#8). Option B: MR30 pair in the pocket beside the cell, see above |
| Haptic | LRA (-65, 0) -> J6 (-50, -14.2): ~41 mm | clear |
| Buttons (6 w) | button PCB (Y 30.6) -> J12 (-38.35, 26.6), cable +Y | **blocked**: 0.6 mm from the carrier edge to the button PCB, the SH plug needs ~4 |
| Front sensor (8 w) | pads (-66.2, 25.4) -> J8 (-56, 26.6), cable +Y | **blocked** by the button PCB (same) |
| Touch strip (2 w) | pads (-17.8, 29.75) -> J7 (-46.5, 26.6): ~47 mm | **blocked** by the button PCB (same) |
| Carrier J1 <-> power J1 (24 p) | facing each other across a 2.05 mm gap (X 27.93 -> 29.98) | **blocked**: two SH plugs do not fit; turn one connector or use a short FFC |
| Power J5 (NTC) | cable +Y from Y 33.1 | **blocked**: 2.7 mm to the top wall |
| Power J6 (Qi TX) | cable +X into the TX board 0.8 mm away | **blocked** for a plug; solder the module wires or turn J6 |
| Carrier J4, J6, J9, J11, J13 | | clear |

## Check 8: mass

**About 475 g** (option B: 464 g modelled, chambers +17 g, MR30 pair 5 g; + ~10 g fabric, glue, wires; first pass 465). Cell 160 (given), front shell 70, lid 37, speakers
2 x 28 (estimate: Dayton weight not found), OLED 14, e-paper 12.5, board stand-ins 12.5, carrier 11, speaker
boxes 2 x 9.3, Qi ferrite/magnet/coil 21, power board 7, back ring 6. PETG at 1.27, solid (no infill): printed at
15-20 % infill the shell parts weigh about 40 g less.

## What I changed or had to decide (the drawings do not say)

- **Haptic size:** Vybronics lists the VLV101040A as **10 x 10 x 4.0** (and as a Z-axis LRA, not X-axis), so it is
  modelled at that size, on a 1 mm pad with a U clip on the lid. Your 10 x 40 x 10 envelope (X -70..-60, Y +-20,
  Z 1..11) was checked too: clear of everything except the clip I added for the small part.
- **Dayton CE70-30P-8:** the spec sheet could not be downloaded (Dayton's link 404s, Parts Express returned an
  empty page). Modelled from the BOM envelope 70 x 30 x 19.5: racetrack flange 2.0 thick (R15 ends), basket
  60 x 20, magnet dia 24, 4 holes dia 3.2 at Y +-29, Z +-8. **Verify on arrival.** Box: sleeve 66.8 x 29.9, wall 1.2,
  back wall 1.5 (X 71.8..73.3 as drawn), front plate with a 62 x 22 opening sealed by 1 mm foam to the flange,
  net air volume about 26 cm3 (room for a zeolite bag beside the magnet), sealed wire hole dia 2.5.
- **Seal:** tongue 2.0 x 2.5 tall, 0.2 fit to the walls, groove 1.6 x 0.95 deep for the 1.5 cord (about 23 %
  squeeze). Clips: arm 6 x 1.2 x 5 inside the tongue, 0.8 hook over a 0.8 ledge (Z 2.7..4.0, 0.6 engagement).
- **Speaker face pocket:** the end wall is thinned to 1.2 over Y +-35.2 so the ePTFE (0.2) and a 0.8 foam pad fit
  between the wall and the driver face at X 92.8. Where that pocket meets the trim channel (|Y| 34.4..35.2) the wall
  is **0.6**: thin for PETG.
- **Trim frame:** 71.2 wide as drawn, but the end face is only flat for |Y| < 32 (R6 corners; the net draws them
  square). At Y +-35.6 the frame stands **1.2 mm proud** of the rounded corner. Shrink it to about 63 wide or
  wrap it round the corner.
- **USB-C:** opening 10.8 x 4.2 (R 2.1) at Z 16.05; with the footprint's 0.25 shift the receptacle face is 0.45
  inside the wall, **2.65 below the outer face, 3.25 below the fabric**. A plug overmold larger than 10.8 x 4.2
  (most are about 12 x 6.5) stops at the surface and leaves only about 3.4 of its 6.65 shell in the receptacle:
  it may not latch. Receptacle to opening: 1.09 clearance all round.
- **E-paper:** pocket 96.8 x 56.4 x 1.1 (0.1 fit), window = active area 86.4 x 51.84 **centred on the panel**: the
  active-area offset was not found (Waveshare's page 404s), so check it on the panel drawing before cutting.
  Cover recess 0.5 deep, 1.5 wider than the window; 1.4 of lid under the panel border. The cell's foam pad lies
  over the panel (0.08 below the lid face): the cell's weight and swelling press on the glass through 1 mm EVA.
- **Carrier bracket:** posts dia 5 at H1..H4 (H1/H4 up to the front wall, H2/H3 to Z 27 under the panel) joined by
  4 x 1.4 bars at Z 25.6..27; M2 self-tappers from the back. How the bracket is fixed to the shell is not drawn
  (glue pads or front-wall inserts at H1/H4). The screw heads clash with the swell gap (#14): see safety blocker 2.
- **Power board:** no holes in the outline, so it rests on 5 lid posts dia 4 (49, -14), (63, -14), (68.5, 2.2),
  (69.5, 30), (56, 31), placed clear of back-side parts. It needs 2-3 M2 holes or clip tabs to be held.
- **Qi stack:** magnet ring 56/44 x 1.0 against the wall, then coil 50/20 x 1.0, then ferrite 50 x 0.8 (Z
  27.5..30.3, as the section). The ring's ID 44 sits over the coil's outer turns (44..50): a N52 ring between coil
  and phone heats and trips FOD. Use a ring with ID >= 51 or move it outside the coil.
- **Pry notch:** modelled as drawn (X 89..91.5, Y 9..15, 2 deep from the back, under the ring). It does not reach
  the seam, so a tool in it cannot lever the lid off the shell.
- **LTE antenna:** Linx ANT-5GLFPC1 has no STEP here: 42 x 18.1 x 0.3 box on the top wall (X -14..28, Z 11.9..30).
- **Parts without a KiCad 3D model** are boxes (courtyard x datasheet height, `cad/boards/standins.json`): SIM7080G,
  nano-SIM, TPS63001, EWM104 (height 2.5 assumed), JST SH 22/24 p, MR30PW-M (6.5 high, verify), JST PH S2B,
  SRP7028A inductors, VQFN-RHL, HTSSOP-28, APDS-9960. Switches PTS645 and the button PCB are boxes too.

## Open, in order of impact

0. The safety blockers at the top (thickness limit, swell gap, cell retention, e-paper under the cell, leads, NTC,
   heat at the cell end, venting, opening).
1. Speakers vs seal: the 30 mm driver leaves no room for the tongue, cord, foam and end hooks at the ends (#1-#7).
   Options: driver face 3 mm further in (needs 3 mm of length or a shorter cell), seal on the speaker box's back
   wall (box becomes part of the wet side), or a lower driver.
2. Right end: power board, J7, USB-C 2 and the board's 0402/1206 parts reach into the speaker box R (#9, #11, #18);
   left end: OLED, GNSS board and front sensor 0.2-1.2 into box L (#10, #16, #17). Pull the board outlines to
   X +-71.6 or move the box back walls out.
3. Cable exits: button PCB blocks J7/J8/J12; carrier J1 and power J1 face each other 2 mm apart; J5, J6 blocked.
4. Battery plug vs nano-SIM (#8) and the lead U-turn.
5. Power board back-side parts over the cell (check 2), screw heads in the swell gap (#14).
6. USB-C recess depth, trim frame corners, 0.6 end-wall band, Qi ring on the print plate, Qi magnet ID.
7. Verify on arrival: Dayton driver, Waveshare active-area offset and FPC tail, MR30 body, EWM104 height.
