// Wire format of the BLE setup service (docs/protocol.md "BLE provisioning").
// Hardware-free: compiles in native tests. No logging here: these buffers carry
// the Wi-Fi password and the custom token.
#pragma once

#include <stddef.h>
#include <stdint.h>

#include <string>
#include <vector>

namespace hs {
namespace setup {

// Largest attribute value BLE allows (ATT spec). Every characteristic value
// must fit: the token is therefore sent in chunks (TokenAssembler).
constexpr size_t kAttrMax = 512;

struct WifiCreds {
    std::string ssid;  // 1..32 bytes, kept exactly (spaces included)
    std::string pass;  // empty (open network) or 8..63 bytes
};

enum class CredsError { None, BadJson, Ssid, Pass };

// wifiCreds write: {"ssid": "...", "pass": "..."} ("pass" may be omitted).
CredsError parseWifiCreds(const uint8_t* data, size_t len, WifiCreds& out);

struct WifiNetwork {
    std::string ssid;
    int rssi = 0;
    bool open = false;
};

// wifiList value: [{"ssid","rssi","open"}], strongest first, one entry per SSID
// (the strongest), hidden networks dropped, at most `maxEntries`, and trimmed
// so the JSON fits in kAttrMax.
std::string encodeWifiList(std::vector<WifiNetwork> networks, size_t maxEntries);

// info value: {"deviceId","fw","proto"}.
std::string encodeInfo(const char* deviceId, const char* fw, int proto);

// status value: {"state"} or {"state","reason"}. Never carries secrets.
std::string encodeStatus(const char* state, const char* reason = nullptr);

// Arduino/ESP-IDF Wi-Fi disconnect reason -> status reason for wifi_failed:
// "auth" (wrong password), "no_ap" (network not found), or "other".
const char* wifiFailReason(uint8_t disconnectReason);

// Reassembles the custom token from token-characteristic writes. Each write is
// one flags byte then up to kAttrMax-1 token bytes:
//   bit 0 (0x01) first chunk: drop anything collected so far
//   bit 1 (0x02) last chunk: the token is complete
// A chunk without "first" before any first chunk, or a token over `maxLen`,
// is an error and clears the buffer.
class TokenAssembler {
public:
    enum class Result { More, Complete, Error };

    explicit TokenAssembler(size_t maxLen) : maxLen_(maxLen) {}
    ~TokenAssembler() { clear(); }

    Result add(const uint8_t* data, size_t len);
    // The finished token (valid after Complete until clear()).
    const std::string& token() const { return buf_; }
    // Overwrites and frees the buffer.
    void clear();

private:
    size_t maxLen_;
    std::string buf_;
    bool started_ = false;
};

}  // namespace setup
}  // namespace hs
