// heartsync firmware entry point.
// Phase 1 hello: print the device ID, show a static heart through IDisplay,
// connect to Wi-Fi from secrets.h.
#include <Arduino.h>
#include <esp_mac.h>

#include "config.h"

#if __has_include("secrets.h")
#include "secrets.h"
#else
#warning "include/secrets.h not found: using secrets.example.h, Wi-Fi will not connect"
#include "secrets.example.h"
#endif

#include "art/Animator.h"
#include "art/Sprites.h"
#include "display/DisplayFactory.h"
#include "events/EventBus.h"
#include "net/CloudClient.h"
#include "net/Ota.h"
#include "net/WifiManager.h"
#include "util/Log.h"

namespace {

hs::IDisplay& display = hs::createDisplay();
hs::Animator animator(display);
hs::EventBus bus;
hs::WifiManager wifi;
hs::CloudClient cloud(bus);

char deviceId[16];  // "hs-" + 12 hex digits of the base MAC

void initDeviceId() {
    uint8_t mac[6] = {0};
    esp_efuse_mac_get_default(mac);
    snprintf(deviceId, sizeof(deviceId), "hs-%02x%02x%02x%02x%02x%02x", mac[0], mac[1], mac[2],
             mac[3], mac[4], mac[5]);
}

void onEvent(const hs::Event& event, void*) {
    LOGI("event", "%s from %s", hs::eventTypeName(event.type), event.from.c_str());
    if (event.type == hs::EventType::Heart) {
        animator.showCentered(hs::sprites::kHeart);
    }
}

}  // namespace

void setup() {
    Serial.begin(HS_SERIAL_BAUD);
    delay(200);
    initDeviceId();
    LOGI("boot", "heartsync v%s board=%s", HS_FW_VERSION, HS_BOARD_NAME);
    LOGI("boot", "device id: %s", deviceId);

    hs::ota::begin();

    const bool displayOk = display.begin();
    LOGI("boot", "display=%s %ux%u ok=%d", display.name(), (unsigned)display.width(),
         (unsigned)display.height(), displayOk);
    animator.showCentered(hs::sprites::kHeart);

    bus.subscribe(onEvent);
    wifi.begin(HS_WIFI_SSID, HS_WIFI_PASSWORD);
    cloud.begin(deviceId);

    if (displayOk) {
        hs::ota::reportHealthy();
    }
}

void loop() {
    wifi.loop();
    cloud.loop();

    static uint32_t lastStatusMs = 0;
    if (millis() - lastStatusMs >= 30000) {
        lastStatusMs = millis();
        LOGI("status", "id=%s wifi=%d heap=%u", deviceId, wifi.connected(),
             (unsigned)ESP.getFreeHeap());
    }
    delay(10);
}
