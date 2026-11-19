# Real-parts library

3D models of the bought parts for the HeartSync digital clone, one folder per part:
`cad/models/<part>/` holds the STEP file, the datasheet or drawing PDF, and a README
(source URL, part number, date collected, licence, notes). No guessed boxes: a model is
either the maker's own STEP, a KiCad library model built from the maker's drawing, or a model
we built from the datasheet drawing (`*_from_drawing.step`, flagged **verify on arrival**).

Collected 2026-11-19. Open parts (not chosen yet) and their options are in
[`open_parts.md`](open_parts.md).

## Parts

| Part | Folder | Model source | Datasheet in folder |
|---|---|---|---|
| ESP32-S3-WROOM-1U-N16R8 | `esp32-s3-wroom-1u-n16r8` | Espressif (linked: `Hardware/heartsync_kicad/3dmodels`) | yes |
| Same Sky CES-571423-28PMB speaker | `speaker_ces-571423-28pmb` | Same Sky official | yes |
| Ezurio FlexPIFA 001-0014 | `flexpifa_001-0014` | **from drawing, verify** | yes |
| JST SH SM02/04/05/06/07B-SRSS-TB | `jst_sh` | KiCad library | yes (series catalogue) |
| JST SHR-02/04/05/06/07V-S-B | `jst_sh` | **from drawing, verify** | yes (series catalogue) |
| Amphenol 124019572112A waterproof USB-C | `usbc_amphenol_124019572112a` | Amphenol official | **no** (CDN blocks scripts; save from a browser) |
| G-Switch PS-7054DVB-6PL 7 x 7 latching button | `btn_latch_ps-7054dvb-6pl` | **from drawing, verify** | yes |
| C&K PTS645SM43SMTR92 tactile (x4) | `btn_tact_pts645sm43smtr92` | KiCad library | **no** (C&K returns 403; save from a browser) |
| Mill-Max 0906-2 pogo pin (dock) | `pogo_millmax_0906-2` | **from drawing, verify** | yes (catalogue page) |
| Pogo target pad (device, our part) | `pogo_pad` | from `params.csv` | n/a |
| Dock magnet 6 x 2 mm | `magnet_6x2` | **from drawing, verify** | no (supplier has no PDF) |
| OLED option A: NHD-2.7-12864WDW3 | `oled_nhd-2.7-12864wdw3` | Newhaven official | yes |
| OLED option B: NHD-3.12-25664UCW2 | `oled_nhd-3.12-25664ucw2` | Newhaven official | yes |
| OLED (picked): bare 3.12 in SSD1322 panel, WEX025664B | `oled_wex025664b_panel_312` | **from drawing, verify** (FPC folded) | yes (outline drawing) |
| Mic option A: Adafruit 6049 (ICS-43434) | `mic_adafruit-6049_ics-43434` | Adafruit official (MIT) | yes (learn guide) |
| Light option A: Adafruit 5378 (VEML7700) | `light_adafruit-5378_veml7700` | Adafruit official (MIT) | yes (Vishay sensor datasheet) |
| Cell (picked): LiPol LP1160100 | `cell_lipol_lp1160100` | **from drawing, verify** (max envelope) | yes |
| GNSS (picked): Taoglas SGGP.12.4.A.02 | `gnss_taoglas_sggp.12.4.a.02` | **from drawing, verify** | yes |
| LTE flex (picked): Molex 212570-0100 | `lte_molex_212570-0100` | Molex official (TraceParts) | yes (sales drawing) |

In the assembly (`REAL` in `cad/fusion/heartsync_assembly.py`): all of these except the JST
housings, the dock pogo pin and both Newhaven OLED modules; since the 2026-11-19 pass the Adafruit
mic and light boards are replaced by our front board (phase 4). Still stand-ins (no part chosen,
or no model published): Qi coil and TX board, LRA. Our own boards (front board, power board,
carrier rev B tab, button strip, mute board, pogo board, touch strip, GNSS ground plane) are
outlines with their main parts. See `open_parts.md` and `docs/hardware/board-plans.md`.

## Rebuilding the drawing models

`from_drawing.py` is a Fusion 360 script. It opens its own new document, builds every
`*_from_drawing` / `*_from_params` model from the dimensions written in it, exports the STEP
files into these folders, and closes the document without saving. Change a dimension there
(never in an exported STEP), then rerun it. Each function's docstring gives the part's frame
(origin and axes) and the datasheet figure used.

## Using a model in the assembly

Add it to `REAL` in `cad/fusion/heartsync_assembly.py` with the file's bounding box as
measured in Fusion, then place it with `place_step(name, key, axes, local_ref, world_ref)`:
`axes` gives the world direction of the file's X, Y and Z, and the local reference point
lands on the world point. The script checks every placement against the expected box and
renames bodies `<name>|<body>` so the fit check can tell parts apart. The fit check result
(every clash with volume and overlap box) is in `docs/handoff.md`.

## Licences

Vendor files keep their makers' terms (each README says which). Several have no
redistribution grant (Same Sky, Amphenol, Newhaven), so keep this repository private.
KiCad library models are CC-BY-SA 4.0 with the KiCad exception; Adafruit models are MIT;
`*_from_drawing` models are ours.
