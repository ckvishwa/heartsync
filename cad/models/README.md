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
| Mic option A: Adafruit 6049 (ICS-43434) | `mic_adafruit-6049_ics-43434` | Adafruit official (MIT) | yes (learn guide) |
| Light option A: Adafruit 5378 (VEML7700) | `light_adafruit-5378_veml7700` | Adafruit official (MIT) | yes (Vishay sensor datasheet) |

Still stand-ins in the assembly (no part chosen, or no model published): 10,000 mAh cell,
SIM7080G board, LTE flex antenna, GNSS patch, USB-C PD board, Qi2 coil and TX board. See
`open_parts.md`.

## Rebuilding the drawing models

`from_drawing.py` is a Fusion 360 script. It opens its own new document, builds every
`*_from_drawing` / `*_from_params` model from the dimensions written in it, exports the STEP
files into these folders, and closes the document without saving. Change a dimension there
(never in an exported STEP), then rerun it. Each function's docstring gives the part's frame
(origin and axes) and the datasheet figure used.

## What the real models changed (for the assembly swap)

The swap into `cad/fusion/heartsync_assembly.py` and the fit check are **not done yet**:
another session was rewriting that script when this library was built (it landed as
`6abad791`). Known differences against the stand-ins in that commit, from the models alone:

- Speaker: 82.5 mm long with its mounting ears (box 57.5); the case is 68.1 mm wide inside.
- FlexPIFA: the cable leaves the folded short end, not a long side; only 17 of the 40 mm
  is 2.5 thick.
- Latching mute button: case 7 deep plus a 5.4 knob (12.4 released) against a 4.2 deep
  stand-in body.
- Tactile switches: 6 x 6 body, 4.3 to the plunger top (stand-in 6 x 3.5 x 6).
- OLED (option A): 82 x 47.5 x 6.7 module instead of 73 x 41.9 x 1.8 glass.
- Mic and light sensor (option A): 16.5 x 12.7 and 25.4 x 17.8 boards against 8 x 8 and
  7 x 7 stand-ins; the right-angle light board stands 17.8 mm deep.

## Licences

Vendor files keep their makers' terms (each README says which). Several have no
redistribution grant (Same Sky, Amphenol, Newhaven), so keep this repository private.
KiCad library models are CC-BY-SA 4.0 with the KiCad exception; Adafruit models are MIT;
`*_from_drawing` models are ours.
