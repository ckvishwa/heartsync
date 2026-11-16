#include "ble/BleSetup.h"

#if HS_BLE_SETUP

#include <Arduino.h>
#include <NimBLEDevice.h>

#include <algorithm>
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
    bool confirmRequested = false;  // numeric comparison: code to show
    uint16_t confirmHandle = 0;
    uint32_t confirmCode = 0;
    int auth = -1;  // -1 none, 0 failed, 1 ok
    bool scanRequested = false;
    int pageRequested = -1;  // wifiScan 0x02 <page>
    bool credsPending = false;
    bool credsBad = false;
    setup::WifiCreds creds;
    bool tokenComplete = false;
    bool tokenBad = false;
    setup::TokenAssembler token{HS_SETUP_TOKEN_MAX};
    std::string tokenDone;  // a finished token, moved out of the assembler at once
};

Shared g;
NimBLEServer* gServer = nullptr;
NimBLECharacteristic* gWifiScan = nullptr;
NimBLECharacteristic* gWifiList = nullptr;
NimBLECharacteristic* gWifiCreds = nullptr;
NimBLECharacteristic* gToken = nullptr;
NimBLECharacteristic* gStatus = nullptr;

void clearValue(NimBLECharacteristic* c) {
    // Do not leave secrets in the attribute's own buffer: overwrite the old bytes
    // first (setting length 0 alone keeps them), then empty it.
    static const uint8_t kZeros[setup::kAttrMax] = {0};
    const size_t len = c->getValue().size();
    c->setValue(kZeros, len < sizeof(kZeros) ? len : sizeof(kZeros));
    c->setValue(kZeros, 0);
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
        wipe(g.tokenDone);
        g.tokenComplete = false;
    }

    // Numeric comparison: NimBLE waits for injectConfirmPasskey(). loop() shows
    // the code and answers it (BOOT tap = accept, timeout = reject).
    void onConfirmPassKey(NimBLEConnInfo& info, uint32_t code) override {
        std::lock_guard<std::mutex> lock(g.m);
        g.confirmRequested = true;
        g.confirmHandle = info.getConnHandle();
        g.confirmCode = code;
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
            const setup::ScanCommand cmd = setup::parseScanCommand(v.data(), v.size());
            if (cmd.startScan) {
                g.scanRequested = true;
            } else if (cmd.selectPage) {
                g.pageRequested = cmd.page;
            }
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
                    wipe(g.tokenDone);
                    g.tokenDone = g.token.token();
                    g.token.clear();
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

namespace {

std::vector<std::string> gPages;  // Wi-Fi list pages from the last scan (loop() only)

// wifiList notification: one byte, the page now readable. Never the page itself
// (a notification holds only MTU-3 bytes; the app reads the value).
void signalPage(uint8_t page) {
    if (gWifiList != nullptr) {
        gWifiList->notify(&page, 1);
    }
}

}  // namespace

void BleSetup::endConfirm() {
    confirmPending_ = false;
    confirmHandle_ = 0;
}

void BleSetup::confirm(uint32_t pressStartMs) {
    if (!confirmPending_ || gServer == nullptr) {
        return;  // nothing waiting: a stray tap does nothing, and is not kept
    }
    if (static_cast<int32_t>(pressStartMs - confirmStartMs_) < 0) {
        LOGW("setup", "BOOT was pressed before the code appeared: tap again");
        return;
    }
    const uint16_t h = confirmHandle_;
    endConfirm();
    if (NimBLEDevice::injectConfirmPasskey(gServer->getPeerInfoByHandle(h), true)) {
        animator_.showSpriteWithText(sprites::kHeart, "PAIRING", true);
        LOGI("setup", "pairing code confirmed with BOOT");
    } else {
        LOGW("setup", "pairing ended before the BOOT tap");
    }
}

void BleSetup::begin(const char* deviceId) {
    machine_.begin(millis(), setupstore::fails());
    wifi_.beginIdle();

    const std::string id(deviceId);
    const std::string name = HS_SETUP_NAME_PREFIX + id.substr(id.size() - 4);
    NimBLEDevice::init(name);
    NimBLEDevice::setMTU(HS_SETUP_MTU);
    // Bonding on, because Android's standard pairing flow (createBond) expects it,
    // but no bond outlives a setup session: every setup starts by deleting all
    // bonds, so each phone pairs again with a fresh code. The app removes its
    // stale bond before connecting. DisplayYesNo on both sides gives numeric
    // comparison (LE Secure Connections, MITM-protected); the "yes" is BOOT.
    NimBLEDevice::setSecurityAuth(true /* bond */, true /* mitm */, true /* sc */);
    NimBLEDevice::setSecurityIOCap(BLE_HS_IO_DISPLAY_YESNO);
    NimBLEDevice::deleteAllBonds();

    gServer = NimBLEDevice::createServer();
    gServer->setCallbacks(&gServerCallbacks, false);
    gServer->advertiseOnDisconnect(false);  // loop() decides

    NimBLEService* svc = gServer->createService(HS_SETUP_UUID_SERVICE);
    NimBLECharacteristic* info = svc->createCharacteristic(HS_SETUP_UUID_INFO, kRead);
    info->setValue(setup::encodeInfo(deviceId, HS_FW_VERSION, HS_SETUP_PROTO));
    gWifiScan = svc->createCharacteristic(HS_SETUP_UUID_WIFI_SCAN, kWrite);
    gWifiList = svc->createCharacteristic(HS_SETUP_UUID_WIFI_LIST,
                                          kRead | NIMBLE_PROPERTY::NOTIFY);
    gPages = setup::encodeWifiPages({}, HS_SETUP_WIFI_LIST_MAX);
    gWifiList->setValue(gPages[0]);
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
    stopAdvertising();  // also drops any connected phone
    if (machine_.state() == State::WifiConnecting) {
        wifi_.stop();
    }
    wipe(gTested.pass);
    NimBLEDevice::deleteAllBonds();
    machine_.onBootHold(nowMs);
    setupstore::setFails(0);
    endConfirm();
    codeShown_ = false;
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
    uint8_t reason = wifi_.lastDisconnectReason();
    if (reason == 8) {
        reason = 0;  // ASSOC_LEAVE: our own disconnect before this test, not a verdict
    }
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
    bool connected, disconnected, confirmRequested, scanRequested, credsPending, credsBad;
    bool tokenComplete, tokenBad;
    int auth, pageRequested;
    uint16_t confirmHandle;
    uint32_t confirmCode;
    setup::WifiCreds creds;
    std::string token;
    {
        std::lock_guard<std::mutex> lock(g.m);
        connected = g.connected;
        disconnected = g.disconnected;
        confirmRequested = g.confirmRequested;
        confirmHandle = g.confirmHandle;
        confirmCode = g.confirmCode;
        g.confirmCode = 0;
        auth = g.auth;
        scanRequested = g.scanRequested;
        pageRequested = g.pageRequested;
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
            std::swap(token, g.tokenDone);
        }
        g.connected = g.disconnected = g.confirmRequested = false;
        g.scanRequested = g.credsPending = g.credsBad = false;
        g.pageRequested = -1;
        g.tokenComplete = g.tokenBad = false;
        g.auth = -1;
    }

    const uint8_t failsBefore = machine_.fails();

    if (connected) {
        machine_.onConnect();
        connectedMs_ = nowMs;
        LOGI("setup", "phone connected");
    }
    // A phone that connects and never pairs must not hold the board forever.
    if (machine_.state() == State::Connected && nowMs - connectedMs_ >= kPairingDeadlineMs &&
        gServer != nullptr) {
        LOGW("setup", "no pairing within %u s: disconnecting",
             (unsigned)(kPairingDeadlineMs / 1000));
        for (uint16_t h : gServer->getPeerDevices()) {
            gServer->disconnect(h);
        }
        connectedMs_ = nowMs;  // do not repeat until the disconnect lands
    }
    if (confirmRequested) {
        codeShown_ = true;
        confirmPending_ = true;
        confirmHandle_ = confirmHandle;
        confirmStartMs_ = nowMs;
        char text[17];  // the OLED line fits 16 characters
        snprintf(text, sizeof(text), "TAP BOOT %06u", (unsigned)(confirmCode % 1000000u));
        animator_.showTestScreen(text);  // shown, never logged
        memset(text, 0, sizeof(text));
        confirmCode = 0;
        shown_ = machine_.state();  // keep the code on screen until the state moves on
        LOGI("setup", "pairing: code shown, waiting for a BOOT tap");
    }
    // Nobody tapped BOOT in time: reject. The failed pairing counts as one try.
    if (confirmPending_ && nowMs - confirmStartMs_ >= HS_SETUP_CONFIRM_MS && gServer != nullptr) {
        const uint16_t h = confirmHandle_;
        endConfirm();
        (void)NimBLEDevice::injectConfirmPasskey(gServer->getPeerInfoByHandle(h), false);
        LOGW("setup", "pairing not confirmed with BOOT within %u s: rejected",
             (unsigned)(HS_SETUP_CONFIRM_MS / 1000));
    }
    if (auth != -1) {
        endConfirm();
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
        codeShown_ = false;
    }
    if (disconnected) {
        endConfirm();
        if (codeShown_ && machine_.state() == State::Connected) {
            // Code shown but the session ended unpaired: counts as a failed try.
            machine_.onAuth(false, nowMs);
            LOGW("setup", "pairing abandoned (%u of %u)", (unsigned)machine_.fails(),
                 (unsigned)HS_SETUP_MAX_FAILS);
        }
        if (machine_.state() == State::WifiConnecting) {
            wifi_.stop();
            wipe(gTested.pass);
        }
        machine_.onDisconnect(nowMs);
        NimBLEDevice::deleteAllBonds();  // a fresh pairing for every session
        codeShown_ = false;
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
        gPages = setup::encodeWifiPages(nets, HS_SETUP_WIFI_LIST_MAX);
        gWifiList->setValue(gPages[0]);
        signalPage(0);
        LOGI("setup", "Wi-Fi scan: %u networks, %u pages", (unsigned)nets.size(),
             (unsigned)gPages.size());
    }
    if (pageRequested >= 0 && static_cast<size_t>(pageRequested) < gPages.size()) {
        gWifiList->setValue(gPages[pageRequested]);
        signalPage(static_cast<uint8_t>(pageRequested));
    }  // out of range: ignored (the app times out)

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
            wifi_.beginTest(gTested.ssid.c_str(), gTested.pass.c_str());
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
