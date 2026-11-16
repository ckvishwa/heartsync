#include "net/CloudClient.h"

#include <Arduino.h>
#include <HTTPClient.h>
#include <Preferences.h>
#include <WiFi.h>

#include <vector>

#include "config.h"

#if __has_include("secrets.h")
#include "secrets.h"
#else
#include "secrets.example.h"
#endif

#include "util/Log.h"

// Older secrets.h files may not define these yet.
#ifndef HS_FIREBASE_EMULATOR_HOST
#define HS_FIREBASE_EMULATOR_HOST ""
#endif
#ifndef HS_FIREBASE_API_KEY
#define HS_FIREBASE_API_KEY ""
#endif
#ifndef HS_FIREBASE_PROJECT_ID
#define HS_FIREBASE_PROJECT_ID "demo-heartsync"
#endif

namespace hs {

namespace {

constexpr const char* kNvsNamespace = "hs-cloud";
constexpr const char* kKeyRefresh = "refresh";
constexpr const char* kKeyCustom = "custom";

std::string nvsGet(const char* key) {
    Preferences p;
    if (!p.begin(kNvsNamespace, true)) {
        return {};
    }
    String v = p.isKey(key) ? p.getString(key, "") : String();
    p.end();
    return std::string(v.c_str());
}

void nvsPut(const char* key, const std::string& value) {
    Preferences p;
    if (!p.begin(kNvsNamespace, false)) {
        return;
    }
    if (value.empty()) {
        p.remove(key);
    } else {
        p.putString(key, value.c_str());
    }
    p.end();
}

bool due(uint32_t now, uint32_t at) { return static_cast<int32_t>(now - at) >= 0; }

}  // namespace

void CloudClient::begin(const char* deviceId) {
    deviceId_ = deviceId;
    host_ = HS_FIREBASE_EMULATOR_HOST;
    apiKey_ = HS_FIREBASE_API_KEY;
    if (apiKey_.empty()) {
        apiKey_ = "demo-key";  // the emulator accepts any key
    }
    if (host_.empty()) {
        LOGW("cloud",
             "HS_FIREBASE_EMULATOR_HOST not set in secrets.h: sync disabled (real project is a "
             "later Phase 2 item)");
        state_ = State::Disabled;
        return;
    }
    LOGI("cloud", "emulator %s, project %s, device %s", host_.c_str(), HS_FIREBASE_PROJECT_ID,
         deviceId_);
    resetSession(State::SignIn);
}

void CloudClient::resetSession(State next) {
    state_ = next;
    session_ = fs::AuthSession{};
    coupleId_.clear();
    partnerUid_.clear();
    cursor_.clear();
    nextActionMs_ = millis();
    backoffMs_ = 0;
}

void CloudClient::fail(const char* what, int status) {
    backoffMs_ = backoffMs_ == 0 ? HS_CLOUD_RETRY_MIN_MS : backoffMs_ * 2;
    if (backoffMs_ > HS_CLOUD_RETRY_MAX_MS) {
        backoffMs_ = HS_CLOUD_RETRY_MAX_MS;
    }
    nextActionMs_ = millis() + backoffMs_;
    LOGW("cloud", "%s failed (status %d), retry in %u ms", what, status, (unsigned)backoffMs_);
    if (status == 401 || status == 403) {
        // Token rejected or rules denied: start again from sign-in.
        state_ = State::SignIn;
    }
}

void CloudClient::loop(bool wifiConnected) {
    if (state_ == State::Disabled || !wifiConnected) {
        return;
    }
    const uint32_t now = millis();
    if (!due(now, nextActionMs_)) {
        return;
    }
    if (state_ != State::SignIn && due(now, tokenExpiresMs_)) {
        state_ = State::SignIn;  // refresh before the ID token expires
    }
    switch (state_) {
        case State::SignIn:
            if (signIn()) {
                state_ = coupleId_.empty() ? State::Profile : State::Polling;
            }
            break;
        case State::Profile:
            if (loadProfile()) {
                state_ = State::Cursor;
            }
            break;
        case State::Cursor:
            if (heartbeat(true)) {
                state_ = State::Polling;
                LOGI("cloud", "ready: listening for events from the partner");
            }
            break;
        case State::Polling:
            if (due(now, nextHeartbeatMs_)) {
                heartbeat(false);
            } else {
                poll();
            }
            break;
        case State::Disabled:
            break;
    }
}

std::string CloudClient::authUrl(const char* path) const {
    // Emulator: http://<host>:9099/<real host>/<path>?key=<key>
    return "http://" + host_ + ":" + std::to_string(HS_EMU_PORT_AUTH) + "/" + path +
           "?key=" + apiKey_;
}

std::string CloudClient::docsUrl(const std::string& path) const {
    return "http://" + host_ + ":" + std::to_string(HS_EMU_PORT_FIRESTORE) + "/v1/projects/" +
           HS_FIREBASE_PROJECT_ID + "/databases/(default)/documents" + path;
}

int CloudClient::request(const char* method, const std::string& url, const char* contentType,
                         const std::string& body, bool auth, std::string& response) {
    WiFiClient client;
    HTTPClient http;
    http.setConnectTimeout(HS_CLOUD_HTTP_TIMEOUT_MS);
    http.setTimeout(HS_CLOUD_HTTP_TIMEOUT_MS);
    if (!http.begin(client, url.c_str())) {
        return -1;
    }
    if (contentType != nullptr) {
        http.addHeader("Content-Type", contentType);
    }
    if (auth) {
        http.addHeader("Authorization", ("Bearer " + session_.idToken).c_str());
    }
    const int status = body.empty() && strcmp(method, "GET") == 0
                           ? http.GET()
                           : http.sendRequest(method, (uint8_t*)body.data(), body.size());
    if (status > 0) {
        response = http.getString().c_str();
    }
    http.end();
    return status;
}

bool CloudClient::signIn() {
    std::string response;
    const std::string refresh = session_.refreshToken.empty() ? nvsGet(kKeyRefresh)
                                                              : session_.refreshToken;
    fs::AuthSession s;
    if (!refresh.empty()) {
        const int st = request("POST", authUrl("securetoken.googleapis.com/v1/token"),
                               "application/x-www-form-urlencoded", fs::refreshBody(refresh),
                               false, response);
        if (st == 200 && fs::parseRefresh(response.c_str(), s)) {
            LOGI("cloud", "token refreshed, uid=%s", s.uid.c_str());
        } else {
            LOGW("cloud", "refresh failed (status %d)", st);
            if (st == 400) {
                nvsPut(kKeyRefresh, "");  // revoked or from another emulator run
            }
            s = fs::AuthSession{};
        }
    }
    if (s.idToken.empty()) {
        const std::string custom = nvsGet(kKeyCustom);
        if (custom.empty()) {
            LOGW("cloud", "no credentials: provision a custom token over serial (`token <jwt>`)");
            nextActionMs_ = millis() + HS_CLOUD_RETRY_MAX_MS;
            return false;
        }
        const int st = request(
            "POST", authUrl("identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken"),
            "application/json", fs::signInBody(custom), false, response);
        if (st != 200 || !fs::parseSignIn(response.c_str(), s)) {
            fail("custom token sign-in", st);
            return false;
        }
        nvsPut(kKeyCustom, "");  // single use: from now on the refresh token is the credential
        LOGI("cloud", "signed in with custom token, uid=%s", s.uid.c_str());
    }
    if (!session_.uid.empty() && session_.uid != s.uid) {
        coupleId_.clear();  // a different owner: reload the profile
    }
    session_ = s;
    nvsPut(kKeyRefresh, s.refreshToken);
    const uint32_t lifeMs = (s.expiresInS > 600 ? s.expiresInS - 300 : 300) * 1000u;
    tokenExpiresMs_ = millis() + lifeMs;
    backoffMs_ = 0;
    nextActionMs_ = millis();
    return true;
}

bool CloudClient::loadProfile() {
    std::string response;
    int st = request("GET", docsUrl("/users/" + session_.uid), nullptr, "", true, response);
    if (st != 200 || !fs::parseUserCoupleId(response.c_str(), coupleId_)) {
        fail("read users/{uid}.coupleId", st);
        return false;
    }
    st = request("GET", docsUrl("/couples/" + coupleId_), nullptr, "", true, response);
    if (st != 200 || !fs::parseCouplePartner(response.c_str(), session_.uid, partnerUid_)) {
        fail("read couple members", st);
        return false;
    }
    LOGI("cloud", "couple=%s owner=%s partner=%s", coupleId_.c_str(), session_.uid.c_str(),
         partnerUid_.c_str());
    backoffMs_ = 0;
    return true;
}

bool CloudClient::heartbeat(bool setCursor) {
    std::string response;
    const std::string body = fs::heartbeatBody(HS_FIREBASE_PROJECT_ID, coupleId_, deviceId_,
                                               session_.uid, HS_FW_VERSION, true);
    const int st = request("POST", docsUrl(":commit"), "application/json", body, true, response);
    std::string commitTime;
    if (st != 200 || !fs::parseCommitTime(response.c_str(), commitTime)) {
        fail("heartbeat", st);
        return false;
    }
    if (setCursor || cursor_.empty()) {
        cursor_ = commitTime;
    }
    nextHeartbeatMs_ = millis() + HS_CLOUD_HEARTBEAT_MS;
    nextActionMs_ = millis() + HS_CLOUD_POLL_MS;
    backoffMs_ = 0;
    LOGI("cloud", "heartbeat ok (online, fw %s)", HS_FW_VERSION);
    return true;
}

bool CloudClient::poll() {
    std::string response;
    const int st = request("POST", docsUrl("/couples/" + coupleId_ + ":runQuery"),
                           "application/json", fs::eventsQueryBody(partnerUid_, cursor_, 5), true,
                           response);
    std::vector<fs::RemoteEvent> events;
    if (st != 200 || !fs::parseEventsQuery(response.c_str(), session_.uid, events)) {
        fail("poll events", st);
        return false;
    }
    for (const fs::RemoteEvent& e : events) {
        cursor_ = e.createdAt;
        bus_.publish(e.event);
    }
    backoffMs_ = 0;
    nextActionMs_ = millis() + HS_CLOUD_POLL_MS;
    return true;
}

bool CloudClient::sendHeart() {
    if (state_ != State::Polling) {
        LOGW("cloud", "sendHeart: not signed in yet");
        return false;
    }
    std::string response;
    const std::string url = "http://" + host_ + ":" + std::to_string(HS_EMU_PORT_FUNCTIONS) + "/" +
                            HS_FIREBASE_PROJECT_ID + "/" + HS_FUNCTIONS_REGION + "/sendHeart";
    const int st = request("POST", url, "application/json", "{\"data\":{}}", true, response);
    if (st != 200) {
        LOGW("cloud", "sendHeart failed (status %d)", st);
        return false;
    }
    LOGI("cloud", "heart sent");
    return true;
}

void CloudClient::provisionCustomToken(const char* token) {
    if (token == nullptr || strlen(token) < 20) {
        LOGW("cloud", "token rejected: too short");
        return;
    }
    nvsPut(kKeyCustom, token);
    nvsPut(kKeyRefresh, "");
    LOGI("cloud", "custom token stored (%u chars); signing in", (unsigned)strlen(token));
    if (!host_.empty()) {
        resetSession(State::SignIn);
    }
}

void CloudClient::forget() {
    nvsPut(kKeyCustom, "");
    nvsPut(kKeyRefresh, "");
    LOGI("cloud", "stored tokens erased");
    if (!host_.empty()) {
        resetSession(State::SignIn);
    }
}

void CloudClient::logStatus() const {
    static const char* kNames[] = {"disabled", "sign-in", "profile", "cursor", "polling"};
    LOGI("cloud", "state=%s uid=%s couple=%s partner=%s", kNames[static_cast<int>(state_)],
         session_.uid.empty() ? "-" : session_.uid.c_str(),
         coupleId_.empty() ? "-" : coupleId_.c_str(),
         partnerUid_.empty() ? "-" : partnerUid_.c_str());
}

}  // namespace hs
