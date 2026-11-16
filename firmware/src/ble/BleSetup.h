// BLE Wi-Fi setup service (Phase 3, ADR 0009, docs/protocol.md "BLE provisioning").
//
// NimBLE GATT server with one service. Every characteristic needs an encrypted,
// authenticated link (LE Secure Connections only).
//
// Pairing is numeric comparison: the same 6-digit code shows on the OLED and on
// the phone. The user taps Pair on the phone AND taps BOOT on the board
// (confirm()). The BOOT tap proves someone is at the board, so nobody nearby
// can pair without touching it; it is only meaningful if the user compared the
// two codes first. No BOOT tap within HS_SETUP_CONFIRM_MS rejects the pairing.
//
// The Wi-Fi list is paged. A notification on wifiList is only a "page ready"
// signal (1 byte: the page number); the app reads the value itself (a long
// read, up to 512 bytes), because a notification holds only MTU-3 bytes.
//
// NimBLE callbacks run on the BLE host task: they only queue work under a mutex,
// and loop() on the Arduino task does the Wi-Fi, HTTP and display work.
//
// Never logs the Wi-Fi password, the token, or the pairing code.
#pragma once

#include "config.h"

#if HS_BLE_SETUP

#include <stdint.h>

#include "art/Animator.h"
#include "net/CloudClient.h"
#include "net/WifiManager.h"
#include "setup/SetupMachine.h"

namespace hs {

class BleSetup {
public:
    BleSetup(Animator& animator, WifiManager& wifi, CloudClient& cloud)
        : animator_(animator), wifi_(wifi), cloud_(cloud) {}

    void begin(const char* deviceId);
    void loop(uint32_t nowMs);
    // BOOT held in setup mode: clear the lockout and advertise again.
    void restart(uint32_t nowMs);
    // BOOT tapped in setup mode: accepts the pairing code on screen, but only
    // while a pairing is waiting for it and the press began (`pressStartMs`)
    // after the code appeared, so the user saw the code before pressing.
    // Otherwise it does nothing (it is never remembered for a later pairing).
    void confirm(uint32_t pressStartMs);

private:
    void showState();
    void notifyStatus(const char* reason = nullptr);
    void endConfirm();
    void stopAdvertising();
    void startAdvertising();
    void handleWifiTest(uint32_t nowMs);

    Animator& animator_;
    WifiManager& wifi_;
    CloudClient& cloud_;
    setup::SetupMachine machine_{HS_SETUP_MAX_FAILS, HS_SETUP_WINDOW_MS};
    setup::State shown_ = setup::State::TimedOut;
    bool codeShown_ = false;       // a pairing code was shown this session
    bool confirmPending_ = false;  // a code is on screen, waiting for BOOT
    uint16_t confirmHandle_ = 0;
    uint32_t confirmStartMs_ = 0;
    static constexpr uint32_t kPairingDeadlineMs = 60000;
    uint32_t connectedMs_ = 0;
    uint32_t wifiStartMs_ = 0;
    uint32_t signedInMs_ = 0;
};

}  // namespace hs

#endif  // HS_BLE_SETUP
