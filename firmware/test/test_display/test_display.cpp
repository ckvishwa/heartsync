// Native tests for the monochrome canvas (thresholding, 2x scaling, SSD1306
// page layout) and the OLED idle policy. Run: pio test -e native
#include <unity.h>

#include <vector>

#include "art/Animator.h"
#include "art/Sprites.h"
#include "display/IdlePolicy.h"
#include "display/MonoCanvas.h"

namespace {

// IDisplay backed by the real MonoCanvas, like the OLED driver minus the I2C.
class MonoFake : public hs::IDisplay {
public:
    bool begin() override { return true; }
    uint16_t logicalWidth() const override { return hs::MonoCanvas::kWidth; }
    uint16_t logicalHeight() const override { return hs::MonoCanvas::kHeight; }
    bool isColor() const override { return false; }
    void setPixel(int16_t x, int16_t y, hs::Rgb c) override { canvas.setColor(x, y, c); }
    void clear() override { canvas.clear(); }
    void show() override {}
    void setBrightness(uint8_t) override {}
    const char* name() const override { return "mono-fake"; }
    hs::MonoCanvas canvas;
};

int countBits(const std::vector<uint8_t>& buf) {
    int n = 0;
    for (uint8_t b : buf) {
        for (; b != 0; b &= static_cast<uint8_t>(b - 1)) {
            ++n;
        }
    }
    return n;
}

}  // namespace

void setUp() {}
void tearDown() {}

void test_canvas_geometry() {
    TEST_ASSERT_EQUAL(64, hs::MonoCanvas::kWidth);
    TEST_ASSERT_EQUAL(32, hs::MonoCanvas::kHeight);
    TEST_ASSERT_EQUAL(128, hs::MonoCanvas::kPhysWidth);
    TEST_ASSERT_EQUAL(64, hs::MonoCanvas::kPhysHeight);
    TEST_ASSERT_EQUAL(1024, hs::MonoCanvas::kPageBytes);
}

void test_threshold() {
    TEST_ASSERT_FALSE(hs::MonoCanvas::isOn(hs::kBlack));
    TEST_ASSERT_TRUE(hs::MonoCanvas::isOn(hs::kWhite));
    TEST_ASSERT_TRUE(hs::MonoCanvas::isOn(hs::sprites::kHeart.color));    // red heart
    TEST_ASSERT_TRUE(hs::MonoCanvas::isOn(hs::sprites::kAvatarA.color));  // blue avatar
    TEST_ASSERT_FALSE(hs::MonoCanvas::isOn(hs::Rgb{10, 10, 10}));         // near black
    TEST_ASSERT_FALSE(hs::MonoCanvas::isOn(hs::Rgb{0, 0, 255}, 40));      // pure blue, luma 28
    TEST_ASSERT_TRUE(hs::MonoCanvas::isOn(hs::Rgb{0, 0, 255}, 20));
}

void test_set_get_and_clip() {
    hs::MonoCanvas c;
    c.set(0, 0, true);
    c.set(63, 31, true);
    c.set(64, 0, true);  // clipped
    c.set(-1, 5, true);  // clipped
    TEST_ASSERT_TRUE(c.get(0, 0));
    TEST_ASSERT_TRUE(c.get(63, 31));
    TEST_ASSERT_FALSE(c.get(64, 0));
    TEST_ASSERT_EQUAL(2, c.litCount());
    c.set(0, 0, false);
    TEST_ASSERT_EQUAL(1, c.litCount());
    c.clear();
    TEST_ASSERT_EQUAL(0, c.litCount());
}

void test_2x_scaling_makes_2x2_blocks() {
    hs::MonoCanvas c;
    c.set(5, 3, true);
    TEST_ASSERT_TRUE(c.physical(10, 6));
    TEST_ASSERT_TRUE(c.physical(11, 6));
    TEST_ASSERT_TRUE(c.physical(10, 7));
    TEST_ASSERT_TRUE(c.physical(11, 7));
    TEST_ASSERT_FALSE(c.physical(9, 6));
    TEST_ASSERT_FALSE(c.physical(12, 6));
    TEST_ASSERT_FALSE(c.physical(10, 5));
    TEST_ASSERT_FALSE(c.physical(10, 8));
    TEST_ASSERT_FALSE(c.physical(-1, 0));
}

void test_render_pages_layout() {
    hs::MonoCanvas c;
    c.set(0, 0, true);    // physical (0..1, 0..1): page 0, bits 0 and 1
    c.set(63, 31, true);  // physical (126..127, 62..63): page 7, bits 6 and 7
    c.set(2, 4, true);    // physical (4..5, 8..9): page 1, bits 0 and 1
    std::vector<uint8_t> buf(hs::MonoCanvas::kPageBytes, 0xAA);
    c.renderPages(buf.data());
    TEST_ASSERT_EQUAL_HEX8(0x03, buf[0]);
    TEST_ASSERT_EQUAL_HEX8(0x03, buf[1]);
    TEST_ASSERT_EQUAL_HEX8(0x00, buf[2]);
    TEST_ASSERT_EQUAL_HEX8(0x03, buf[128 + 4]);
    TEST_ASSERT_EQUAL_HEX8(0x03, buf[128 + 5]);
    TEST_ASSERT_EQUAL_HEX8(0xC0, buf[7 * 128 + 126]);
    TEST_ASSERT_EQUAL_HEX8(0xC0, buf[7 * 128 + 127]);
    TEST_ASSERT_EQUAL(3 * 4, countBits(buf));  // each logical pixel is 4 physical pixels
}

void test_heart_on_mono_canvas() {
    MonoFake display;
    hs::Animator animator(display);
    animator.showCentered(hs::sprites::kHeart, 2);
    // Red heart thresholds to on: 40 sprite pixels x 4 = 160 logical, x 4 = 640 physical.
    TEST_ASSERT_EQUAL(160, display.canvas.litCount());
    std::vector<uint8_t> buf(hs::MonoCanvas::kPageBytes, 0);
    display.canvas.renderPages(buf.data());
    TEST_ASSERT_EQUAL(640, countBits(buf));
}

void test_idle_policy() {
    using hs::IdleLevel;
    TEST_ASSERT_TRUE(hs::idleLevel(0, 30000, 600000) == IdleLevel::Active);
    TEST_ASSERT_TRUE(hs::idleLevel(29999, 30000, 600000) == IdleLevel::Active);
    TEST_ASSERT_TRUE(hs::idleLevel(30000, 30000, 600000) == IdleLevel::Dim);
    TEST_ASSERT_TRUE(hs::idleLevel(600000, 30000, 600000) == IdleLevel::Off);
    TEST_ASSERT_TRUE(hs::idleLevel(4000000000u, 30000, 0) == IdleLevel::Dim);  // off disabled
    TEST_ASSERT_TRUE(hs::idleLevel(4000000000u, 0, 0) == IdleLevel::Active);   // both disabled
    // millis() wrap: last activity just before the wrap, now just after.
    const uint32_t last = 0xFFFFFF00u;
    const uint32_t now = 0x00000100u;
    TEST_ASSERT_TRUE(hs::idleLevel(now - last, 30000, 600000) == IdleLevel::Active);
}

int main(int, char**) {
    UNITY_BEGIN();
    RUN_TEST(test_canvas_geometry);
    RUN_TEST(test_threshold);
    RUN_TEST(test_set_get_and_clip);
    RUN_TEST(test_2x_scaling_makes_2x2_blocks);
    RUN_TEST(test_render_pages_layout);
    RUN_TEST(test_heart_on_mono_canvas);
    RUN_TEST(test_idle_policy);
    return UNITY_END();
}
