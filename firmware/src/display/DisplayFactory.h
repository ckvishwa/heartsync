#pragma once

#include "display/IDisplay.h"

namespace hs {

// Returns the one display for this build, chosen by the DISPLAY_DRIVER build flag.
// The object lives for the lifetime of the program.
IDisplay& createDisplay();

}  // namespace hs
