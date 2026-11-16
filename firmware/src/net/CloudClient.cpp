#include "net/CloudClient.h"

#include <Arduino.h>
#include <HTTPClient.h>
#include <Preferences.h>
#include <WiFi.h>

#include <algorithm>
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
constexpr const char* kKeyCustom = "custom";  // bench serial path only

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

void wipe(std::string& s) {
    std::fill(s.begin(), s.end(), '\0');
    s.clear();
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
    claims_ = fs::BoardClaims{};
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
                state_ = cursor_.empty() ? State::Cursor : State::Polling;
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
                         const std::string& body, bool auth, std::string& response,
                         uint32_t timeoutMs) {
    WiFiClient client;
    HTTPClient http;
    http.setConnectTimeout(HS_CLOUD_HTTP_TIMEOUT_MS);
    http.setTimeout(timeoutMs);
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

bool CloudClient::adopt(const fs::AuthSession& s) {
    fs::BoardClaims c;
    if (!fs::claimsFromIdToken(s.idToken, c) || c.deviceId != deviceId_) {
        // A person's token, a malformed one, or another board's: never use it.
        LOGW("cloud", "credentials are not this board's (uid=%s): set the board up again",
             s.uid.c_str());
        nvsPut(kKeyRefresh, "");
        needsSetup_ = true;
        state_ = State::Disabled;
        return false;
    }
    if (c.coupleId != claims_.coupleId || c.owner != claims_.owner) {
        cursor_.clear();  // a different couple or owner: start a new cursor
    }
    session_ = s;
    claims_ = c;
    needsSetup_ = false;
    nvsPut(kKeyRefresh, s.refreshToken);
    const uint32_t lifeMs = (s.expiresInS > 600 ? s.expiresInS - 300 : 300) * 1000u;
    tokenExpiresMs_ = millis() + lifeMs;
    backoffMs_ = 0;
    nextActionMs_ = millis();
    return true;
}

bool CloudClient::signIn() {
    std::string response;
    std::string refresh = session_.refreshToken.empty() ? nvsGet(kKeyRefresh)
                                                        : session_.refreshToken;
    fs::AuthSession s;
    if (!refresh.empty()) {
        const int st = request("POST", authUrl("securetoken.googleapis.com/v1/token"),
                               "application/x-www-form-urlencoded", fs::refreshBody(refresh),
                               false, response);
        wipe(refresh);
        if (st == 200 && fs::parseRefresh(response.c_str(), s)) {
            LOGI("cloud", "token refreshed, uid=%s", s.uid.c_str());
        } else if (st == 400) {
            LOGW("cloud", "refresh refused (status 400): credentials revoked");
            nvsPut(kKeyRefresh, "");  // revoked or from another emulator run
            s = fs::AuthSession{};
        } else {
            // Network down or server error: keep the credentials and retry later.
            wipe(response);
            fail("token refresh", st);
            return false;
        }
        wipe(response);
    }
    if (s.idToken.empty()) {
#if HS_DEV_SERIAL_TOKEN
        std::string custom = nvsGet(kKeyCustom);
        if (!custom.empty()) {
            const int st = request(
                "POST", authUrl("identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken"),
                "application/json", fs::signInBody(custom), false, response);
            wipe(custom);
            nvsPut(kKeyCustom, "");  // single use, whatever the outcome
            if (st != 200 || !fs::parseSignIn(response.c_str(), s)) {
                wipe(response);
                fail("custom token sign-in", st);
                return false;
            }
            wipe(response);
            LOGI("cloud", "signed in with custom token, uid=%s", s.uid.c_str());
        }
#endif
        if (s.idToken.empty()) {
            LOGW("cloud", "no credentials: hold BOOT 5 s to set the board up");
            needsSetup_ = true;
            nextActionMs_ = millis() + HS_CLOUD_RETRY_MAX_MS;
            return false;
        }
    }
    return adopt(s);
}

CloudClient::SignInResult CloudClient::signInWithCustomToken(const std::string& customToken) {
    if (host_.empty()) {
        return SignInResult::Disabled;
    }
    std::string response;
    const int st = request(
        "POST", authUrl("identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken"),
        "application/json", fs::signInBody(customToken), false, response);
    fs::AuthSession s;
    const bool parsed = st == 200 && fs::parseSignIn(response.c_str(), s);
    wipe(response);
    if (st <= 0) {
        LOGW("cloud", "custom token sign-in: no answer (status %d)", st);
        return SignInResult::Network;
    }
    if (!parsed) {
        LOGW("cloud", "custom token sign-in refused (status %d)", st);
        return SignInResult::Rejected;
    }
    resetSession(State::SignIn);
    if (!adopt(s)) {
        return SignInResult::WrongBoard;
    }
    state_ = State::Cursor;
    LOGI("cloud", "signed in as %s (couple %s, owner %s)", claims_.uid.c_str(),
         claims_.coupleId.c_str(), claims_.owner.c_str());
    return SignInResult::Ok;
}

bool CloudClient::heartbeat(bool setCursor) {
    std::string response;
    const std::string body = fs::heartbeatBody(HS_FIREBASE_PROJECT_ID, claims_.coupleId,
                                               deviceId_, claims_.owner, HS_FW_VERSION, true);
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
    const int st = request("POST", docsUrl("/couples/" + claims_.coupleId + ":runQuery"),
                           "application/json", fs::eventsQueryBody(cursor_, 5), true, response);
    std::vector<fs::RemoteEvent> events;
    std::string newest;
    if (st != 200 || !fs::parseEventsQuery(response.c_str(), claims_.owner, events, &newest)) {
        fail("poll events", st);
        return false;
    }
    for (const fs::RemoteEvent& e : events) {
        bus_.publish(e.event);
    }
    if (!newest.empty()) {
        cursor_ = newest;  // also moves past the owner's own events
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
    const int st = request("POST", url, "application/json", "{\"data\":{}}", true, response,
                           HS_CLOUD_CALL_TIMEOUT_MS);
    if (st != 200) {
        LOGW("cloud", "sendHeart failed (status %d)", st);
        return false;
    }
    LOGI("cloud", "heart sent");
    return true;
}

#if HS_DEV_SERIAL_TOKEN
void CloudClient::provisionCustomToken(const char* token) {
    if (token == nullptr || strlen(token) < 20) {
        LOGW("cloud", "token rejected: too short");
        return;
    }
    nvsPut(kKeyCustom, token);
    nvsPut(kKeyRefresh, "");
    LOGI("cloud", "custom token stored (%u chars); signing in", (unsigned)strlen(token));
    if (!host_.empty()) {
        needsSetup_ = false;
        resetSession(State::SignIn);
    }
}
#endif

void CloudClient::forget() {
    nvsPut(kKeyCustom, "");
    nvsPut(kKeyRefresh, "");
    LOGI("cloud", "stored tokens erased");
    if (!host_.empty()) {
        resetSession(State::SignIn);
    }
}

bool CloudClient::hasCredentials() const { return !nvsGet(kKeyRefresh).empty(); }

void CloudClient::logStatus() const {
    static const char* kNames[] = {"disabled", "sign-in", "cursor", "polling"};
    LOGI("cloud", "state=%s uid=%s couple=%s owner=%s%s", kNames[static_cast<int>(state_)],
         claims_.uid.empty() ? "-" : claims_.uid.c_str(),
         claims_.coupleId.empty() ? "-" : claims_.coupleId.c_str(),
         claims_.owner.empty() ? "-" : claims_.owner.c_str(),
         needsSetup_ ? " (needs setup)" : "");
}

}  // namespace hs
