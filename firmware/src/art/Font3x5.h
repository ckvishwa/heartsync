// Tiny 3x5 pixel font for status text on the 64x32 logical canvas.
// Hardware-free: compiles in native tests.
#pragma once

#include <stdint.h>

namespace hs {
namespace font3x5 {

constexpr uint8_t kWidth = 3;
constexpr uint8_t kHeight = 5;
constexpr uint8_t kAdvance = 4;  // glyph width plus one pixel of spacing

// Five rows, top first. Bit 2 is the leftmost pixel, bit 0 the rightmost.
// Lowercase letters map to uppercase; unsupported characters draw as '?'.
const uint8_t* glyph(char c);

// Width in pixels of `text` drawn with this font (no trailing spacing).
uint16_t textWidth(const char* text);

}  // namespace font3x5
}  // namespace hs
