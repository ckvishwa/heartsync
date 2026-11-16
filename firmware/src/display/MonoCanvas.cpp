#include "display/MonoCanvas.h"

#include <string.h>

namespace hs {

static_assert(MonoCanvas::kPhysWidth == HS_OLED_WIDTH, "logical canvas x scale must fill the OLED");
static_assert(MonoCanvas::kPhysHeight == HS_OLED_HEIGHT, "logical canvas x scale must fill the OLED");
static_assert(MonoCanvas::kPhysHeight % 8 == 0, "page layout needs a height that is a multiple of 8");

bool MonoCanvas::isOn(Rgb c, uint8_t threshold) {
    // Integer Rec. 601 luma: weights sum to 256.
    const uint16_t luma = static_cast<uint16_t>((77u * c.r + 150u * c.g + 29u * c.b) >> 8);
    return luma > threshold;
}

void MonoCanvas::clear() { memset(bits_, 0, sizeof(bits_)); }

void MonoCanvas::set(int16_t x, int16_t y, bool on) {
    if (x < 0 || y < 0 || x >= kWidth || y >= kHeight) {
        return;
    }
    const uint16_t i = static_cast<uint16_t>(y) * kWidth + static_cast<uint16_t>(x);
    if (on) {
        bits_[i >> 3] |= static_cast<uint8_t>(1u << (i & 7));
    } else {
        bits_[i >> 3] &= static_cast<uint8_t>(~(1u << (i & 7)));
    }
}

bool MonoCanvas::get(int16_t x, int16_t y) const {
    if (x < 0 || y < 0 || x >= kWidth || y >= kHeight) {
        return false;
    }
    const uint16_t i = static_cast<uint16_t>(y) * kWidth + static_cast<uint16_t>(x);
    return (bits_[i >> 3] >> (i & 7)) & 1u;
}

bool MonoCanvas::physical(int16_t px, int16_t py) const {
    if (px < 0 || py < 0) {
        return false;
    }
    return get(px / kScale, py / kScale);
}

int MonoCanvas::litCount() const {
    int n = 0;
    for (uint8_t b : bits_) {
        for (; b != 0; b &= static_cast<uint8_t>(b - 1)) {
            ++n;
        }
    }
    return n;
}

void MonoCanvas::renderPages(uint8_t* out) const {
    for (uint16_t page = 0; page < kPhysHeight / 8; ++page) {
        for (uint16_t px = 0; px < kPhysWidth; ++px) {
            uint8_t column = 0;
            for (uint8_t bit = 0; bit < 8; ++bit) {
                if (physical(static_cast<int16_t>(px), static_cast<int16_t>(page * 8 + bit))) {
                    column |= static_cast<uint8_t>(1u << bit);
                }
            }
            out[page * kPhysWidth + px] = column;
        }
    }
}

}  // namespace hs
