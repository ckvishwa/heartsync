// 1-bit logical canvas for monochrome displays, plus the logic that turns it
// into hardware pixels. Hardware-free: compiles in native tests.
//
//   - Colour is thresholded to on/off here, in the driver layer, never in art.
//   - The logical canvas (64x32) is scaled by HS_OLED_SCALE (2) so each logical
//     pixel becomes a 2x2 block on the 128x64 OLED.
//   - renderPages() writes the SSD1306 page layout: 8 pages of 128 bytes, each
//     byte a vertical strip of 8 pixels with the least significant bit on top.
//     U8g2's full frame buffer for the SSD1306 uses the same layout.
#pragma once

#include <stddef.h>
#include <stdint.h>

#include "config.h"
#include "display/IDisplay.h"

namespace hs {

class MonoCanvas {
public:
    static constexpr uint16_t kWidth = HS_LOGICAL_WIDTH;
    static constexpr uint16_t kHeight = HS_LOGICAL_HEIGHT;
    static constexpr uint8_t kScale = HS_OLED_SCALE;
    static constexpr uint16_t kPhysWidth = kWidth * kScale;
    static constexpr uint16_t kPhysHeight = kHeight * kScale;
    static constexpr size_t kPageBytes = static_cast<size_t>(kPhysWidth) * kPhysHeight / 8;

    // Perceived brightness (0..255) above the threshold means the pixel is on.
    static bool isOn(Rgb color, uint8_t threshold = HS_MONO_THRESHOLD);

    void clear();
    void set(int16_t x, int16_t y, bool on);        // out of range: ignored
    void setColor(int16_t x, int16_t y, Rgb color) { set(x, y, isOn(color)); }
    bool get(int16_t x, int16_t y) const;           // out of range: false
    bool physical(int16_t px, int16_t py) const;    // hardware pixel after scaling
    int litCount() const;

    // Write the scaled frame in SSD1306 page layout. `out` holds kPageBytes.
    void renderPages(uint8_t* out) const;

private:
    uint8_t bits_[kWidth * kHeight / 8] = {};
};

}  // namespace hs
