// Built-in sprites as 1-bit-per-pixel bitmaps with one colour each.
// Rows are packed MSB first: bit 7 of the first byte is the leftmost pixel.
// Each row takes ceil(width / 8) bytes.
//
// Hardware-free: compiles in native tests. Generate new sprites from PNGs with
// tools/pixel2header.py.
#pragma once

#include <stdint.h>

#include "display/IDisplay.h"

namespace hs {

struct Sprite {
    uint8_t width;
    uint8_t height;
    const uint8_t* rows;
    Rgb color;
};

constexpr uint8_t spriteRowBytes(const Sprite& s) { return static_cast<uint8_t>((s.width + 7) / 8); }

// True if the pixel at (x, y) is set. Out-of-range coordinates are not set.
constexpr bool spritePixel(const Sprite& s, int16_t x, int16_t y) {
    return x >= 0 && y >= 0 && x < s.width && y < s.height &&
           ((s.rows[y * spriteRowBytes(s) + x / 8] >> (7 - (x % 8))) & 1) != 0;
}

namespace sprites {

// .##..##.
// ########
// ########
// ########
// .######.
// ..####..
// ...##...
// ........
inline constexpr uint8_t kHeartRows[8] = {0x66, 0xFF, 0xFF, 0xFF, 0x7E, 0x3C, 0x18, 0x00};
inline constexpr Sprite kHeart{8, 8, kHeartRows, Rgb{255, 0, 40}};

// Placeholder avatars. Replace with real ones in Phase 1 (docs/phases.md).
// ..####..
// .######.
// ##.##.##
// ########
// ########
// #.####.#
// .#....#.
// ..####..
inline constexpr uint8_t kAvatarARows[8] = {0x3C, 0x7E, 0xDB, 0xFF, 0xFF, 0xBD, 0x42, 0x3C};
inline constexpr Sprite kAvatarA{8, 8, kAvatarARows, Rgb{80, 160, 255}};

// .######.
// ########
// ##.##.##
// ########
// ##....##
// ###..###
// .######.
// ..#..#..
inline constexpr uint8_t kAvatarBRows[8] = {0x7E, 0xFF, 0xDB, 0xFF, 0xC3, 0xE7, 0x7E, 0x24};
inline constexpr Sprite kAvatarB{8, 8, kAvatarBRows, Rgb{255, 170, 60}};

}  // namespace sprites
}  // namespace hs
