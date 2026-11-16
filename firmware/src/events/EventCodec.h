// JSON encoding of events: {"type":"heart","from":"<uid>","payload":{}}
// See "Device wire format" in docs/protocol.md.
#pragma once

#include <string>

#include "events/Event.h"

namespace hs {

// Encode an event as compact JSON. Returns an empty string if the event is
// invalid (unknown type, empty sender, or a payload that is not a JSON object).
std::string encodeEvent(const Event& event);

// Decode JSON into an event. Returns false and leaves `out` untouched if the
// JSON is malformed, the type is unknown, or the sender is missing.
bool decodeEvent(const char* json, Event& out);

}  // namespace hs
