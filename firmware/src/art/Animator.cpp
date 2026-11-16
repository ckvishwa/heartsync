#include "art/Animator.h"

#include "art/Font3x5.h"

namespace hs {

namespace {
constexpr Rgb kTextColor{255, 255, 255};
}

void Animator::drawSprite(const Sprite& sprite, int16_t x, int16_t y, uint8_t scale) {
    if (scale == 0) {
        return;
    }
    for (int16_t sy = 0; sy < sprite.height; ++sy) {
        for (int16_t sx = 0; sx < sprite.width; ++sx) {
            if (!spritePixel(sprite, sx, sy)) {
                continue;
            }
            for (uint8_t dy = 0; dy < scale; ++dy) {
                for (uint8_t dx = 0; dx < scale; ++dx) {
                    display_.setPixel(x + sx * scale + dx, y + sy * scale + dy, sprite.color);
                }
            }
        }
    }
}

void Animator::drawRect(int16_t x, int16_t y, int16_t w, int16_t h, Rgb color) {
    if (w <= 0 || h <= 0) {
        return;
    }
    for (int16_t i = 0; i < w; ++i) {
        display_.setPixel(x + i, y, color);
        display_.setPixel(x + i, y + h - 1, color);
    }
    for (int16_t j = 0; j < h; ++j) {
        display_.setPixel(x, y + j, color);
        display_.setPixel(x + w - 1, y + j, color);
    }
}

uint16_t Animator::drawText(const char* text, int16_t x, int16_t y, Rgb color) {
    if (text == nullptr) {
        return 0;
    }
    int16_t cx = x;
    for (const char* p = text; *p != '\0'; ++p) {
        const uint8_t* rows = font3x5::glyph(*p);
        for (int16_t ry = 0; ry < font3x5::kHeight; ++ry) {
            for (int16_t rx = 0; rx < font3x5::kWidth; ++rx) {
                if ((rows[ry] >> (font3x5::kWidth - 1 - rx)) & 1u) {
                    display_.setPixel(cx + rx, y + ry, color);
                }
            }
        }
        cx += font3x5::kAdvance;
    }
    return font3x5::textWidth(text);
}

uint8_t Animator::fitScale(const Sprite& sprite) const {
    if (sprite.width == 0 || sprite.height == 0) {
        return 1;
    }
    const uint16_t sx = display_.logicalWidth() / sprite.width;
    const uint16_t sy = display_.logicalHeight() / sprite.height;
    const uint16_t s = sx < sy ? sx : sy;
    return static_cast<uint8_t>(s == 0 ? 1 : (s > 255 ? 255 : s));
}

void Animator::showCentered(const Sprite& sprite, uint8_t scale) {
    const int16_t w = static_cast<int16_t>(sprite.width * scale);
    const int16_t h = static_cast<int16_t>(sprite.height * scale);
    const int16_t x = (static_cast<int16_t>(display_.logicalWidth()) - w) / 2;
    const int16_t y = (static_cast<int16_t>(display_.logicalHeight()) - h) / 2;
    display_.clear();
    drawSprite(sprite, x, y, scale);
    display_.show();
}

void Animator::showSpriteWithText(const Sprite& sprite, const char* text, bool border) {
    const int16_t w = static_cast<int16_t>(display_.logicalWidth());
    const int16_t h = static_cast<int16_t>(display_.logicalHeight());
    display_.clear();
    if (border) {
        drawRect(0, 0, w, h, kTextColor);
    }

    // Sprite at 2x, centred horizontally, near the top; text line below it.
    const uint8_t scale = (h >= 32 && w >= 32) ? 2 : 1;
    const int16_t sx = (w - sprite.width * scale) / 2;
    drawSprite(sprite, sx, 3, scale);

    const int16_t tx = (w - static_cast<int16_t>(font3x5::textWidth(text))) / 2;
    const int16_t ty = h - 2 - font3x5::kHeight;
    drawText(text, tx, ty, kTextColor);
    display_.show();
}

}  // namespace hs
