// Native tests for sprites and drawing. Run: pio test -e native
#include <unity.h>

#include <vector>

#include "art/Animator.h"
#include "art/Sprites.h"
#include "display/IDisplay.h"

namespace {

// In-memory IDisplay. This is the point of the abstraction: art code is
// testable with no LED hardware.
class FakeDisplay : public hs::IDisplay {
public:
    FakeDisplay(uint16_t w, uint16_t h) : w_(w), h_(h), pixels_(w * h, hs::kBlack) {}
    bool begin() override { return true; }
    uint16_t width() const override { return w_; }
    uint16_t height() const override { return h_; }
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

int main(int, char**) {
    UNITY_BEGIN();
    RUN_TEST(test_heart_size_and_pixel_count);
    RUN_TEST(test_heart_shape);
    RUN_TEST(test_heart_is_symmetric);
    RUN_TEST(test_sprite_pixel_out_of_range_is_unset);
    RUN_TEST(test_draw_heart_on_small_display);
    RUN_TEST(test_draw_heart_centered_on_panel_size);
    RUN_TEST(test_draw_clips_at_edges);
    return UNITY_END();
}
