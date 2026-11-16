#include "ble/BleSetup.h"

#if HS_BLE_SETUP

#include <Arduino.h>
#include <NimBLEDevice.h>
#include <esp_random.h>

#include <algorithm>
#include <atomic>
#include <mutex>
#include <string>
#include <vector>

#include "art/Sprites.h"
#include "net/WifiStore.h"
#include "setup/SetupCodec.h"
#include "util/Log.h"

namespace hs {

namespace {

using setup::State;

void wipe(std::string& s) {
    std::fill(s.begin(), s.end(), '\0');
    s.clear();
}

// Work queued by NimBLE callbacks (BLE host task) for loop() (Arduino task).
struct Shared {
    std::mutex m;
    bool connected = false;
    bool disconnected = false;
    bool pinRequested = false;
    int auth = -1;  // -1 none, 0 failed, 1 ok
    bool scanRequested = false;
    bool credsPending = false;
    bool credsBad = false;
    setup::WifiCreds creds;
    bool tokenComplete = false;
    bool tokenBad = false;
    setup::TokenAssembler token{HS_SETUP_TOKEN_MAX};
};

Shared g;
std::atomic<uint32_t> gPasskey{0};
NimBLEServer* gServer = nullptr;
NimBLECharacteristic* gWifiScan = nullptr;
NimBLECharacteristic* gWifiList = nullptr;
NimBLECharacteristic* gWifiCreds = nullptr;
NimBLECharacteristic* gToken = nullptr;
NimBLECharacteristic* gStatus = nullptr;

void clearValue(NimBLECharacteristic* c) {
    // Do not leave secrets in the attribute's own buffer.
    static const uint8_t kZero[1] = {0};
    c->setValue(kZero, 0);
}

class ServerCallbacks : public NimBLEServerCallbacks {
    void onConnect(NimBLEServer*, NimBLEConnInfo&) override {
        std::lock_guard<std::mutex> lock(g.m);
        g.connected = true;
    }

    void onDisconnect(NimBLEServer*, NimBLEConnInfo&, int) override {
        std::lock_guard<std::mutex> lock(g.m);
        g.disconnected = true;
        wipe(g.creds.pass);
        g.creds = {};
        g.credsPending = false;
        g.token.clear();
        g.tokenComplete = false;
    }

    uint32_t onPassKeyDisplay() override {
        std::lock_guard<std::mutex> lock(g.m);
        g.pinRequested = true;
        return gPasskey.load();
    }

    void onAuthenticationComplete(NimBLEConnInfo& info) override {
        // LE Secure Connections only (CONFIG_BT_NIMBLE_SM_SC_ONLY refuses legacy
        // pairing in the host); check the result again here.
        const bool ok =
            info.isEncrypted() && info.isAuthenticated() && info.getSecKeySize() == 16;
        if (!ok && gServer != nullptr) {
            gServer->disconnect(info);
        }
        std::lock_guard<std::mutex> lock(g.m);
        g.auth = ok ? 1 : 0;
    }
};

class CharCallbacks : public NimBLECharacteristicCallbacks {
    void onWrite(NimBLECharacteristic* c, NimBLEConnInfo& info) override {
        if (!info.isEncrypted() || !info.isAuthenticated()) {
            clearValue(c);
            return;  // the stack enforces this too (WRITE_AUTHEN)
        }
        const NimBLEAttValue v = c->getValue();
        std::lock_guard<std::mutex> lock(g.m);
        if (c == gWifiScan) {
            g.scanRequested = true;
        } else if (c == gWifiCreds) {
            setup::WifiCreds creds;
            const setup::CredsError err = setup::parseWifiCreds(v.data(), v.size(), creds);
            if (err == setup::CredsError::None) {
                wipe(g.creds.pass);
                g.creds = creds;
                g.credsPending = true;
                wipe(creds.pass);
            } else {
                g.credsBad = true;
            }
            clearValue(c);
        } else if (c == gToken) {
            switch (g.token.add(v.data(), v.size())) {
                case setup::TokenAssembler::Result::Complete:
                    g.tokenComplete = true;
                    break;
                case setup::TokenAssembler::Result::Error:
                    g.tokenBad = true;
                    break;
                case setup::TokenAssembler::Result::More:
                    break;
            }
            clearValue(c);
        }
    }
};

ServerCallbacks gServerCallbacks;
CharCallbacks gCharCallbacks;

constexpr uint32_t kRead = NIMBLE_PROPERTY::READ | NIMBLE_PROPERTY::READ_ENC |
                           NIMBLE_PROPERTY::READ_AUTHEN;
constexpr uint32_t kWrite = NIMBLE_PROPERTY::WRITE | NIMBLE_PROPERTY::WRITE_ENC |
                            NIMBLE_PROPERTY::WRITE_AUTHEN;

setup::WifiCreds gTested;  // credentials under test, saved only if they work

}  // namespace

void BleSetup::newPasskey() {
    gPasskey.store(esp_random() % 1000000u);
    NimBLEDevice::setSecurityPasskey(gPasskey.load());
}

void BleSetup::begin(const char* deviceId) {
    machine_.begin(millis(), setupstore::fails());
    wifi_.beginIdle();

    const std::string id(deviceId);
    const std::string name = HS_SETUP_NAME_PREFIX + id.substr(id.size() - 4);
    NimBLEDevice::init(name);
    NimBLEDevice::setMTU(HS_SETUP_MTU);
    // Bonding off: every setup pairs again with a fresh passkey.
    NimBLEDevice::setSecurityAuth(false /* bond */, true /* mitm */, true /* sc */);
    NimBLEDevice::setSecurityIOCap(BLE_HS_IO_DISPLAY_ONLY);
    NimBLEDevice::deleteAllBonds();
    newPasskey();

    gServer = NimBLEDevice::createServer();
    gServer->setCallbacks(&gServerCallbacks, false);
    gServer->advertiseOnDisconnect(false);  // loop() decides

    NimBLEService* svc = gServer->createService(HS_SETUP_UUID_SERVICE);
    NimBLECharacteristic* info = svc->createCharacteristic(HS_SETUP_UUID_INFO, kRead);
    info->setValue(setup::encodeInfo(deviceId, HS_FW_VERSION, HS_SETUP_PROTO));
    gWifiScan = svc->createCharacteristic(HS_SETUP_UUID_WIFI_SCAN, kWrite);
    gWifiList = svc->createCharacteristic(HS_SETUP_UUID_WIFI_LIST,
                                          kRead | NIMBLE_PROPERTY::NOTIFY);
    gWifiList->setValue("[]");
    gWifiCreds = svc->createCharacteristic(HS_SETUP_UUID_WIFI_CREDS, kWrite);
    gToken = svc->createCharacteristic(HS_SETUP_UUID_TOKEN, kWrite);
    gStatus = svc->createCharacteristic(HS_SETUP_UUID_STATUS, kRead | NIMBLE_PROPERTY::NOTIFY);
    for (NimBLECharacteristic* c : {gWifiScan, gWifiCreds, gToken}) {
        c->setCallbacks(&gCharCallbacks);
    }
    svc->start();
    notifyStatus();

    NimBLEAdvertising* adv = NimBLEDevice::getAdvertising();
    adv->setName(name);
    adv->addServiceUUID(HS_SETUP_UUID_SERVICE);
    adv->enableScanResponse(true);

    LOGI("setup", "BLE setup as \"%s\" (fails so far: %u)", name.c_str(),
         (unsigned)machine_.fails());
    if (machine_.advertising()) {
        startAdvertising();
    }
    showState();
}

void BleSetup::startAdvertising() {
    NimBLEDevice::startAdvertising();
    LOGI("setup", "advertising");
}

void BleSetup::stopAdvertising() {
    NimBLEDevice::stopAdvertising();
    if (gServer != nullptr) {
        for (uint16_t h : gServer->getPeerDevices()) {
            gServer->disconnect(h);
        }
    }
}

void BleSetup::restart(uint32_t nowMs) {
    machine_.onBootHold(nowMs);
    setupstore::setFails(0);
    newPasskey();
    pinShown_ = false;
    LOGI("setup", "BOOT held: lockout cleared");
    startAdvertising();
    showState();
}

void BleSetup::notifyStatus(const char* reason) {
    if (gStatus == nullptr) {
        return;
    }
    gStatus->setValue(setup::encodeStatus(machine_.statusName(), reason));
    gStatus->notify();
}

void BleSetup::showState() {
    shown_ = machine_.state();
    switch (shown_) {
        case State::Advertising:
            animator_.showSpriteWithText(sprites::kHeart, "SET UP", true);
            break;
        case State::Connected:
            animator_.showSpriteWithText(sprites::kHeart, "PAIRING", true);
            break;
        case State::Ready:
            animator_.showSpriteWithText(sprites::kHeart, "PAIRED", true);
            break;
        case State::WifiConnecting:
            animator_.showSpriteWithText(sprites::kHeart, "WIFI...", true);
            break;
        case State::WifiOk:
            animator_.showSpriteWithText(sprites::kHeart, "WIFI OK", true);
            break;
        case State::WifiFailed:
            animator_.showSpriteWithText(sprites::kHeart, "WIFI FAIL", true);
            break;
        case State::SigningIn:
            animator_.showSpriteWithText(sprites::kHeart, "SIGNING IN", true);
            break;
        case State::SignedIn:
            animator_.showSpriteWithText(sprites::kHeart, "DONE", true);
            break;
        case State::Locked:
            animator_.showTestScreen("LOCKED HOLD BOOT");
            break;
        case State::TimedOut:
            animator_.showTestScreen("HOLD BOOT");
            break;
    }
}

void BleSetup::handleWifiTest(uint32_t nowMs) {
    if (machine_.state() != State::WifiConnecting) {
        return;
    }
    if (wifi_.connected()) {
        machine_.onWifiResult(true);
        wifistore::save(gTested);
        LOGI("setup", "Wi-Fi \"%s\" works; saved", gTested.ssid.c_str());
        wipe(gTested.pass);
        notifyStatus();
        showState();
        return;
    }
    const uint32_t elapsed = nowMs - wifiStartMs_;
    const uint8_t reason = wifi_.lastDisconnectReason();
    // Give a first transient disconnect a few seconds before failing on it.
    if ((reason != 0 && elapsed >= 8000) || elapsed >= HS_SETUP_WIFI_CONNECT_MS) {
        const char* why = reason != 0 ? setup::wifiFailReason(reason) : "timeout";
        wifi_.stop();
        wipe(gTested.pass);
        machine_.onWifiResult(false);
        LOGW("setup", "Wi-Fi test failed (%s)", why);
        notifyStatus(why);
        showState();
    }
}

void BleSetup::loop(uint32_t nowMs) {
    // Take the queued work.
    bool connected, disconnected, pinRequested, scanRequested, credsPending, credsBad;
    bool tokenComplete, tokenBad;
    int auth;
    setup::WifiCreds creds;
    std::string token;
    {
        std::lock_guard<std::mutex> lock(g.m);
        connected = g.connected;
        disconnected = g.disconnected;
        pinRequested = g.pinRequested;
        auth = g.auth;
        scanRequested = g.scanRequested;
        credsPending = g.credsPending;
        credsBad = g.credsBad;
        tokenComplete = g.tokenComplete;
        tokenBad = g.tokenBad;
        if (credsPending) {
            creds = g.creds;
            wipe(g.creds.pass);
            g.creds = {};
        }
        if (tokenComplete) {
            token = g.token.token();
            g.token.clear();
        }
        g.connected = g.disconnected = g.pinRequested = false;
        g.scanRequested = g.credsPending = g.credsBad = false;
        g.tokenComplete = g.tokenBad = false;
        g.auth = -1;
    }

    const uint8_t failsBefore = machine_.fails();

    if (connected) {
        machine_.onConnect();
        LOGI("setup", "phone connected");
    }
    if (pinRequested) {
        pinShown_ = true;
        char text[12];
        snprintf(text, sizeof(text), "PIN %06u", (unsigned)gPasskey.load());
        animator_.showTestScreen(text);  // shown, never logged
        memset(text, 0, sizeof(text));
        shown_ = machine_.state();  // keep the PIN on screen until the state moves on
        LOGI("setup", "pairing: passkey shown on the display");
    }
    if (auth == 1) {
        machine_.onAuth(true, nowMs);
        LOGI("setup", "paired (LE Secure Connections, authenticated)");
        notifyStatus();
        showState();
    } else if (auth == 0) {
        machine_.onAuth(false, nowMs);
        LOGW("setup", "pairing failed (%u of %u)", (unsigned)machine_.fails(),
             (unsigned)HS_SETUP_MAX_FAILS);
        newPasskey();
        pinShown_ = false;
    }
    if (disconnected) {
        if (pinShown_ && machine_.state() == State::Connected) {
            // Passkey shown but the session ended unpaired: counts as a wrong try.
            machine_.onAuth(false, nowMs);
            LOGW("setup", "pairing abandoned (%u of %u)", (unsigned)machine_.fails(),
                 (unsigned)HS_SETUP_MAX_FAILS);
        }
        if (machine_.state() == State::WifiConnecting) {
            wifi_.stop();
            wipe(gTested.pass);
        }
        machine_.onDisconnect(nowMs);
        newPasskey();
        pinShown_ = false;
        LOGI("setup", "phone disconnected");
        if (machine_.advertising()) {
            startAdvertising();
        }
    }

    if (scanRequested) {
        const State s = machine_.state();
        if (s == State::Ready || s == State::WifiFailed || s == State::WifiOk) {
            if (!wifi_.startScan()) {
                LOGW("setup", "Wi-Fi scan could not start");
            }
        }
    }
    std::vector<setup::WifiNetwork> nets;
    if (wifi_.scanResults(nets)) {
        gWifiList->setValue(setup::encodeWifiList(nets, HS_SETUP_WIFI_LIST_MAX));
        gWifiList->notify();
        LOGI("setup", "Wi-Fi scan: %u networks", (unsigned)nets.size());
    }

    if (credsBad) {
        notifyStatus("bad_creds");
    }
    if (credsPending) {
        if (machine_.onCreds()) {
            wifi_.stop();
            wipe(gTested.pass);
            gTested = creds;
            wifiStartMs_ = nowMs;
            notifyStatus();
            showState();
            wifi_.begin(gTested.ssid.c_str(), gTested.pass.c_str());
        } else {
            notifyStatus("not_ready");
        }
        wipe(creds.pass);
    }
    handleWifiTest(nowMs);

    if (tokenBad) {
        notifyStatus("bad_token");
    }
    if (tokenComplete) {
        if (machine_.onToken()) {
            notifyStatus();
            showState();
            const CloudClient::SignInResult r = cloud_.signInWithCustomToken(token);
            wipe(token);
            machine_.onSignInResult(r == CloudClient::SignInResult::Ok);
            const char* why = nullptr;
            switch (r) {
                case CloudClient::SignInResult::Ok: break;
                case CloudClient::SignInResult::Rejected: why = "token_rejected"; break;
                case CloudClient::SignInResult::WrongBoard: why = "wrong_board"; break;
                case CloudClient::SignInResult::Network: why = "network"; break;
                case CloudClient::SignInResult::Disabled: why = "cloud_disabled"; break;
            }
            notifyStatus(why);
            showState();
            if (r == CloudClient::SignInResult::Ok) {
                signedInMs_ = nowMs;
                setupstore::setForced(false);
                LOGI("setup", "board signed in; restarting into normal mode");
            }
        } else {
            wipe(token);
            notifyStatus("not_ready");
        }
    }

    if (machine_.state() == State::SignedIn &&
        nowMs - signedInMs_ >= HS_SETUP_REBOOT_DELAY_MS) {
        ESP.restart();
    }

    machine_.tick(nowMs);
    if (machine_.fails() != failsBefore) {
        setupstore::setFails(machine_.fails());
    }
    if (machine_.state() != shown_) {
        if (machine_.state() == State::Locked || machine_.state() == State::TimedOut) {
            stopAdvertising();
            LOGW("setup", "%s: hold BOOT 5 s to set up again",
                 machine_.state() == State::Locked ? "locked after wrong passkeys"
                                                   : "setup window closed");
        }
        showState();
    }
}

}  // namespace hs

#endif  // HS_BLE_SETUP
