// STUB, filled in Phase 1b when the 64x32 P2 HUB75 panel arrives.
//
// Plan: wrap ESP32-HUB75-MatrixPanel-DMA behind IDisplay. Add the library to
// lib_deps of the hub75 env, assign the panel pins in config.h and
// docs/hardware/pinout.md, and implement the methods below. Nothing outside
// src/display/ should need to change.
//
// Until then this driver does nothing, so the hub75 build compiles and proves
// the DISPLAY_DRIVER switch works.
#pragma once

#include "config.h"
#include "display/IDisplay.h"
#include "util/Log.h"

namespace hs {

class Hub75Display : public IDisplay {
public:
    bool begin() override {
        LOGW("display", "hub75 driver is a stub (Phase 1b); nothing will be shown");
        return true;
    }
    uint16_t logicalWidth() const override { return HS_HUB75_WIDTH; }
    uint16_t logicalHeight() const override { return HS_HUB75_HEIGHT; }
    bool isColor() const override { return true; }
    void setPixel(int16_t, int16_t, Rgb) override {}
    void clear() override {}
    void show() override {}
    void setBrightness(uint8_t) override {}
    const char* name() const override { return "hub75(stub)"; }
};

}  // namespace hs
