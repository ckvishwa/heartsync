// Small addressable LED matrix or strip (WS2812B by default), driven by FastLED.
// Geometry, chipset, and pin come from config.h.
#pragma once

#include "config.h"
#include "display/IDisplay.h"

namespace hs {

class SmallLedDisplay : public IDisplay {
public:
    bool begin() override;
    uint16_t width() const override { return HS_MATRIX_WIDTH; }
    uint16_t height() const override { return HS_MATRIX_HEIGHT; }
    void setPixel(int16_t x, int16_t y, Rgb color) override;
    void clear() override;
    void show() override;
    void setBrightness(uint8_t percent) override;
    const char* name() const override { return "small_led"; }
};

}  // namespace hs
