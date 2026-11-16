#include "net/WifiManager.h"

#include <Arduino.h>
#include <WiFi.h>
#include <string.h>

#include "config.h"
#include "util/Log.h"

namespace hs {

namespace {

const char* reasonText(uint8_t r) {
    switch (r) {
        case 201: return "no access point found (2.4 GHz network missing?)";
        case 202: return "auth failed (password?)";
        case 15: return "4-way handshake timeout (wrong password?)";
        case 2: return "auth expired";
        case 8: return "left the network";
        default: return "see esp_wifi_types.h";
    }
}

volatile uint8_t gLastReason = 0;

// Logs whether the configured SSID is visible from the board (2.4 GHz only).
void scanFor(const char* ssid) {
    const int n = WiFi.scanNetworks(false, true);
    int matches = 0;
    for (int i = 0; i < n; ++i) {
        if (WiFi.SSID(i) == ssid) {
            ++matches;
            LOGI("wifi", "scan: \"%s\" seen, channel %d, rssi %d, auth %d", ssid, WiFi.channel(i),
                 WiFi.RSSI(i), (int)WiFi.encryptionType(i));
        }
    }
    if (matches == 0) {
        LOGW("wifi", "scan: \"%s\" NOT seen among %d networks (board is 2.4 GHz only)", ssid, n);
    }
    WiFi.scanDelete();
}

}  // namespace

void WifiManager::begin(const char* ssid, const char* password) {
    if (ssid == nullptr || ssid[0] == '\0' || strcmp(ssid, "your-wifi-name") == 0) {
        LOGW("wifi", "no credentials: copy include/secrets.example.h to include/secrets.h");
        return;
    }
    WiFi.mode(WIFI_STA);
    registerEvents();
    gLastReason = 0;
    scanFor(ssid);
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

void WifiManager::registerEvents() {
    if (eventsRegistered_) {
        return;
    }
    eventsRegistered_ = true;
    WiFi.onEvent(
        [](WiFiEvent_t, WiFiEventInfo_t info) {
            const uint8_t r = info.wifi_sta_disconnected.reason;
            gLastReason = r;
            LOGW("wifi", "disconnect reason %u: %s", (unsigned)r, reasonText(r));
        },
        ARDUINO_EVENT_WIFI_STA_DISCONNECTED);
}

void WifiManager::beginTest(const char* ssid, const char* password) {
    WiFi.mode(WIFI_STA);
    registerEvents();
    WiFi.scanDelete();
    gLastReason = 0;
    WiFi.setAutoReconnect(true);
    WiFi.begin(ssid, password);
    started_ = true;
    wasConnected_ = false;
    lastAttemptMs_ = millis();
    LOGI("wifi", "testing \"%s\"", ssid);  // SSID only; never log the password
}

void WifiManager::beginIdle() {
    WiFi.mode(WIFI_STA);
    WiFi.setAutoReconnect(false);
    registerEvents();
    WiFi.disconnect();
}

void WifiManager::stop() {
    started_ = false;
    wasConnected_ = false;
    WiFi.setAutoReconnect(false);
    WiFi.disconnect();
}

bool WifiManager::connected() const { return WiFi.status() == WL_CONNECTED; }

uint8_t WifiManager::lastDisconnectReason() const { return gLastReason; }

bool WifiManager::startScan() {
    if (WiFi.scanComplete() == WIFI_SCAN_RUNNING) {
        return true;  // already running
    }
    WiFi.scanDelete();
    return WiFi.scanNetworks(true /* async */, false /* no hidden */) == WIFI_SCAN_RUNNING;
}

bool WifiManager::scanResults(std::vector<setup::WifiNetwork>& out) {
    const int n = WiFi.scanComplete();
    if (n < 0) {
        return false;  // running, or failed (WIFI_SCAN_FAILED)
    }
    out.clear();
    for (int i = 0; i < n; ++i) {
        setup::WifiNetwork net;
        net.ssid = WiFi.SSID(i).c_str();
        net.rssi = WiFi.RSSI(i);
        net.open = WiFi.encryptionType(i) == WIFI_AUTH_OPEN;
        out.push_back(net);
    }
    WiFi.scanDelete();
    return true;
}

}  // namespace hs
