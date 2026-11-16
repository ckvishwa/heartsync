#include "net/WifiStore.h"

#include <Preferences.h>

#include <algorithm>

namespace hs {
namespace wifistore {

namespace {
constexpr const char* kNs = "hs-wifi";
}

bool load(setup::WifiCreds& out) {
    Preferences p;
    if (!p.begin(kNs, true)) {
        return false;
    }
    const bool has = p.isKey("ssid");
    if (has) {
        out.ssid = p.getString("ssid", "").c_str();
        out.pass = p.getString("pass", "").c_str();
    }
    p.end();
    return has && !out.ssid.empty();
}

void save(const setup::WifiCreds& creds) {
    Preferences p;
    if (!p.begin(kNs, false)) {
        return;
    }
    p.putString("ssid", creds.ssid.c_str());
    p.putString("pass", creds.pass.c_str());
    p.end();
}

void erase() {
    Preferences p;
    if (p.begin(kNs, false)) {
        p.clear();
        p.end();
    }
}

}  // namespace wifistore

namespace setupstore {

namespace {
constexpr const char* kNs = "hs-setup";
}

uint8_t fails() {
    Preferences p;
    if (!p.begin(kNs, true)) {
        return 0;
    }
    const uint8_t n = p.isKey("fails") ? p.getUChar("fails", 0) : 0;
    p.end();
    return n;
}

void setFails(uint8_t n) {
    Preferences p;
    if (p.begin(kNs, false)) {
        p.putUChar("fails", n);
        p.end();
    }
}

bool forced() {
    Preferences p;
    if (!p.begin(kNs, true)) {
        return false;
    }
    const bool on = p.isKey("force") && p.getBool("force", false);
    p.end();
    return on;
}

void setForced(bool on) {
    Preferences p;
    if (p.begin(kNs, false)) {
        p.putBool("force", on);
        p.end();
    }
}

}  // namespace setupstore
}  // namespace hs
