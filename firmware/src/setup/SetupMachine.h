// BLE setup flow as a pure state machine (docs/protocol.md "BLE provisioning",
// ADR 0009). Hardware-free: compiles in native tests. The BLE and Wi-Fi glue
// (src/ble/BleSetup) feeds it events and acts on what it returns.
//
//   Advertising --connect--> Connected --auth ok--> Ready
//   Ready --creds--> WifiConnecting --ok--> WifiOk --token--> SigningIn --ok--> SignedIn
//                                   \--fail--> WifiFailed (new creds allowed)
//   SigningIn --fail--> WifiOk (a new token is allowed)
//   wrong passkey: fails++, back to Advertising; at maxFails -> Locked
//   no connection for windowMs -> TimedOut
//   BOOT hold -> clears the lockout (the glue also wipes storage and reboots)
#pragma once

#include <stdint.h>

namespace hs {
namespace setup {

enum class State {
    Advertising,
    Connected,       // link up, not yet paired
    Ready,           // paired: encrypted + authenticated (LE Secure Connections)
    WifiConnecting,
    WifiOk,
    WifiFailed,
    SigningIn,
    SignedIn,
    Locked,
    TimedOut,
};

class SetupMachine {
public:
    SetupMachine(uint8_t maxFails, uint32_t windowMs) : maxFails_(maxFails), windowMs_(windowMs) {}

    // `fails` is the stored count of wrong passkeys (survives reboots).
    void begin(uint32_t nowMs, uint8_t fails);

    void onConnect();
    void onDisconnect(uint32_t nowMs);
    // Pairing finished. `ok` means encrypted, authenticated, 16-byte key.
    void onAuth(bool ok, uint32_t nowMs);

    // Returns false (and changes nothing) if credentials are not accepted now.
    bool onCreds();
    void onWifiResult(bool ok);
    // Returns false if a token is not accepted now (Wi-Fi must be up).
    bool onToken();
    void onSignInResult(bool ok);

    void onBootHold(uint32_t nowMs);
    void tick(uint32_t nowMs);

    State state() const { return state_; }
    uint8_t fails() const { return fails_; }
    bool advertising() const { return state_ == State::Advertising; }
    // Status characteristic `state` value for the current state.
    const char* statusName() const;

private:
    uint8_t maxFails_;
    uint32_t windowMs_;
    uint32_t windowStartMs_ = 0;
    uint8_t fails_ = 0;
    State state_ = State::Advertising;
};

const char* stateName(State s);

}  // namespace setup
}  // namespace hs
