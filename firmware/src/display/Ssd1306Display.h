// 0.96 inch 128x64 monochrome I2C OLED (SSD1306), driven by U8g2.
// Art draws on the 64x32 logical canvas; this driver thresholds colour to
// on/off and scales 2x. See docs/adr/0007-oled-bench-display-u8g2.md.
#pragma once

#include "config.h"
#include "display/IDisplay.h"
#include "display/IdlePolicy.h"
#include "display/MonoCanvas.h"

namespace hs {

class Ssd1306Display : public IDisplay {
public:
    bool begin() override;
    uint16_t logicalWidth() const override { return MonoCanvas::kWidth; }
    uint16_t logicalHeight() const override { return MonoCanvas::kHeight; }
    bool isColor() const override { return false; }
    void setPixel(int16_t x, int16_t y, Rgb color) override { canvas_.setColor(x, y, color); }
    void clear() override { canvas_.clear(); }
    void show() override;
    void setBrightness(uint8_t percent) override;
    void tick(uint32_t nowMs) override;
    const char* name() const override { return "ssd1306"; }

    // 7-bit I2C address in use, or 0 if no OLED was found.
    uint8_t i2cAddress() const { return address_; }

private:
    void applyLevel(IdleLevel level);

    MonoCanvas canvas_;
    uint8_t address_ = 0;
    bool ok_ = false;
    uint8_t brightness_ = HS_OLED_CONTRAST_DEFAULT_PERCENT;
    uint32_t lastActivityMs_ = 0;
    IdleLevel level_ = IdleLevel::Active;
};

}  // namespace hs
