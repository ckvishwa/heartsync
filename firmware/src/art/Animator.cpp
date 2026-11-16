#include "art/Animator.h"

namespace hs {

void Animator::drawSprite(const Sprite& sprite, int16_t x, int16_t y) {
    for (int16_t sy = 0; sy < sprite.height; ++sy) {
        for (int16_t sx = 0; sx < sprite.width; ++sx) {
            if (spritePixel(sprite, sx, sy)) {
                display_.setPixel(x + sx, y + sy, sprite.color);
            }
        }
    }
}

void Animator::showCentered(const Sprite& sprite) {
    const int16_t x = (static_cast<int16_t>(display_.width()) - sprite.width) / 2;
    const int16_t y = (static_cast<int16_t>(display_.height()) - sprite.height) / 2;
    display_.clear();
    drawSprite(sprite, x, y);
    display_.show();
}

}  // namespace hs
