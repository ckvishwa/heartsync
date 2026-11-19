# LiPol Battery LP1160100, 3.7 V 10,000 mAh pouch with PCM (picked)

**Status:** from drawing, VERIFY ON ARRIVAL  
**Part number:** LP1160100 (drawing FD_0110_10, 2020-06-08): 100 +-1 x 60 +-0.5 x 11 +-0.3 mm, PCM, AWG22 UL1007 leads 100 +-3 mm  
**Collected:** 2026-11-19

## Files

- STEP: `lp1160100_from_drawing.step` (MAX envelope 101 x 60.5 x 11.3, PCM end, 4 mm lead stubs)
- Datasheet: `LP1160100_datasheet.pdf`

## Source

- Datasheet: https://www.li-polymer-battery.com/wp-content/uploads/2021/04/LP1160100-3.7V_10000mAh-Datasheet.pdf
- Variant with 10 k NTC and a lead connector: https://www.lipobattery.us/cb-iec62133-un38-3-msds-certified-lp1160100-10000mah-3-7v-37wh-lipo-battery-with-pcm-and-wires-and-10k-ntc-and-molex-51021-0300/

## Licence

Ours (made in this repo by `cad/models/from_drawing.py`). Datasheet PDF: copyright of its maker.

## Notes

- Modelled at the maximum envelope on purpose: the assembly puts the 1.2 mm swell gap above the thickest allowed cell (11.3).
- **This datasheet says NTC: no.** Order it with a 10 k NTC and a JST lead (3 wires, e.g. JST PHR-3) instead of the Molex 51021 listing; the NTC goes to the IP5328P NTC pin.
- Charge 2000 mA max, discharge 4000 mA continuous, cut-off 2.75 V, charge 4.2 V, 0 to 45 deg C charge.
- Frame: X 0..101 with the PCM end at X 0..6, Y centred, Z 0..11.3; leads leave the PCM end at Y +21 / +25 (read off the drawing: verify).
