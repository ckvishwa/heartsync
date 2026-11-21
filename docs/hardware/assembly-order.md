# HeartSync v1 assembly order

Status: plan for the first PETG build (2026-11-19). Model: `cad/fusion/heartsync_assembly.py`.
Read `docs/hardware/safety.md` first. Brightness stays capped at 25 percent and no LiPo wiring
happens before Phase 8: until then, section 7 runs on a current-limited bench supply in place of
the cell, and **section 8 waits for Phase 8**.

The rule behind the order: **everything hot happens before the cell is near the case** (heat-set
inserts, fabric edge sealing, soldering), and **the cell goes in last**, on the lid, just before
the case closes. The case opens without heat: screws, clips, a press-fit ring and peelable
adhesive only.

## 1. Print and check the parts

1. PLA test print first (`cad/print-profiles/pla-test.md`): tray, lid, bracket, both speaker
   cradles. Check the 0.9 mm grille webs and the round holes, the lid tongue fit (0.15), the bracket pins in the
   carrier holes, the 2.7 mm lens-ledge overhang round the window, and the strip pocket.
2. PETG final (`petg-final.md`): tray front-down, lid outside-down, bracket and cradles flat.
3. TPU (`tpu-bumpers.md`): back ring and top strip.

## 2. Heat-set inserts (before any electronics, long before the cell)

1. Four M2 heat-set inserts into the tray's corner bosses with the soldering iron.
2. Let the tray cool fully. Check that each insert is square and flush.

## 3. Front, outside

1. Qi marking ring into its groove (0.4 proud).
2. Lens gasket (adhesive foam, 1.5 wide) onto the ledge round the window, then the smoked PC lens.
3. Fabric (one piece, FRONT + TOP, `cad/net/heartsync_net.pdf` at 100 %): wrap the front, fold
   down the tuck groove round the lens, fold over the top-front edge, wrap the top edge and its
   corners. Cut and seal the mic and light holes and the key and USB-C openings (heat-seal or
   fray stop: do it now, while no cell is anywhere near).

## 4. Front wall, inside

1. Clear PC window into the light hole; ePTFE membrane over the mic hole.
2. Touch strip into its pocket (1.2 wall in front of it).
3. Display panel face-down on the wall behind the window, FPC folded behind it as delivered.
4. Wi-Fi FlexPIFA (adhesive face on the wall, thick end left), GNSS patch on its ground board,
   LTE flex on the top wall.

## 5. Top edge

1. TPU strip into the two top-wall windows from outside (flush with the fabric, icons up, the rib
   in its slot); its inner flange sits on the wall, PSA ring on the flange edge. Press the brass
   trim frames into the end-wall channels (flush).
2. Button strip (five PTS810 switches and the mute LED) behind it. Both USB-C receptacles onto
   their gaskets.

## 6. Boards

1. Carrier bracket pins into the carrier holes H1 to H4.
2. Front board over the bracket, panel FPC into its connector, front flex to the carrier, three
   M1.6 screws into the front-wall bosses. The carrier now hangs on the bracket pins.
3. Power board in its slot (both USB-C ports in their notches), Qi TX board, Qi coil behind the ring.
4. Speakers into their cradles with the foam pad, face gasket on the membrane.
5. LRA on its fin. Pogo board with the four pads and their seal washers, two M1.6 screws.
   Magnets into their blind pockets.
6. All cables: speaker JST SH, U.FL (Wi-Fi to U1, GNSS and LTE to the carrier tab), button strip,
   mute, touch, dock input and Qi TX to the power board. Stow the cable slack.

## 7. Power checks without the cell (bench supply, current-limited)

1. Feed the power board's cell connector from a bench supply at 3.8 V, 1 A limit.
2. **Pogo pads dead until docked:** with nothing on the pads, all four read 0 V and the dock input
   switch is off. Only the dock's seated signal turns it on.
3. **Charge limit about 90 percent:** the IP5328P charge voltage is strapped to 4.20 V (fallback
   if the ESP32 hangs), and the ESP32 stops charging at 4.08 to 4.10 V (about 90 percent), with
   the MAX17048 percentage as a second check. Check both on the bench with a battery simulator or
   an electronic load before the real cell.
4. Cell NTC input: hot and cold cut-offs (0 and 45 deg C) stop charging and the Qi TX.
5. Qi TX: on only with an input present (USB-C or dock), never from the cell.

## 8. The cell, last (Phase 8 only)

1. On the lid: stretch-release adhesive strips on the cell pad, cell (PCM end at the left, -X),
   insulator on its top face, foam frame round it against the lid ribs. The 1.2 swell gap above
   stays free.
2. Leads (and the NTC lead) out through the notch at the PCM end and along the top channel above
   the side ribs; plug the JST PH into the power board.
3. From here on: **no heat**. No soldering, no heat-set inserts, no heat gun, no hot glue.

## 9. Close

1. Dress the cell leads flat in the top channel, clear of the lid tongue and the gasket channel,
   so closing the lid cannot pinch them.
2. Silicone cord into the lid's gasket channel; a 0.3 silicone washer on each lid screw pad (the
   screw holes are inside the gasket line, so the washer between pad and insert boss closes that
   water path; the pad face drops 0.3 in the next model revision).
3. Lid onto the tray (tongue inside the wall), four M2 low-head screws into the inserts.
4. Press the TPU back ring into its channel over the screw heads.

## Venting

The ePTFE membranes over the speakers and the mic pass air, so slow pressure changes equalise.
If the cell ever vents, the lid (four M2 screws, no adhesive) is the only fast relief: do not
glue or pot it.

## Opening again

Peel the back ring off by hand, remove the four screws, lift the lid with the cell on it, unplug
the cell first. Nothing needs heat.
