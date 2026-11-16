// The display abstraction. ALL drawing goes through this interface.
// No code outside src/display/ may include or call a display library.
// See docs/adr/0002-display-abstraction.md and 0007.
//
// Art draws on a LOGICAL canvas (64x32 on every driver that can show it, the
// size of the final HUB75 panel). Drivers map the logical canvas to their
// hardware: the OLED scales it 2x, the panel shows it 1:1.
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
constexpr Rgb kWhite{255, 255, 255};

class IDisplay {
public:
    virtual ~IDisplay() = default;

    // Initialise the hardware. Returns false if the display cannot start.
    // The firmware must keep running either way.
    virtual bool begin() = 0;

    // Size of the logical canvas that art draws on.
    virtual uint16_t logicalWidth() const = 0;
    virtual uint16_t logicalHeight() const = 0;

    // False for monochrome displays. Art may pick simpler shapes when false;
    // colour is still passed in and the driver thresholds it to on/off.
    virtual bool isColor() const = 0;

    // (0, 0) is the top-left logical pixel. Out-of-range coordinates are ignored.
    virtual void setPixel(int16_t x, int16_t y, Rgb color) = 0;

    // Set every pixel to black. Does not push to the hardware.
    virtual void clear() = 0;

    // Push the frame buffer to the hardware. Counts as activity (wakes the display).
    virtual void show() = 0;

    // 0 to 100. LED drivers clamp to HS_BRIGHTNESS_CAP_PERCENT; the OLED maps
    // it to its contrast register.
    virtual void setBrightness(uint8_t percent) = 0;

    // Call often from loop(). Drivers use it for idle dimming and similar.
    virtual void tick(uint32_t nowMs) { (void)nowMs; }

    virtual const char* name() const = 0;
};

}  // namespace hs
