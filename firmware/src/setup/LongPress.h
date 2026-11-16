// BOOT button gestures: a short tap or a long hold. Hardware-free (native tests).
//
// GPIO 0 is a strapping pin: held at power-up it enters the ROM bootloader, so the
// reset gesture is a hold *while running* (ADR 0009).
//   tap:  pressed and released within tapMaxMs  -> Tap, reported on release
//   hold: pressed for holdMs                    -> Hold, reported once while held
// A press between tapMaxMs and holdMs is ignored, and a hold never also taps.
#pragma once

#include <stdint.h>

namespace hs {

class LongPress {
public:
    enum class Action { None, Tap, Hold };

    LongPress(uint32_t debounceMs, uint32_t tapMaxMs, uint32_t holdMs)
        : debounceMs_(debounceMs), tapMaxMs_(tapMaxMs), holdMs_(holdMs) {}

    // `pressed` is the raw reading (already inverted for active-low buttons).
    Action update(bool pressed, uint32_t nowMs) {
        if (pressed != raw_) {
            raw_ = pressed;
            changedMs_ = nowMs;
        }
        if (raw_ != stable_ && nowMs - changedMs_ >= debounceMs_) {
            stable_ = raw_;
            if (stable_) {
                downMs_ = changedMs_;
                holdFired_ = false;
            } else if (!holdFired_ && changedMs_ - downMs_ <= tapMaxMs_) {
                return Action::Tap;
            }
        }
        if (stable_ && !holdFired_ && nowMs - downMs_ >= holdMs_) {
            holdFired_ = true;
            return Action::Hold;
        }
        return Action::None;
    }

    bool pressed() const { return stable_; }

    // When the latest press began (debounced). With a Tap, this is the tap's start.
    uint32_t pressStartMs() const { return downMs_; }

    // How long the current press has lasted (0 when released), for a countdown.
    uint32_t heldMs(uint32_t nowMs) const { return stable_ ? nowMs - downMs_ : 0; }

private:
    uint32_t debounceMs_;
    uint32_t tapMaxMs_;
    uint32_t holdMs_;
    uint32_t changedMs_ = 0;
    uint32_t downMs_ = 0;
    bool raw_ = false;
    bool stable_ = false;
    bool holdFired_ = false;
};

}  // namespace hs
