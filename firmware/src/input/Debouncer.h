// Button debouncer. Hardware-free: compiles in native tests.
// Feed the raw level and the time; it reports one press per stable
// released -> pressed transition.
#pragma once

#include <stdint.h>

namespace hs {

class Debouncer {
public:
    explicit Debouncer(uint32_t stableMs) : stableMs_(stableMs) {}

    // `pressed` is the raw reading (already inverted for active-low buttons).
    // Returns true exactly once per debounced press.
    bool update(bool pressed, uint32_t nowMs) {
        if (pressed != raw_) {
            raw_ = pressed;
            changedMs_ = nowMs;
            return false;
        }
        if (raw_ != stable_ && nowMs - changedMs_ >= stableMs_) {
            stable_ = raw_;
            return stable_;
        }
        return false;
    }

    bool pressed() const { return stable_; }

private:
    uint32_t stableMs_;
    uint32_t changedMs_ = 0;
    bool raw_ = false;
    bool stable_ = false;
};

}  // namespace hs
