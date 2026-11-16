#include "events/EventCodec.h"

#include <ArduinoJson.h>
#include <string.h>

namespace hs {

namespace {

struct TypeName {
    EventType type;
    const char* name;
};

constexpr TypeName kTypeNames[] = {
    {EventType::Heart, "heart"}, {EventType::Touch, "touch"}, {EventType::Art, "art"},
    {EventType::Mood, "mood"},   {EventType::Voice, "voice"},
};

}  // namespace

const char* eventTypeName(EventType type) {
    for (const auto& entry : kTypeNames) {
        if (entry.type == type) {
            return entry.name;
        }
    }
    return "unknown";
}

EventType eventTypeFromName(const char* name) {
    if (name == nullptr) {
        return EventType::Unknown;
    }
    for (const auto& entry : kTypeNames) {
        if (strcmp(entry.name, name) == 0) {
            return entry.type;
        }
    }
    return EventType::Unknown;
}

std::string encodeEvent(const Event& event) {
    if (event.type == EventType::Unknown || event.from.empty()) {
        return {};
    }
    JsonDocument payload;
    if (deserializeJson(payload, event.payloadJson) != DeserializationError::Ok ||
        !payload.is<JsonObject>()) {
        return {};
    }
    JsonDocument doc;
    doc["type"] = eventTypeName(event.type);
    doc["from"] = event.from;
    doc["payload"] = payload.as<JsonObject>();
    std::string out;
    serializeJson(doc, out);
    return out;
}

bool decodeEvent(const char* json, Event& out) {
    if (json == nullptr) {
        return false;
    }
    JsonDocument doc;
    if (deserializeJson(doc, json) != DeserializationError::Ok || !doc.is<JsonObject>()) {
        return false;
    }
    const EventType type = eventTypeFromName(doc["type"].as<const char*>());
    const char* from = doc["from"].as<const char*>();
    if (type == EventType::Unknown || from == nullptr || from[0] == '\0') {
        return false;
    }
    Event event;
    event.type = type;
    event.from = from;
    if (doc["payload"].is<JsonObject>()) {
        event.payloadJson.clear();
        serializeJson(doc["payload"], event.payloadJson);
    }
    out = event;
    return true;
}

}  // namespace hs
