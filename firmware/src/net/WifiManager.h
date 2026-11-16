// Station-mode Wi-Fi with non-blocking reconnect. Credentials come from BLE
// setup (net/WifiStore), or on bench builds from secrets.h (HS_DEV_WIFI_FALLBACK).
#pragma once

#include <stdint.h>

#include <vector>

#include "setup/SetupCodec.h"

namespace hs {

class WifiManager {
public:
    // Start connecting. Returns immediately (after a short scan that logs
    // whether the SSID is visible). Never logs the password.
    void begin(const char* ssid, const char* password);

    // Setup mode: try credentials without the logging scan (it would block loop()
    // and throw away a running async scan). Returns immediately.
    void beginTest(const char* ssid, const char* password);

    // Setup mode: station mode on, not connected, ready to scan.
    void beginIdle();

    // Call from loop(). Logs state changes and retries while disconnected.
    void loop();

    // Drop the connection and stop retrying.
    void stop();

    bool connected() const;

    // Last station disconnect reason (ESP-IDF code), 0 if none since begin().
    uint8_t lastDisconnectReason() const;

    // Background scan for the setup list. startScan() returns false if a scan
    // cannot start now; scanResults() returns true once results are ready.
    bool startScan();
    bool scanResults(std::vector<setup::WifiNetwork>& out);

private:
    void registerEvents();

    bool started_ = false;
    bool eventsRegistered_ = false;
    bool wasConnected_ = false;
    uint32_t lastAttemptMs_ = 0;
};

}  // namespace hs
