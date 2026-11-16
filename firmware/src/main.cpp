// heartsync firmware entry point.
//
// Two modes (ADR 0009):
//   setup   BLE Wi-Fi setup from the app. Entered when no Wi-Fi is stored, or
//           after BOOT is held 5 s (that also wipes Wi-Fi and tokens).
//   normal  Wi-Fi from NVS (bench builds: secrets.h as a fallback), cloud sync.
// BOOT in normal mode: a tap sends a heart. BOOT in setup mode: a tap confirms
// the pairing code on screen (only while one is waiting; never a heart). GPIO 0
// is a strapping pin, so the hold works while running, never at power-up.
#include <Arduino.h>
#include <algorithm>
#include <esp_mac.h>

#include "config.h"

#if __has_include("secrets.h")
#include "secrets.h"
#else
#warning "include/secrets.h not found: using secrets.example.h (no emulator host)"
#include "secrets.example.h"
#endif

#include "art/Animator.h"
#include "art/Sprites.h"
#include "display/DisplayFactory.h"
#include "events/EventBus.h"
#include "ble/BleSetup.h"
#include "net/CloudClient.h"
#include "net/Ota.h"
#include "net/WifiManager.h"
#include "net/WifiStore.h"
#include "setup/LongPress.h"
#include "util/Log.h"

namespace {

hs::IDisplay& display = hs::createDisplay();
hs::Animator animator(display);
hs::EventBus bus;
hs::WifiManager wifi;
hs::CloudClient cloud(bus);
hs::LongPress bootButton(HS_BUTTON_DEBOUNCE_MS, HS_SETUP_TAP_MAX_MS, HS_SETUP_LONG_PRESS_MS);
#if HS_BLE_SETUP
hs::BleSetup bleSetup(animator, wifi, cloud);
#endif
bool setupMode = false;

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

void sendHeart() {
    const bool ok = cloud.sendHeart();
    animator.showSpriteWithText(hs::sprites::kHeart, ok ? "SENT" : "NOT SENT", false);
}

#if HS_BLE_SETUP
// BOOT held 5 s: wipe Wi-Fi and tokens and restart into setup mode.
void resetToSetup() {
    LOGW("input", "BOOT held: wiping Wi-Fi and tokens, restarting into setup");
    animator.showTestScreen("RESETTING");
    hs::wifistore::erase();
    cloud.forget();
    hs::setupstore::setFails(0);
    hs::setupstore::setForced(true);
    delay(500);
    ESP.restart();
}

// While BOOT is held past a tap, count down to the reset on the display.
void showHoldCountdown(uint32_t heldMs) {
    static uint32_t lastShown = 0;
    if (heldMs <= HS_SETUP_TAP_MAX_MS) {
        lastShown = 0;
        return;
    }
    const uint32_t left = (HS_SETUP_LONG_PRESS_MS - heldMs + 999) / 1000;
    if (left != lastShown && heldMs < HS_SETUP_LONG_PRESS_MS) {
        lastShown = left;
        char text[16];
        snprintf(text, sizeof(text), "RESET IN %u", (unsigned)left);
        animator.showTestScreen(text);
    }
}
#endif  // HS_BLE_SETUP

// Serial commands, one per line. Tokens are never echoed.
//   token <jwt>   bench only: store a board token (tools/provision_device.py)
//   forget        erase stored tokens
//   heart         send a heart, same as a BOOT tap
//   status        print cloud state
void handleCommand(char* line) {
    if (strncmp(line, "token ", 6) == 0) {
#if HS_DEV_SERIAL_TOKEN
        cloud.provisionCustomToken(line + 6);
#else
        LOGW("cli", "serial tokens are off in this build: use BLE setup from the app");
#endif
    } else if (strcmp(line, "forget") == 0) {
        cloud.forget();
    } else if (strcmp(line, "heart") == 0) {
        sendHeart();
    } else if (strcmp(line, "status") == 0) {
        LOGI("status", "id=%s mode=%s wifi=%d heap=%u min=%u", deviceId,
             setupMode ? "setup" : "normal", wifi.connected(), (unsigned)ESP.getFreeHeap(),
             (unsigned)ESP.getMinFreeHeap());
        cloud.logStatus();
    } else if (line[0] != '\0') {
        LOGW("cli", "unknown command (try: status, heart, token <jwt>, forget)");
    }
}

void pollSerial() {
    static char line[HS_SERIAL_LINE_MAX];
    static size_t len = 0;
    static bool overflow = false;
    while (Serial.available() > 0) {
        const int c = Serial.read();
        if (c == '\r') {
            continue;
        }
        if (c == '\n') {
            line[len] = '\0';
            if (overflow) {
                LOGW("cli", "line too long, ignored");
            } else {
                handleCommand(line);
            }
            memset(line, 0, sizeof(line));  // do not keep tokens in RAM
            len = 0;
            overflow = false;
        } else if (len + 1 < sizeof(line)) {
            line[len++] = static_cast<char>(c);
        } else {
            overflow = true;
        }
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

    pinMode(HS_PIN_BUTTON, INPUT_PULLUP);  // BOOT button: input only, active low
    bus.subscribe(onEvent);
    cloud.begin(deviceId);

    hs::setup::WifiCreds creds;
    const bool haveWifi = hs::wifistore::load(creds);
    const bool forced = hs::setupstore::forced();
#if HS_BLE_SETUP
    bool fallback = false;
#if HS_DEV_WIFI_FALLBACK
    fallback = strlen(HS_WIFI_SSID) > 0 && strcmp(HS_WIFI_SSID, "your-wifi-name") != 0;
#endif
    setupMode = forced || (!haveWifi && !fallback);
#endif
    if (setupMode) {
#if HS_BLE_SETUP
        LOGI("boot", "mode: setup (%s)", forced ? "BOOT reset" : "no Wi-Fi stored");
        // Stay in setup until sign-in succeeds, even if Wi-Fi gets saved first
        // and power drops before the token arrives.
        hs::setupstore::setForced(true);
        bleSetup.begin(deviceId);
#endif
    } else if (haveWifi) {
        LOGI("boot", "mode: normal (Wi-Fi from setup)");
        wifi.begin(creds.ssid.c_str(), creds.pass.c_str());
    } else {
        LOGI("boot", "mode: normal (bench Wi-Fi from secrets.h)");
        wifi.begin(HS_WIFI_SSID, HS_WIFI_PASSWORD);
    }
    std::fill(creds.pass.begin(), creds.pass.end(), '\0');

    // A missing bench display is not a firmware fault: stay healthy so a
    // wiring problem never triggers a rollback or a reboot loop.
    if (!displayOk) {
        LOGW("boot", "display not available; running headless");
    }
    hs::ota::reportHealthy();
}

void loop() {
    const uint32_t now = millis();
    display.tick(now);
    pollSerial();
    const hs::LongPress::Action action = bootButton.update(digitalRead(HS_PIN_BUTTON) == LOW, now);

    if (setupMode) {
#if HS_BLE_SETUP
        bleSetup.loop(now);
        if (action == hs::LongPress::Action::Tap) {
            // Ignored unless a pairing code is waiting and the press began after
            // the code appeared.
            bleSetup.confirm(bootButton.pressStartMs());
        } else if (action == hs::LongPress::Action::Hold) {
            bleSetup.restart(now);
        }
#endif
    } else {
        wifi.loop();
        cloud.loop(wifi.connected());
#if HS_BLE_SETUP
        showHoldCountdown(bootButton.heldMs(now));
#endif
        if (action == hs::LongPress::Action::Tap) {
            LOGI("input", "BOOT tap: sending heart");
            sendHeart();
        } else if (action == hs::LongPress::Action::Hold) {
#if HS_BLE_SETUP
            resetToSetup();
#else
            LOGW("input", "BOOT held: this build has no BLE setup; nothing wiped");
#endif
        }
        static bool setupHintShown = false;
        if (cloud.needsSetup() && !setupHintShown) {
            setupHintShown = true;
            animator.showTestScreen("SETUP NEEDED");
        }
    }

    static uint32_t lastStatusMs = 0;
    if (millis() - lastStatusMs >= 30000) {
        lastStatusMs = millis();
        LOGI("status", "id=%s mode=%s wifi=%d heap=%u min=%u", deviceId,
             setupMode ? "setup" : "normal", wifi.connected(), (unsigned)ESP.getFreeHeap(),
             (unsigned)ESP.getMinFreeHeap());
    }
    delay(10);
}
