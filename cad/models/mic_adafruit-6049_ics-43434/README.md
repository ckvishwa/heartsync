# Adafruit 6049 I2S MEMS microphone breakout, ICS-43434 (option A, recommended)

**Status:** official STEP (open part, candidate)  
**Part number:** Adafruit product 6049 (TDK ICS-43434, I2S, 16.51 x 12.70 mm)  
**Collected:** 2026-11-19

## Files

- STEP: `adafruit_6049_ics-43434.step`
- Datasheet: `adafruit_6049_guide.pdf` (Adafruit learn guide: pinout and dimensions)

## Source

- Product: https://www.adafruit.com/product/6049
- STEP: https://github.com/adafruit/Adafruit_CAD_Parts/tree/main/6049%20I2S%20MEMS%20Microphone
- ICS-43434 datasheet: https://invensense.tdk.com/wp-content/uploads/2016/02/DS-000069-ICS-43434-v1.2.pdf (the TDK site returned a web page instead of the PDF; not saved)

## Licence

MIT (the Adafruit_CAD_Parts repository LICENSE).

## Notes

- Replaces the INMP441, which TDK has discontinued. The ICS-43434 is its I2S successor with the same interface.
- Bottom-port mic: the sound hole goes through the PCB, so the board's underside faces the front-wall hole. STEP frame: PCB Z 0..1.5, mic on top at X 7.0..9.5, Y 5.5..8.8.
