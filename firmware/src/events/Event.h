// Event types shared with the cloud. See docs/protocol.md.
// Hardware-free: compiles in native tests.
#pragma once

#include <stdint.h>
#include <string>

namespace hs {

enum class EventType : uint8_t {
    Heart,
    Touch,  // Phase 4
    Art,    // Phase 3
    Mood,   // Phase 3
    Voice,  // Phase 7
    Unknown,
};

struct Event {
    EventType type = EventType::Unknown;
    std::string from;                 // uid of the sender
    std::string payloadJson = "{}";   // type-specific JSON object
};

// Wire name of a type ("heart", "touch", ...). Unknown maps to "unknown".
const char* eventTypeName(EventType type);

// Parse a wire name. Returns EventType::Unknown for anything unrecognised.
EventType eventTypeFromName(const char* name);

}  // namespace hs
