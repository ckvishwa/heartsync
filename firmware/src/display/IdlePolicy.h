// When a bench OLED should dim or switch off to avoid burn-in.
// Hardware-free: compiles in native tests.
#pragma once

#include <stdint.h>

namespace hs {

enum class IdleLevel : uint8_t { Active, Dim, Off };

// `idleMs` is time since the last activity. A threshold of 0 disables that step.
// Unsigned arithmetic makes millis() wrap-around safe for the caller
// (pass nowMs - lastActivityMs).
constexpr IdleLevel idleLevel(uint32_t idleMs, uint32_t dimAfterMs, uint32_t offAfterMs) {
    return (offAfterMs != 0 && idleMs >= offAfterMs)   ? IdleLevel::Off
           : (dimAfterMs != 0 && idleMs >= dimAfterMs) ? IdleLevel::Dim
                                                       : IdleLevel::Active;
}

}  // namespace hs
