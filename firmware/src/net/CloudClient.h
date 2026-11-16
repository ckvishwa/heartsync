// Phase 2 cloud sync over the Firebase REST APIs (emulator for now).
// See docs/adr/0008-device-sync-rest-polling.md and docs/protocol.md.
//
//   1. Sign in as the owner: a refresh token stored in NVS, or, the first time,
//      a custom token provisioned over serial (`token <jwt>`) and then erased.
//   2. Read users/{owner}.coupleId and the partner uid from couples/{id}.members.
//   3. Heartbeat couples/{id}/devices/{deviceId} (owner, firmwareVersion,
//      online, lastSeen). Its commitTime is the starting cursor for events.
//   4. Poll couples/{id}/events where from == partner, createdAt > cursor, and
//      publish each one on the EventBus.
//   5. sendHeart() calls the sendHeart Cloud Function as the owner.
//
// Tokens are never logged. The device never reads users/{uid}/private/*.
#pragma once

#include <stdint.h>

#include <string>

#include "cloud/FirestoreCodec.h"
#include "events/EventBus.h"

namespace hs {

class CloudClient {
public:
    explicit CloudClient(EventBus& bus) : bus_(bus) {}

    void begin(const char* deviceId);

    // Call from loop(). Does at most one network call per invocation.
    void loop(bool wifiConnected);

    // Send a heart as the owner. Blocks for one HTTP call (a few hundred ms on LAN).
    bool sendHeart();

    // Store a custom token in NVS and sign in with it on the next loop().
    void provisionCustomToken(const char* token);
    // Erase the stored refresh and custom tokens.
    void forget();

    bool ready() const { return state_ == State::Polling; }
    void logStatus() const;

private:
    enum class State : uint8_t { Disabled, SignIn, Profile, Cursor, Polling };

    bool signIn();
    bool loadProfile();
    bool heartbeat(bool setCursor);
    bool poll();
    void fail(const char* what, int status);
    void resetSession(State next);

    std::string authUrl(const char* path) const;
    std::string docsUrl(const std::string& path) const;
    int request(const char* method, const std::string& url, const char* contentType,
                const std::string& body, bool auth, std::string& response);

    EventBus& bus_;
    const char* deviceId_ = nullptr;
    std::string host_;
    std::string apiKey_;
    State state_ = State::Disabled;
    fs::AuthSession session_;
    std::string coupleId_;
    std::string partnerUid_;
    std::string cursor_;
    uint32_t tokenExpiresMs_ = 0;
    uint32_t nextActionMs_ = 0;
    uint32_t nextHeartbeatMs_ = 0;
    uint32_t backoffMs_ = 0;
};

}  // namespace hs
