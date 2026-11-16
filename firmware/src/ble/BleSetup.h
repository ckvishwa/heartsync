// BLE Wi-Fi setup service (Phase 3, ADR 0009, docs/protocol.md "BLE provisioning").
//
// NimBLE GATT server with one service. Every characteristic needs an encrypted,
// authenticated link (LE Secure Connections only, passkey shown on the OLED).
// NimBLE callbacks run on the BLE host task: they only queue work under a mutex,
// and loop() on the Arduino task does the Wi-Fi, HTTP and display work.
//
// Never logs the Wi-Fi password, the token, or the passkey.
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

private:
    void showState();
    void notifyStatus(const char* reason = nullptr);
    void newPasskey();
    void stopAdvertising();
    void startAdvertising();
    void handleWifiTest(uint32_t nowMs);

    Animator& animator_;
    WifiManager& wifi_;
    CloudClient& cloud_;
    setup::SetupMachine machine_{HS_SETUP_MAX_FAILS, HS_SETUP_WINDOW_MS};
    setup::State shown_ = setup::State::TimedOut;
    bool pinShown_ = false;
    static constexpr uint32_t kPairingDeadlineMs = 60000;
    uint32_t connectedMs_ = 0;
    uint32_t wifiStartMs_ = 0;
    uint32_t signedInMs_ = 0;
};

}  // namespace hs

#endif  // HS_BLE_SETUP
