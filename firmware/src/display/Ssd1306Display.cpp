#include "config.h"

#if HS_DISPLAY_IS_SSD1306

#include <Arduino.h>
#include <U8g2lib.h>
#include <Wire.h>
#include <string.h>

#include "display/Ssd1306Display.h"
#include "util/Log.h"

namespace hs {

namespace {

// Full frame buffer (1 KB). The constructor touches no hardware.
U8G2_SSD1306_128X64_NONAME_F_HW_I2C s_oled(U8G2_R0, U8X8_PIN_NONE, HS_PIN_I2C_SCL,
                                           HS_PIN_I2C_SDA);

uint8_t contrastFor(uint8_t percent) {
    return static_cast<uint8_t>((static_cast<uint16_t>(percent) * 255) / 100);
}

// Log every responding address; return 0x3C or 0x3D if present, else 0.
uint8_t scanBus() {
    uint8_t found = 0;
    int count = 0;
    for (uint8_t addr = 0x08; addr < 0x78; ++addr) {
        Wire.beginTransmission(addr);
        if (Wire.endTransmission() == 0) {
            ++count;
            LOGI("i2c", "device at 0x%02X", addr);
            if (found == 0 && (addr == 0x3C || addr == 0x3D)) {
                found = addr;
            }
        }
    }
    LOGI("i2c", "scan done on SDA=%d SCL=%d: %d device(s)", HS_PIN_I2C_SDA, HS_PIN_I2C_SCL, count);
    return found;
}

}  // namespace

bool Ssd1306Display::begin() {
    Wire.begin(HS_PIN_I2C_SDA, HS_PIN_I2C_SCL, HS_OLED_I2C_HZ);
    address_ = scanBus();
    if (address_ == 0) {
        LOGE("display",
             "no SSD1306 at 0x3C or 0x3D. Check wiring: VCC to 3V3, GND to GND, SDA to GPIO %d, "
             "SCL to GPIO %d. Continuing without a display.",
             HS_PIN_I2C_SDA, HS_PIN_I2C_SCL);
        ok_ = false;
        return false;
    }
    s_oled.setI2CAddress(address_ << 1);  // U8g2 takes the 8-bit form
    s_oled.setBusClock(HS_OLED_I2C_HZ);
    if (!s_oled.begin()) {
        LOGE("display", "ssd1306 init failed at 0x%02X", address_);
        ok_ = false;
        return false;
    }
    s_oled.setFlipMode(HS_OLED_FLIP);
    ok_ = true;
    level_ = IdleLevel::Active;
    lastActivityMs_ = millis();
    setBrightness(brightness_);
    clear();
    show();
    LOGI("display", "ssd1306 %ux%u at 0x%02X, logical %ux%u x%u, flip=%d", HS_OLED_WIDTH,
         HS_OLED_HEIGHT, address_, MonoCanvas::kWidth, MonoCanvas::kHeight, MonoCanvas::kScale,
         HS_OLED_FLIP);
    return true;
}

void Ssd1306Display::show() {
    if (!ok_) {
        return;
    }
    canvas_.renderPages(s_oled.getBufferPtr());
    s_oled.sendBuffer();
    lastActivityMs_ = millis();
    if (level_ != IdleLevel::Active) {
        applyLevel(IdleLevel::Active);
    }
}

void Ssd1306Display::setBrightness(uint8_t percent) {
    brightness_ = percent > 100 ? 100 : percent;
    if (ok_ && level_ == IdleLevel::Active) {
        s_oled.setContrast(contrastFor(brightness_));
    }
}

void Ssd1306Display::tick(uint32_t nowMs) {
    if (!ok_) {
        return;
    }
    const IdleLevel level =
        idleLevel(nowMs - lastActivityMs_, HS_OLED_IDLE_DIM_MS, HS_OLED_IDLE_OFF_MS);
    if (level != level_) {
        applyLevel(level);
    }
}

void Ssd1306Display::applyLevel(IdleLevel level) {
    level_ = level;
    switch (level) {
        case IdleLevel::Active:
            s_oled.setPowerSave(0);
            s_oled.setContrast(contrastFor(brightness_));
            break;
        case IdleLevel::Dim:
            s_oled.setPowerSave(0);
            s_oled.setContrast(contrastFor(HS_OLED_DIM_PERCENT));
            LOGI("display", "idle: dimmed");
            break;
        case IdleLevel::Off:
            s_oled.setPowerSave(1);
            LOGI("display", "idle: off");
            break;
    }
}

}  // namespace hs

#endif  // HS_DISPLAY_IS_SSD1306
