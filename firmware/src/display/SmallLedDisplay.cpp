#include "config.h"

#if HS_DISPLAY_IS_SMALL_LED

#include <FastLED.h>

#include "display/SmallLedDisplay.h"
#include "util/Log.h"

namespace hs {

namespace {

constexpr uint16_t kNumLeds = HS_MATRIX_WIDTH * HS_MATRIX_HEIGHT;
CRGB s_leds[kNumLeds];

// Map (x, y) to the LED index along the data line.
uint16_t ledIndex(uint16_t x, uint16_t y) {
#if HS_MATRIX_SERPENTINE
    if (y & 1) {
        return y * HS_MATRIX_WIDTH + (HS_MATRIX_WIDTH - 1 - x);
    }
#endif
    return y * HS_MATRIX_WIDTH + x;
}

}  // namespace

bool SmallLedDisplay::begin() {
    FastLED.addLeds<HS_LED_CHIPSET, HS_PIN_LED_DATA, HS_LED_COLOR_ORDER>(s_leds, kNumLeds);
    FastLED.setMaxPowerInVoltsAndMilliamps(HS_LED_SUPPLY_VOLTS, HS_LED_MAX_MILLIAMPS);
    setBrightness(HS_BRIGHTNESS_DEFAULT_PERCENT);
    clear();
    show();
    LOGI("display", "small_led %ux%u on GPIO %d, brightness cap %d%%", (unsigned)HS_MATRIX_WIDTH,
         (unsigned)HS_MATRIX_HEIGHT, HS_PIN_LED_DATA, HS_BRIGHTNESS_CAP_PERCENT);
    return true;
}

void SmallLedDisplay::setPixel(int16_t x, int16_t y, Rgb color) {
    if (x < 0 || y < 0 || x >= HS_MATRIX_WIDTH || y >= HS_MATRIX_HEIGHT) {
        return;
    }
    s_leds[ledIndex(x, y)] = CRGB(color.r, color.g, color.b);
}

void SmallLedDisplay::clear() { fill_solid(s_leds, kNumLeds, CRGB::Black); }

void SmallLedDisplay::show() { FastLED.show(); }

void SmallLedDisplay::setBrightness(uint8_t percent) {
    if (percent > HS_BRIGHTNESS_CAP_PERCENT) {
        percent = HS_BRIGHTNESS_CAP_PERCENT;
    }
    FastLED.setBrightness(static_cast<uint8_t>((static_cast<uint16_t>(percent) * 255) / 100));
}

}  // namespace hs

#endif  // HS_DISPLAY_IS_SMALL_LED
