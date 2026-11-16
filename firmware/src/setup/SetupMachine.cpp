#include "setup/SetupMachine.h"

namespace hs {
namespace setup {

void SetupMachine::begin(uint32_t nowMs, uint8_t fails) {
    fails_ = fails;
    windowStartMs_ = nowMs;
    state_ = fails_ >= maxFails_ ? State::Locked : State::Advertising;
}

void SetupMachine::onConnect() {
    if (state_ == State::Advertising) {
        state_ = State::Connected;
    }
}

void SetupMachine::onDisconnect(uint32_t nowMs) {
    switch (state_) {
        case State::Locked:
        case State::TimedOut:
        case State::SignedIn:
            return;  // terminal until BOOT hold or reboot
        default:
            state_ = State::Advertising;
            windowStartMs_ = nowMs;  // a fresh window after every session
    }
}

void SetupMachine::onAuth(bool ok, uint32_t nowMs) {
    if (state_ != State::Connected && state_ != State::Advertising) {
        return;
    }
    if (ok) {
        state_ = State::Ready;
        fails_ = 0;
        return;
    }
    if (fails_ < 255) {
        fails_++;
    }
    if (fails_ >= maxFails_) {
        state_ = State::Locked;
    } else {
        state_ = State::Advertising;
        windowStartMs_ = nowMs;
    }
}

bool SetupMachine::onCreds() {
    switch (state_) {
        case State::Ready:
        case State::WifiFailed:
        case State::WifiOk:  // switching to another network before the token
            state_ = State::WifiConnecting;
            return true;
        default:
            return false;
    }
}

void SetupMachine::onWifiResult(bool ok) {
    if (state_ == State::WifiConnecting) {
        state_ = ok ? State::WifiOk : State::WifiFailed;
    }
}

bool SetupMachine::onToken() {
    if (state_ != State::WifiOk) {
        return false;
    }
    state_ = State::SigningIn;
    return true;
}

void SetupMachine::onSignInResult(bool ok) {
    if (state_ == State::SigningIn) {
        state_ = ok ? State::SignedIn : State::WifiOk;
    }
}

void SetupMachine::onBootHold(uint32_t nowMs) {
    fails_ = 0;
    windowStartMs_ = nowMs;
    state_ = State::Advertising;
}

void SetupMachine::tick(uint32_t nowMs) {
    if (state_ == State::Advertising && nowMs - windowStartMs_ >= windowMs_) {
        state_ = State::TimedOut;
    }
}

const char* SetupMachine::statusName() const { return stateName(state_); }

const char* stateName(State s) {
    switch (s) {
        case State::Advertising:
        case State::Connected:
        case State::Ready:
            return "idle";
        case State::WifiConnecting:
            return "wifi_connecting";
        case State::WifiOk:
            return "wifi_ok";
        case State::WifiFailed:
            return "wifi_failed";
        case State::SigningIn:
            return "signing_in";
        case State::SignedIn:
            return "signed_in";
        case State::Locked:
            return "locked";
        case State::TimedOut:
            return "timed_out";
    }
    return "error";
}

}  // namespace setup
}  // namespace hs
