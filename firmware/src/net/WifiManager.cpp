#include "net/WifiManager.h"

#include <Arduino.h>
#include <WiFi.h>
#include <string.h>

#include "config.h"
#include "util/Log.h"

namespace hs {

void WifiManager::begin(const char* ssid, const char* password) {
    if (ssid == nullptr || ssid[0] == '\0' || strcmp(ssid, "your-wifi-name") == 0) {
        LOGW("wifi", "no credentials: copy include/secrets.example.h to include/secrets.h");
        return;
    }
    WiFi.mode(WIFI_STA);
    WiFi.setAutoReconnect(true);
    WiFi.begin(ssid, password);
    started_ = true;
    lastAttemptMs_ = millis();
    LOGI("wifi", "connecting to \"%s\"", ssid);  // SSID only; never log the password
}

void WifiManager::loop() {
    if (!started_) {
        return;
    }
    const bool isConnected = connected();
    if (isConnected && !wasConnected_) {
        LOGI("wifi", "connected, ip=%s rssi=%d", WiFi.localIP().toString().c_str(), WiFi.RSSI());
    } else if (!isConnected && wasConnected_) {
        LOGW("wifi", "disconnected");
        lastAttemptMs_ = millis();
    }
    wasConnected_ = isConnected;

    if (!isConnected && millis() - lastAttemptMs_ >= HS_WIFI_RETRY_MS) {
        lastAttemptMs_ = millis();
        const wl_status_t st = WiFi.status();
        LOGI("wifi", "retrying (status %d: %s)", (int)st,
             st == WL_NO_SSID_AVAIL   ? "network not found; ESP32 needs 2.4 GHz"
             : st == WL_CONNECT_FAILED ? "connect failed; check password"
                                       : "not connected");
        WiFi.reconnect();
    }
}

bool WifiManager::connected() const { return WiFi.status() == WL_CONNECTED; }

}  // namespace hs
