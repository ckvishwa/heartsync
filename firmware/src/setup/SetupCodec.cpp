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

namespace {

std::string encodePage(const std::vector<WifiNetwork>& nets, size_t from, size_t to, size_t page,
                       size_t pages) {
    JsonDocument doc;
    doc["page"] = page;
    doc["pages"] = pages;
    JsonArray arr = doc["nets"].to<JsonArray>();
    for (size_t i = from; i < to; i++) {
        JsonObject o = arr.add<JsonObject>();
        o["ssid"] = nets[i].ssid;
        o["rssi"] = nets[i].rssi;
        o["open"] = nets[i].open;
    }
    std::string raw;
    serializeJson(doc, raw);
    // ArduinoJson writes control characters other than \b \f \n \r \t \0 as raw
    // bytes, which strict JSON parsers (Dart's jsonDecode) refuse. They can only
    // occur inside strings here (SSIDs), so escape them as \u00XX.
    std::string out;
    out.reserve(raw.size());
    static const char kHex[] = "0123456789abcdef";
    for (const char ch : raw) {
        const uint8_t b = static_cast<uint8_t>(ch);
        if (b < 0x20) {
            out += "\\u00";
            out += kHex[b >> 4];
            out += kHex[b & 0x0f];
        } else {
            out += ch;
        }
    }
    return out;
}

}  // namespace

std::vector<std::string> encodeWifiPages(std::vector<WifiNetwork> networks, size_t maxEntries) {
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
    // Split greedily so each page fits; "pages" is patched in once the count is
    // known (it is at most two digits, so the size check uses a 2-digit value).
    std::vector<std::pair<size_t, size_t>> ranges;
    size_t from = 0;
    while (from < unique.size()) {
        size_t to = from + 1;
        while (to < unique.size() && encodePage(unique, from, to + 1, 99, 99).size() <= kAttrMax) {
            to++;
        }
        ranges.emplace_back(from, to);
        from = to;
    }
    if (ranges.empty()) {
        ranges.emplace_back(0, 0);
    }
    std::vector<std::string> pages;
    for (size_t i = 0; i < ranges.size(); i++) {
        pages.push_back(encodePage(unique, ranges[i].first, ranges[i].second, i, ranges.size()));
    }
    return pages;
}

ScanCommand parseScanCommand(const uint8_t* data, size_t len) {
    ScanCommand c;
    if (data == nullptr || len == 0) {
        return c;
    }
    if (data[0] == 0x02 && len >= 2) {
        c.selectPage = true;
        c.page = data[1];
    } else {
        c.startScan = true;
    }
    return c;
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

uint32_t crc32(const uint8_t* data, size_t len) {
    uint32_t crc = 0xFFFFFFFFu;
    for (size_t i = 0; i < len; i++) {
        crc ^= data[i];
        for (int b = 0; b < 8; b++) {
            crc = (crc >> 1) ^ (0xEDB88320u & (0u - (crc & 1u)));
        }
    }
    return ~crc;
}

TokenAssembler::Result TokenAssembler::add(const uint8_t* data, size_t len) {
    if (data == nullptr || len < 2) {
        return fail();
    }
    if (data[0] == kTokenChunk) {
        const uint8_t seq = data[1];
        const size_t n = len - 2;
        if (n == 0 || n > kTokenChunkMax) {
            return fail();
        }
        if (seq == 0) {
            clear();
            started_ = true;
            buf_.reserve(maxLen_);  // no reallocation: no stray copies of the token
        } else if (!started_ || seq != nextSeq_) {
            return fail();  // missing, repeated or out-of-order chunk
        }
        if (buf_.size() + n > maxLen_) {
            return fail();
        }
        buf_.append(reinterpret_cast<const char*>(data + 2), n);
        nextSeq_ = static_cast<uint8_t>(seq + 1);
        if (nextSeq_ == 0) {
            return fail();  // 256 chunks: far over any token size
        }
        return Result::More;
    }
    if (data[0] == kTokenEnd && len == 7) {
        if (!started_ || buf_.empty()) {
            return fail();
        }
        const size_t want = static_cast<size_t>(data[1]) | (static_cast<size_t>(data[2]) << 8);
        const uint32_t crc = static_cast<uint32_t>(data[3]) | (static_cast<uint32_t>(data[4]) << 8) |
                             (static_cast<uint32_t>(data[5]) << 16) |
                             (static_cast<uint32_t>(data[6]) << 24);
        if (want != buf_.size() ||
            crc != crc32(reinterpret_cast<const uint8_t*>(buf_.data()), buf_.size())) {
            return fail();
        }
        started_ = false;
        nextSeq_ = 0;
        return Result::Complete;
    }
    return fail();  // unknown frame (a proto 1 app sends 0x01..0x03 flags)
}

void TokenAssembler::clear() {
    std::fill(buf_.begin(), buf_.end(), '\0');
    buf_.clear();
    buf_.shrink_to_fit();
    started_ = false;
    nextSeq_ = 0;
}

}  // namespace setup
}  // namespace hs
