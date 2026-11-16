// Draws sprites onto an IDisplay. Hardware-free: compiles in native tests.
// Animations (heartbeat pulse, fades) are added here in Phase 1.
#pragma once

#include <stdint.h>

#include "art/Sprites.h"
#include "display/IDisplay.h"

namespace hs {

class Animator {
public:
    explicit Animator(IDisplay& display) : display_(display) {}

    // Draw set pixels of the sprite with its top-left corner at (x, y).
    // Unset pixels are left untouched. Pixels off the display are clipped.
    void drawSprite(const Sprite& sprite, int16_t x, int16_t y);

    // Clear, draw the sprite centred, and show.
    void showCentered(const Sprite& sprite);

private:
    IDisplay& display_;
};

}  // namespace hs
