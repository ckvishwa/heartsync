// Draws sprites, text and shapes onto an IDisplay's logical canvas.
// Hardware-free: compiles in native tests.
// Animations (heartbeat pulse, fades) are added here in Phase 1.
#pragma once

#include <stdint.h>

#include "art/Sprites.h"
#include "display/IDisplay.h"

namespace hs {

class Animator {
public:
    explicit Animator(IDisplay& display) : display_(display) {}

    // Draw set pixels of the sprite with its top-left corner at (x, y), each
    // sprite pixel as a scale x scale block. Unset pixels are left untouched.
    // Pixels off the canvas are clipped.
    void drawSprite(const Sprite& sprite, int16_t x, int16_t y, uint8_t scale = 1);

    // One-pixel rectangle outline.
    void drawRect(int16_t x, int16_t y, int16_t w, int16_t h, Rgb color);

    // Text in the 3x5 font, top-left at (x, y). Returns the width drawn.
    uint16_t drawText(const char* text, int16_t x, int16_t y, Rgb color);

    // Clear, draw the sprite centred at the given scale, and show.
    void showCentered(const Sprite& sprite, uint8_t scale = 1);

    // Largest whole-number scale at which the sprite still fits the canvas.
    uint8_t fitScale(const Sprite& sprite) const;

    // Display test screen: border, heart, and one centred line of text.
    void showTestScreen(const char* text) { showSpriteWithText(sprites::kHeart, text, true); }

    // Sprite (2x on canvases of at least 32x32) near the top, one centred text
    // line at the bottom, optional one-pixel border. Clears and shows.
    void showSpriteWithText(const Sprite& sprite, const char* text, bool border);

private:
    IDisplay& display_;
};

}  // namespace hs
