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

// wifiList pages: {"page":n,"pages":N,"nets":[{"ssid","rssi","open"}]}. Networks
// are strongest first, one entry per SSID (the strongest), hidden ones dropped,
// at most `maxEntries` in total. Each page fits in kAttrMax; there is always at
// least one page (an empty list is one page with no nets). Control characters
// in SSIDs are escaped as \u00XX so strict JSON parsers accept every page.
std::vector<std::string> encodeWifiPages(std::vector<WifiNetwork> networks, size_t maxEntries);

// wifiScan write: 0x01 starts a scan (any other single byte too, for
// compatibility); 0x02 then a page number selects the page wifiList returns.
struct ScanCommand {
    bool startScan = false;
    bool selectPage = false;
    uint8_t page = 0;
};
ScanCommand parseScanCommand(const uint8_t* data, size_t len);

// info value: {"deviceId","fw","proto"}.
std::string encodeInfo(const char* deviceId, const char* fw, int proto);

// status value: {"state"} or {"state","reason"}. Never carries secrets.
std::string encodeStatus(const char* state, const char* reason = nullptr);

// Arduino/ESP-IDF Wi-Fi disconnect reason -> status reason for wifi_failed:
// "auth" (wrong password), "no_ap" (network not found), or "other".
const char* wifiFailReason(uint8_t disconnectReason);

// CRC-32 (IEEE 802.3, the zlib one): crc32("123456789") == 0xCBF43926.
uint32_t crc32(const uint8_t* data, size_t len);

// Token frames (proto 2). A real custom token is about 1 KB, more than one
// attribute value (512 bytes), so the app writes it in numbered chunks (the app
// uses 180 bytes, which fits one plain write at the default iOS MTU; the board
// accepts up to kTokenChunkMax), then an end frame:
//   chunk: 0x10, seq, 1..kTokenChunkMax token bytes   (seq 0 starts a token)
//   end:   0x11, len (uint16 LE), crc32 (uint32 LE)    (exactly 7 bytes)
constexpr uint8_t kTokenChunk = 0x10;
constexpr uint8_t kTokenEnd = 0x11;
constexpr size_t kTokenChunkMax = kAttrMax - 2;

// Reassembles the token in RAM. Seq 0 drops anything collected so far; every
// other chunk must carry the next seq (no gaps, no repeats). Any bad frame, a
// token over `maxLen`, or an end frame whose length or CRC does not match is
// an error and wipes the buffer. The caller wipes it on disconnect and after
// sign-in (clear()). Never stored in NVS.
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
    Result fail() {
        clear();
        return Result::Error;
    }

    size_t maxLen_;
    std::string buf_;
    bool started_ = false;
    uint8_t nextSeq_ = 0;
};

}  // namespace setup
}  // namespace hs
