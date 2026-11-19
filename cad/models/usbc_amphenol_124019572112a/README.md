# Amphenol 124019572112A waterproof USB-C receptacle

**Status:** official STEP  
**Part number:** 124019572112A (USB 3.2 Gen1 Type-C, mid-mount, 0.40 mm centre height, dual-row SMT; IPX8 per the product page)  
**Collected:** 2026-11-19

## Files

- STEP: `124019572112a.step` (from `sc12401957_x1.zip`, file `c12401957_X1.stp`)
- Datasheet: not saved, see below

## Source

- Product page: https://www.amphenol-cs.com/product/124019572112a.html
- STEP: https://cdn.amphenol-cs.com/media/wysiwyg/files/3d/sc12401957_x1.zip
- Drawing: https://cdn.amphenol-cs.com/media/wysiwyg/files/drawing/12401957_1.pdf
- Product specification: https://cdn.amphenol-cs.com/media/wysiwyg/files/documentation/ps-susb014.pdf

## Licence

Amphenol website terms; no licence text ships with the file. Keep the repo private.

## Notes

- **Datasheet PDF missing:** Amphenol's CDN refuses scripted downloads, and Chrome opens PDFs in its viewer. Open the drawing link above in a browser and save it here as `12401957_drawing.pdf`.
- Picked over GCT USB4715 (IP67, power only) because GCT's STEP comes only through a PartCommunity generator that needs an account. GCT drawing: https://gct.co/files/drawings/usb4715.pdf
- STEP envelope 7.86 x 12.2 (with flange) x 4.3 mm: X -9.76..-1.90, Y 6.90..19.10, Z -2.15..2.15 (PCB mid-plane near Z 0). It is mid-mount, so the PD board needs a cut-out under it.
- IPX8 covers the receptacle itself. The case still needs a gasket between the receptacle flange and the wall (the assembly has `usb_c_gasket`, 0.8 mm), sized to this part's flange (12.2 wide).
- This is a full USB 3.2 part (24 contacts). For USB 2.0 + PD only, a 16-pin waterproof part would be simpler to route; ask Amphenol for a 2.0 equivalent before ordering.
