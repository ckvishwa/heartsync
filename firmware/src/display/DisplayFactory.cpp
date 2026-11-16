// Compile-time display selection. This is the only place that knows which
// driver a build uses. To add a driver, see firmware/CLAUDE.md.
#include "display/DisplayFactory.h"

#include "config.h"

#if HS_DISPLAY_IS_SSD1306
#include "display/Ssd1306Display.h"
#elif HS_DISPLAY_IS_SMALL_LED
#include "display/SmallLedDisplay.h"
#elif HS_DISPLAY_IS_HUB75
#include "display/Hub75Display.h"
#else
#error "Unknown DISPLAY_DRIVER. Use ssd1306, small_led, or hub75."
#endif

namespace hs {

IDisplay& createDisplay() {
#if HS_DISPLAY_IS_SSD1306
    static Ssd1306Display display;
#elif HS_DISPLAY_IS_SMALL_LED
    static SmallLedDisplay display;
#elif HS_DISPLAY_IS_HUB75
    static Hub75Display display;
#endif
    return display;
}

}  // namespace hs
