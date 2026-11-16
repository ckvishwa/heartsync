// Cloud sync over the Firebase REST APIs (emulator for now).
// See docs/adr/0008-device-sync-rest-polling.md, ADR 0009, docs/protocol.md.
//
//   1. Sign in as the board's own uid dev_<deviceId>: a refresh token stored in
//      NVS, or, during BLE setup, the custom token from registerDevice (held in
//      RAM, used once). On the bench, `token <jwt>` over serial also works.
//   2. Read the couple and owner from the ID token's claims (a board token
//      cannot read users/ or the couple document).
//   3. Heartbeat couples/{id}/devices/{deviceId} (owner, firmwareVersion,
//      online, lastSeen). Its commitTime is the starting cursor for events.
//   4. Poll couples/{id}/events where createdAt > cursor, skip the owner's own,
//      and publish the rest on the EventBus.
//   5. sendHeart() calls the sendHeart Cloud Function; it posts as the owner.
//
// Tokens are never logged. The device never reads users/**.
#pragma once

#include <stdint.h>

#include <string>

#include "cloud/FirestoreCodec.h"
#include "config.h"
#include "events/EventBus.h"

namespace hs {

class CloudClient {
public:
    enum class SignInResult : uint8_t { Ok, Rejected, WrongBoard, Network, Disabled };

    explicit CloudClient(EventBus& bus) : bus_(bus) {}

    void begin(const char* deviceId);

    // Call from loop(). Does at most one network call per invocation.
    void loop(bool wifiConnected);

    // Send a heart as the owner. Blocks for one HTTP call (a few hundred ms on LAN).
    bool sendHeart();

    // BLE setup: sign in once with a custom token from registerDevice. The token
    // is never stored; on success the refresh token is saved to NVS. Blocks for
    // one HTTP call.
    SignInResult signInWithCustomToken(const std::string& customToken);

#if HS_DEV_SERIAL_TOKEN
    // Bench only: store a custom token in NVS and sign in with it on the next loop().
    void provisionCustomToken(const char* token);
#endif
    // Erase the stored refresh and custom tokens.
    void forget();
    // True if a refresh token is stored (the board has been set up).
    bool hasCredentials() const;
    // True after the stored credentials were refused or belong to another board:
    // the board needs BLE setup again.
    bool needsSetup() const { return needsSetup_; }

    bool ready() const { return state_ == State::Polling; }
    void logStatus() const;

private:
    enum class State : uint8_t { Disabled, SignIn, Cursor, Polling };

    bool signIn();
    // Validates and adopts a fresh session. False if the claims are not this board's.
    bool adopt(const fs::AuthSession& s);
    bool heartbeat(bool setCursor);
    bool poll();
    void fail(const char* what, int status);
    void resetSession(State next);

    std::string authUrl(const char* path) const;
    std::string docsUrl(const std::string& path) const;
    int request(const char* method, const std::string& url, const char* contentType,
                const std::string& body, bool auth, std::string& response,
                uint32_t timeoutMs = HS_CLOUD_HTTP_TIMEOUT_MS);

    EventBus& bus_;
    const char* deviceId_ = nullptr;
    std::string host_;
    std::string apiKey_;
    State state_ = State::Disabled;
    bool needsSetup_ = false;
    fs::AuthSession session_;
    fs::BoardClaims claims_;
    std::string cursor_;
    uint32_t tokenExpiresMs_ = 0;
    uint32_t nextActionMs_ = 0;
    uint32_t nextHeartbeatMs_ = 0;
    uint32_t backoffMs_ = 0;
};

}  // namespace hs
