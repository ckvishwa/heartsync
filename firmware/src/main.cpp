// heartsync firmware entry point.
// Phase 1 hello: print the device ID, show the display test screen through
// IDisplay, connect to Wi-Fi from secrets.h.
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
        animator.showCentered(hs::sprites::kHeart, animator.fitScale(hs::sprites::kHeart));
    }
}

}  // namespace

void setup() {
    Serial.begin(HS_SERIAL_BAUD);
    delay(200);
    initDeviceId();
    LOGI("boot", "heartsync v%s board=%s", HS_FW_VERSION, HS_BOARD_NAME);
    LOGI("boot", "device id: %s", deviceId);
    LOGI("boot", "chip=%s rev=%d cores=%d flash=%uKB psram=%uKB heap=%u", ESP.getChipModel(),
         (int)ESP.getChipRevision(), (int)ESP.getChipCores(),
         (unsigned)(ESP.getFlashChipSize() / 1024), (unsigned)(ESP.getPsramSize() / 1024),
         (unsigned)ESP.getFreeHeap());

    hs::ota::begin();

    const bool displayOk = display.begin();
    LOGI("boot", "display=%s logical=%ux%u color=%d ok=%d", display.name(),
         (unsigned)display.logicalWidth(), (unsigned)display.logicalHeight(),
         (int)display.isColor(), (int)displayOk);
    animator.showTestScreen("HEARTSYNC " HS_FW_VERSION);

    bus.subscribe(onEvent);
    wifi.begin(HS_WIFI_SSID, HS_WIFI_PASSWORD);
    cloud.begin(deviceId);

    // A missing bench display is not a firmware fault: stay healthy so a
    // wiring problem never triggers a rollback or a reboot loop.
    if (!displayOk) {
        LOGW("boot", "display not available; running headless");
    }
    hs::ota::reportHealthy();
}

void loop() {
    wifi.loop();
    cloud.loop();
    display.tick(millis());

    static uint32_t lastStatusMs = 0;
    if (millis() - lastStatusMs >= 30000) {
        lastStatusMs = millis();
        LOGI("status", "id=%s wifi=%d heap=%u", deviceId, wifi.connected(),
             (unsigned)ESP.getFreeHeap());
    }
    delay(10);
}
