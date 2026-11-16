// The display abstraction. ALL drawing goes through this interface.
// No code outside src/display/ may include or call an LED library.
// See docs/adr/0002-display-abstraction.md.
//
// This header has no hardware dependencies, so it also compiles in native tests.
#pragma once

#include <stdint.h>

namespace hs {

struct Rgb {
    uint8_t r;
    uint8_t g;
    uint8_t b;
};

constexpr bool operator==(const Rgb& a, const Rgb& b) {
    return a.r == b.r && a.g == b.g && a.b == b.b;
}
constexpr bool operator!=(const Rgb& a, const Rgb& b) { return !(a == b); }

constexpr Rgb kBlack{0, 0, 0};

class IDisplay {
public:
    virtual ~IDisplay() = default;

    // Initialise the hardware. Returns false if the display cannot start.
    virtual bool begin() = 0;

    virtual uint16_t width() const = 0;
    virtual uint16_t height() const = 0;

    // (0, 0) is the top-left pixel. Out-of-range coordinates are ignored.
    virtual void setPixel(int16_t x, int16_t y, Rgb color) = 0;

    // Set every pixel to black. Does not push to the hardware.
    virtual void clear() = 0;

    // Push the frame buffer to the hardware.
    virtual void show() = 0;

    // 0 to 100. Drivers clamp to HS_BRIGHTNESS_CAP_PERCENT.
    virtual void setBrightness(uint8_t percent) = 0;

    virtual const char* name() const = 0;
};

}  // namespace hs
