// STUB, filled in Phase 2 (see docs/phases.md and docs/protocol.md).
//
// Plan:
//   1. Sign in with the device's custom token (the device acts as its owner).
//   2. Listen to couples/{coupleId}/events where from != owner, decode each
//      with decodeEvent(), and publish it on the EventBus.
//   3. Write the device heartbeat to couples/{coupleId}/devices/{deviceId}.
//   4. sendHeart(): write a heart event with from == owner.
#pragma once

#include "events/EventBus.h"

namespace hs {

class CloudClient {
public:
    explicit CloudClient(EventBus& bus) : bus_(bus) {}

    void begin(const char* deviceId);
    void loop();

    // Returns false until Phase 2 implements it.
    bool sendHeart();

private:
    EventBus& bus_;
    const char* deviceId_ = nullptr;
};

}  // namespace hs
