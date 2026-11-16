#include "setup/SetupCodec.h"

#include <ArduinoJson.h>

#include <algorithm>

namespace hs {
namespace setup {

CredsError parseWifiCreds(const uint8_t* data, size_t len, WifiCreds& out) {
    if (data == nullptr || len == 0 || len > kAttrMax) {
        return CredsError::BadJson;
    }
    JsonDocument doc;
    if (deserializeJson(doc, reinterpret_cast<const char*>(data), len) !=
            DeserializationError::Ok ||
        !doc.is<JsonObject>()) {
        return CredsError::BadJson;
    }
    if (!doc["ssid"].is<const char*>()) {
        return CredsError::Ssid;
    }
    const std::string ssid = doc["ssid"].as<const char*>();
    if (ssid.empty() || ssid.size() > 32) {
        return CredsError::Ssid;
    }
    std::string pass;
    if (!doc["pass"].isNull()) {
        if (!doc["pass"].is<const char*>()) {
            return CredsError::Pass;
        }
        pass = doc["pass"].as<const char*>();
    }
    if (!pass.empty() && (pass.size() < 8 || pass.size() > 63)) {
        std::fill(pass.begin(), pass.end(), '\0');
        return CredsError::Pass;
    }
    out.ssid = ssid;
    out.pass = pass;
    std::fill(pass.begin(), pass.end(), '\0');
    return CredsError::None;
}

std::string encodeWifiList(std::vector<WifiNetwork> networks, size_t maxEntries) {
    networks.erase(std::remove_if(networks.begin(), networks.end(),
                                  [](const WifiNetwork& n) { return n.ssid.empty(); }),
                   networks.end());
    std::stable_sort(networks.begin(), networks.end(),
                     [](const WifiNetwork& a, const WifiNetwork& b) { return a.rssi > b.rssi; });
    std::vector<WifiNetwork> unique;
    for (const WifiNetwork& n : networks) {
        const bool seen = std::any_of(unique.begin(), unique.end(),
                                      [&](const WifiNetwork& u) { return u.ssid == n.ssid; });
        if (!seen) {
            unique.push_back(n);  // first one is the strongest
        }
    }
    if (unique.size() > maxEntries) {
        unique.resize(maxEntries);
    }
    while (true) {
        JsonDocument doc;
        JsonArray arr = doc.to<JsonArray>();
        for (const WifiNetwork& n : unique) {
            JsonObject o = arr.add<JsonObject>();
            o["ssid"] = n.ssid;
            o["rssi"] = n.rssi;
            o["open"] = n.open;
        }
        std::string out;
        serializeJson(doc, out);
        if (out.size() <= kAttrMax || unique.empty()) {
            return out;
        }
        unique.pop_back();  // drop the weakest until it fits
    }
}

std::string encodeInfo(const char* deviceId, const char* fw, int proto) {
    JsonDocument doc;
    doc["deviceId"] = deviceId;
    doc["fw"] = fw;
    doc["proto"] = proto;
    std::string out;
    serializeJson(doc, out);
    return out;
}

std::string encodeStatus(const char* state, const char* reason) {
    JsonDocument doc;
    doc["state"] = state;
    if (reason != nullptr && *reason != '\0') {
        doc["reason"] = reason;
    }
    std::string out;
    serializeJson(doc, out);
    return out;
}

const char* wifiFailReason(uint8_t disconnectReason) {
    switch (disconnectReason) {
        case 2:    // AUTH_EXPIRE
        case 15:   // 4WAY_HANDSHAKE_TIMEOUT: usually a wrong password
        case 202:  // AUTH_FAIL
        case 204:  // HANDSHAKE_TIMEOUT
            return "auth";
        case 201:  // NO_AP_FOUND
            return "no_ap";
        default:
            return "other";
    }
}

TokenAssembler::Result TokenAssembler::add(const uint8_t* data, size_t len) {
    if (data == nullptr || len == 0) {
        clear();
        return Result::Error;
    }
    const uint8_t flags = data[0];
    if (flags & 0x01) {
        clear();
        started_ = true;
        buf_.reserve(maxLen_);  // no reallocation: no stray copies of the token
    } else if (!started_) {
        clear();
        return Result::Error;
    }
    if (buf_.size() + (len - 1) > maxLen_) {
        clear();
        return Result::Error;
    }
    buf_.append(reinterpret_cast<const char*>(data + 1), len - 1);
    if (flags & 0x02) {
        started_ = false;
        return buf_.empty() ? (clear(), Result::Error) : Result::Complete;
    }
    return Result::More;
}

void TokenAssembler::clear() {
    std::fill(buf_.begin(), buf_.end(), '\0');
    buf_.clear();
    buf_.shrink_to_fit();
    started_ = false;
}

}  // namespace setup
}  // namespace hs
