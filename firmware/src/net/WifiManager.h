// Station-mode Wi-Fi with non-blocking reconnect. Credentials come from secrets.h.
// BLE provisioning replaces the hardcoded credentials in Phase 3.
#pragma once

#include <stdint.h>

namespace hs {

class WifiManager {
public:
    // Start connecting. Returns immediately.
    void begin(const char* ssid, const char* password);

    // Call from loop(). Logs state changes and retries while disconnected.
    void loop();

    bool connected() const;

private:
    bool started_ = false;
    bool wasConnected_ = false;
    uint32_t lastAttemptMs_ = 0;
};

}  // namespace hs
