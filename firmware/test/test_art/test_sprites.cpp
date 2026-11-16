// Native tests for sprites and drawing. Run: pio test -e native
#include <unity.h>

#include <vector>

#include "art/Animator.h"
#include "art/Font3x5.h"
#include "art/Sprites.h"
#include "display/IDisplay.h"

namespace {

// In-memory IDisplay. This is the point of the abstraction: art code is
// testable with no LED hardware.
class FakeDisplay : public hs::IDisplay {
public:
    FakeDisplay(uint16_t w, uint16_t h) : w_(w), h_(h), pixels_(w * h, hs::kBlack) {}
    bool begin() override { return true; }
    uint16_t logicalWidth() const override { return w_; }
    uint16_t logicalHeight() const override { return h_; }
    bool isColor() const override { return true; }
    void setPixel(int16_t x, int16_t y, hs::Rgb c) override {
        if (x < 0 || y < 0 || x >= w_ || y >= h_) {
            return;
        }
        pixels_[y * w_ + x] = c;
    }
    void clear() override { pixels_.assign(pixels_.size(), hs::kBlack); }
    void show() override { ++shows; }
    void setBrightness(uint8_t) override {}
    const char* name() const override { return "fake"; }

    hs::Rgb at(int x, int y) const { return pixels_[y * w_ + x]; }
    int lit() const {
        int n = 0;
        for (const auto& p : pixels_) {
            n += (p != hs::kBlack) ? 1 : 0;
        }
        return n;
    }
    int shows = 0;

private:
    uint16_t w_, h_;
    std::vector<hs::Rgb> pixels_;
};

int countSet(const hs::Sprite& s) {
    int n = 0;
    for (int y = 0; y < s.height; ++y) {
        for (int x = 0; x < s.width; ++x) {
            n += hs::spritePixel(s, x, y) ? 1 : 0;
        }
    }
    return n;
}

}  // namespace

void setUp() {}
void tearDown() {}

void test_heart_size_and_pixel_count() {
    const hs::Sprite& heart = hs::sprites::kHeart;
    TEST_ASSERT_EQUAL(8, heart.width);
    TEST_ASSERT_EQUAL(8, heart.height);
    TEST_ASSERT_EQUAL(40, countSet(heart));
}

void test_heart_shape() {
    const hs::Sprite& heart = hs::sprites::kHeart;
    // The notch between the two lobes, and the corners, are empty.
    TEST_ASSERT_FALSE(hs::spritePixel(heart, 0, 0));
    TEST_ASSERT_TRUE(hs::spritePixel(heart, 1, 0));
    TEST_ASSERT_FALSE(hs::spritePixel(heart, 3, 0));
    TEST_ASSERT_FALSE(hs::spritePixel(heart, 4, 0));
    TEST_ASSERT_TRUE(hs::spritePixel(heart, 6, 0));
    // The point at the bottom.
    TEST_ASSERT_TRUE(hs::spritePixel(heart, 3, 6));
    TEST_ASSERT_TRUE(hs::spritePixel(heart, 4, 6));
    TEST_ASSERT_FALSE(hs::spritePixel(heart, 2, 6));
    // Bottom row is empty.
    for (int x = 0; x < 8; ++x) {
        TEST_ASSERT_FALSE(hs::spritePixel(heart, x, 7));
    }
}

void test_heart_is_symmetric() {
    const hs::Sprite& heart = hs::sprites::kHeart;
    for (int y = 0; y < heart.height; ++y) {
        for (int x = 0; x < heart.width; ++x) {
            TEST_ASSERT_EQUAL(hs::spritePixel(heart, x, y),
                              hs::spritePixel(heart, heart.width - 1 - x, y));
        }
    }
}

void test_sprite_pixel_out_of_range_is_unset() {
    const hs::Sprite& heart = hs::sprites::kHeart;
    TEST_ASSERT_FALSE(hs::spritePixel(heart, -1, 1));
    TEST_ASSERT_FALSE(hs::spritePixel(heart, 8, 1));
    TEST_ASSERT_FALSE(hs::spritePixel(heart, 1, -1));
    TEST_ASSERT_FALSE(hs::spritePixel(heart, 1, 8));
}

void test_draw_heart_on_small_display() {
    FakeDisplay display(8, 8);
    hs::Animator animator(display);
    animator.showCentered(hs::sprites::kHeart);
    TEST_ASSERT_EQUAL(40, display.lit());
    TEST_ASSERT_EQUAL(1, display.shows);
    TEST_ASSERT_TRUE(display.at(1, 0) == hs::sprites::kHeart.color);
    TEST_ASSERT_TRUE(display.at(0, 0) == hs::kBlack);
}

void test_draw_heart_centered_on_panel_size() {
    // Same art code on the future 64x32 panel: no rewrite, just centred.
    FakeDisplay display(64, 32);
    hs::Animator animator(display);
    animator.showCentered(hs::sprites::kHeart);
    TEST_ASSERT_EQUAL(40, display.lit());
    // Top-left of the sprite lands at (28, 12).
    TEST_ASSERT_TRUE(display.at(29, 12) == hs::sprites::kHeart.color);
    TEST_ASSERT_TRUE(display.at(28, 12) == hs::kBlack);
}

void test_draw_clips_at_edges() {
    FakeDisplay display(8, 8);
    hs::Animator animator(display);
    animator.drawSprite(hs::sprites::kHeart, 6, 0);  // mostly off the right edge
    TEST_ASSERT_TRUE(display.lit() > 0);
    TEST_ASSERT_TRUE(display.lit() < 40);
    animator.drawSprite(hs::sprites::kHeart, -20, -20);  // fully off: must not crash
}

void test_heart_at_2x_on_logical_canvas() {
    // The bench OLED and the final panel both expose a 64x32 logical canvas.
    FakeDisplay display(64, 32);
    hs::Animator animator(display);
    animator.showCentered(hs::sprites::kHeart, 2);
    TEST_ASSERT_EQUAL(40 * 4, display.lit());
    // 16x16 heart centred: top-left at (24, 8). Sprite pixel (1, 0) covers (26..27, 8..9).
    TEST_ASSERT_TRUE(display.at(26, 8) == hs::sprites::kHeart.color);
    TEST_ASSERT_TRUE(display.at(27, 9) == hs::sprites::kHeart.color);
    TEST_ASSERT_TRUE(display.at(25, 8) == hs::kBlack);  // sprite pixel (0, 0) is empty
}

void test_fit_scale() {
    FakeDisplay panel(64, 32);
    TEST_ASSERT_EQUAL(4, hs::Animator(panel).fitScale(hs::sprites::kHeart));
    FakeDisplay matrix(8, 8);
    TEST_ASSERT_EQUAL(1, hs::Animator(matrix).fitScale(hs::sprites::kHeart));
}

void test_font_glyphs() {
    TEST_ASSERT_EQUAL_PTR(hs::font3x5::glyph('A'), hs::font3x5::glyph('a'));
    TEST_ASSERT_EQUAL_PTR(hs::font3x5::glyph('?'), hs::font3x5::glyph('~'));
    TEST_ASSERT_EQUAL(0, hs::font3x5::textWidth(""));
    TEST_ASSERT_EQUAL(3, hs::font3x5::textWidth("H"));
    TEST_ASSERT_EQUAL(7, hs::font3x5::textWidth("HI"));
}

void test_draw_text() {
    FakeDisplay display(64, 32);
    hs::Animator animator(display);
    const hs::Rgb white{255, 255, 255};
    TEST_ASSERT_EQUAL(3, animator.drawText("I", 0, 0, white));
    // 'I' is ###, .#., .#., .#., ###: 9 pixels.
    TEST_ASSERT_EQUAL(9, display.lit());
    TEST_ASSERT_TRUE(display.at(0, 0) == white);
    TEST_ASSERT_TRUE(display.at(0, 1) == hs::kBlack);
    TEST_ASSERT_TRUE(display.at(1, 2) == white);
}

void test_test_screen_has_border_heart_and_text() {
    FakeDisplay display(64, 32);
    hs::Animator animator(display);
    animator.showTestScreen("OK");
    TEST_ASSERT_EQUAL(1, display.shows);
    // Border corners and edges.
    TEST_ASSERT_TRUE(display.at(0, 0) != hs::kBlack);
    TEST_ASSERT_TRUE(display.at(63, 31) != hs::kBlack);
    TEST_ASSERT_TRUE(display.at(32, 0) != hs::kBlack);
    TEST_ASSERT_TRUE(display.at(0, 16) != hs::kBlack);
    // Heart at 2x with top-left (24, 3): sprite pixel (1, 0) lands at (26, 3).
    TEST_ASSERT_TRUE(display.at(26, 3) == hs::sprites::kHeart.color);
    // Text rows 25..29 have lit pixels inside the border.
    int textLit = 0;
    for (int y = 25; y < 30; ++y) {
        for (int x = 1; x < 63; ++x) {
            textLit += display.at(x, y) != hs::kBlack ? 1 : 0;
        }
    }
    TEST_ASSERT_TRUE(textLit > 0);
}

void test_draw_rect_outline() {
    FakeDisplay display(8, 8);
    hs::Animator animator(display);
    animator.drawRect(0, 0, 8, 8, hs::Rgb{1, 2, 3});
    TEST_ASSERT_EQUAL(28, display.lit());  // 8 * 4 - 4 shared corners
    TEST_ASSERT_TRUE(display.at(3, 3) == hs::kBlack);
}

int main(int, char**) {
    UNITY_BEGIN();
    RUN_TEST(test_heart_size_and_pixel_count);
    RUN_TEST(test_heart_shape);
    RUN_TEST(test_heart_is_symmetric);
    RUN_TEST(test_sprite_pixel_out_of_range_is_unset);
    RUN_TEST(test_draw_heart_on_small_display);
    RUN_TEST(test_draw_heart_centered_on_panel_size);
    RUN_TEST(test_draw_clips_at_edges);
    RUN_TEST(test_heart_at_2x_on_logical_canvas);
    RUN_TEST(test_fit_scale);
    RUN_TEST(test_font_glyphs);
    RUN_TEST(test_draw_text);
    RUN_TEST(test_test_screen_has_border_heart_and_text);
    RUN_TEST(test_draw_rect_outline);
    return UNITY_END();
}
