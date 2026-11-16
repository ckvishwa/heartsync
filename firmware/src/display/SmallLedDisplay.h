// Small addressable LED matrix or strip (WS2812B by default), driven by FastLED.
// Geometry, chipset, and pin come from config.h.
// Kept for reference; not the bench display any more (see ADR 0007). Its
// logical canvas is the matrix itself (8x8), so 64x32 art is clipped.
#pragma once

#include "config.h"
#include "display/IDisplay.h"

namespace hs {

class SmallLedDisplay : public IDisplay {
public:
    bool begin() override;
    uint16_t logicalWidth() const override { return HS_MATRIX_WIDTH; }
    uint16_t logicalHeight() const override { return HS_MATRIX_HEIGHT; }
    bool isColor() const override { return true; }
    void setPixel(int16_t x, int16_t y, Rgb color) override;
    void clear() override;
    void show() override;
    void setBrightness(uint8_t percent) override;
    const char* name() const override { return "small_led"; }
};

}  // namespace hs
