// Native tests for the BLE setup codec, state machine and BOOT gestures.
// Run: pio test -e native
#include <ArduinoJson.h>
#include <unity.h>

#include <initializer_list>

#include <string>
#include <vector>

#include "setup/LongPress.h"
#include "setup/SetupCodec.h"
#include "setup/SetupMachine.h"

using namespace hs::setup;

void setUp() {}
void tearDown() {}

static CredsError creds(const std::string& json, WifiCreds& out) {
    return parseWifiCreds(reinterpret_cast<const uint8_t*>(json.data()), json.size(), out);
}

void test_wifi_creds() {
    WifiCreds c;
    TEST_ASSERT_TRUE(creds(R"({"ssid":"Home","pass":"correct horse"})", c) == CredsError::None);
    TEST_ASSERT_EQUAL_STRING("Home", c.ssid.c_str());
    TEST_ASSERT_EQUAL_STRING("correct horse", c.pass.c_str());

    // A trailing space is part of the SSID (a real bench hotspot has one).
    TEST_ASSERT_TRUE(creds(R"({"ssid":"DeltaForce ","pass":""})", c) == CredsError::None);
    TEST_ASSERT_EQUAL_STRING("DeltaForce ", c.ssid.c_str());
    TEST_ASSERT_TRUE(c.pass.empty());
    // Open network: pass omitted.
    TEST_ASSERT_TRUE(creds(R"({"ssid":"Cafe"})", c) == CredsError::None);
    // UTF-8 SSID: limit is 32 bytes, not characters.
    TEST_ASSERT_TRUE(creds("{\"ssid\":\"caf\xC3\xA9\"}", c) == CredsError::None);
    TEST_ASSERT_EQUAL(5, c.ssid.size());

    WifiCreds untouched;
    untouched.ssid = "keep";
    TEST_ASSERT_TRUE(creds(R"({"ssid":""})", untouched) == CredsError::Ssid);
    TEST_ASSERT_TRUE(creds(R"({"ssid":"123456789012345678901234567890123"})", untouched) ==
                     CredsError::Ssid);  // 33 bytes
    TEST_ASSERT_TRUE(creds(R"({"pass":"12345678"})", untouched) == CredsError::Ssid);
    TEST_ASSERT_TRUE(creds(R"({"ssid":"Home","pass":"short"})", untouched) == CredsError::Pass);
    TEST_ASSERT_TRUE(creds(std::string(R"({"ssid":"Home","pass":")") + std::string(64, 'a') + "\"}",
                           untouched) == CredsError::Pass);
    TEST_ASSERT_TRUE(creds(R"({"ssid":"Home","pass":12345678})", untouched) == CredsError::Pass);
    TEST_ASSERT_TRUE(creds("not json", untouched) == CredsError::BadJson);
    TEST_ASSERT_TRUE(creds("[]", untouched) == CredsError::BadJson);
    TEST_ASSERT_TRUE(parseWifiCreds(nullptr, 0, untouched) == CredsError::BadJson);
    TEST_ASSERT_EQUAL_STRING("keep", untouched.ssid.c_str());  // errors change nothing
}

// Parses one page and checks its shape; returns the SSIDs in order.
static std::vector<std::string> pageSsids(const std::string& json, size_t page, size_t pages) {
    JsonDocument doc;
    TEST_ASSERT_TRUE(deserializeJson(doc, json) == DeserializationError::Ok);
    TEST_ASSERT_EQUAL(page, doc["page"].as<size_t>());
    TEST_ASSERT_EQUAL(pages, doc["pages"].as<size_t>());
    TEST_ASSERT_TRUE(doc["nets"].is<JsonArray>());
    std::vector<std::string> out;
    for (JsonObject n : doc["nets"].as<JsonArray>()) {
        out.push_back(n["ssid"].as<std::string>());
    }
    return out;
}

static std::vector<std::string> allSsids(const std::vector<std::string>& pages) {
    std::vector<std::string> out;
    for (size_t i = 0; i < pages.size(); i++) {
        TEST_ASSERT_TRUE(pages[i].size() <= kAttrMax);
        for (const std::string& s : pageSsids(pages[i], i, pages.size())) {
            out.push_back(s);
        }
    }
    return out;
}

void test_wifi_pages_basic() {
    std::vector<WifiNetwork> nets = {
        {"Weak", -90, false}, {"", -30, true},  // hidden: dropped
        {"Home", -70, false}, {"Home", -50, false},  // duplicate: strongest kept
        {"Cafe \"Q\"", -60, true},
    };
    const std::vector<std::string> pages = encodeWifiPages(nets, 40);
    TEST_ASSERT_EQUAL(1, pages.size());
    TEST_ASSERT_EQUAL_STRING(
        R"({"page":0,"pages":1,"nets":[{"ssid":"Home","rssi":-50,"open":false},)"
        R"({"ssid":"Cafe \"Q\"","rssi":-60,"open":true},{"ssid":"Weak","rssi":-90,"open":false}]})",
        pages[0].c_str());
    // The cap counts unique networks, strongest first.
    const std::vector<std::string> one = encodeWifiPages(nets, 1);
    TEST_ASSERT_EQUAL(1, one.size());
    TEST_ASSERT_EQUAL_STRING(
        R"({"page":0,"pages":1,"nets":[{"ssid":"Home","rssi":-50,"open":false}]})", one[0].c_str());
    // Empty (or only hidden) list: still one page.
    const std::vector<std::string> none = encodeWifiPages({{"", -40, true}}, 40);
    TEST_ASSERT_EQUAL(1, none.size());
    TEST_ASSERT_EQUAL_STRING(R"({"page":0,"pages":1,"nets":[]})", none[0].c_str());
    TEST_ASSERT_EQUAL(1, encodeWifiPages({}, 40).size());
}

void test_wifi_pages_many() {
    // 60 networks with long names (and 5 weaker duplicates): capped at 40,
    // strongest first, every page within one attribute value, page/pages right.
    std::vector<WifiNetwork> many;
    for (int i = 0; i < 60; i++) {
        std::string name = std::string(28, static_cast<char>('a' + (i % 26))) + std::to_string(100 + i);
        many.push_back({name, -30 - i, i % 2 == 0});
    }
    for (int i = 0; i < 5; i++) {
        many.push_back({many[i].ssid, -95, false});
    }
    const std::vector<std::string> pages = encodeWifiPages(many, 40);
    TEST_ASSERT_TRUE(pages.size() > 1);
    const std::vector<std::string> ssids = allSsids(pages);
    TEST_ASSERT_EQUAL(40, ssids.size());
    for (size_t i = 0; i < ssids.size(); i++) {
        TEST_ASSERT_EQUAL_STRING(many[i].ssid.c_str(), ssids[i].c_str());
    }
    // 30 networks (about what the bench board sees): all of them arrive.
    many.resize(30);
    TEST_ASSERT_EQUAL(30, allSsids(encodeWifiPages(many, 40)).size());
}

void test_wifi_pages_escaping() {
    // Trailing space, quotes and backslash kept exactly; control characters are
    // escaped (\u0001 is 6 bytes each) and every page still fits.
    std::vector<WifiNetwork> nets = {{"DeltaForce ", -40, true}, {"say \"hi\"\\", -41, false}};
    std::string ctrl(32, '\x01');
    for (int i = 0; i < 20; i++) {
        ctrl[0] = static_cast<char>('A' + i);
        nets.push_back({ctrl, -50 - i, false});
    }
    const std::vector<std::string> pages = encodeWifiPages(nets, 40);
    TEST_ASSERT_TRUE(pages.size() > 1);
    TEST_ASSERT_TRUE(pages[0].find("\\u0001") != std::string::npos);
    const std::vector<std::string> ssids = allSsids(pages);
    TEST_ASSERT_EQUAL(22, ssids.size());
    TEST_ASSERT_EQUAL_STRING("DeltaForce ", ssids[0].c_str());
    TEST_ASSERT_EQUAL_STRING("say \"hi\"\\", ssids[1].c_str());
    TEST_ASSERT_EQUAL(32, ssids[2].size());
    TEST_ASSERT_EQUAL('\x01', ssids[2][31]);
}

static ScanCommand scanCmd(std::initializer_list<uint8_t> bytes) {
    const std::vector<uint8_t> v(bytes);
    return parseScanCommand(v.data(), v.size());
}

void test_scan_command() {
    ScanCommand c = scanCmd({0x01});
    TEST_ASSERT_TRUE(c.startScan);
    TEST_ASSERT_FALSE(c.selectPage);
    TEST_ASSERT_TRUE(scanCmd({0x7F}).startScan);  // any single byte (proto 1 apps)
    c = scanCmd({0x02, 3});
    TEST_ASSERT_TRUE(c.selectPage);
    TEST_ASSERT_FALSE(c.startScan);
    TEST_ASSERT_EQUAL(3, c.page);
    c = parseScanCommand(nullptr, 0);
    TEST_ASSERT_FALSE(c.startScan);
    TEST_ASSERT_FALSE(c.selectPage);
}

void test_info_status_reasons() {
    TEST_ASSERT_EQUAL_STRING(R"({"deviceId":"hs-20500dcd63f4","fw":"0.1.0","proto":1})",
                             encodeInfo("hs-20500dcd63f4", "0.1.0", 1).c_str());
    TEST_ASSERT_EQUAL_STRING(R"({"state":"wifi_ok"})", encodeStatus("wifi_ok").c_str());
    TEST_ASSERT_EQUAL_STRING(R"({"state":"wifi_failed","reason":"auth"})",
                             encodeStatus("wifi_failed", "auth").c_str());
    TEST_ASSERT_EQUAL_STRING("auth", wifiFailReason(202));
    TEST_ASSERT_EQUAL_STRING("auth", wifiFailReason(15));
    TEST_ASSERT_EQUAL_STRING("auth", wifiFailReason(2));
    TEST_ASSERT_EQUAL_STRING("no_ap", wifiFailReason(201));
    TEST_ASSERT_EQUAL_STRING("other", wifiFailReason(8));
}

using R = TokenAssembler::Result;

static R frame(TokenAssembler& t, const std::vector<uint8_t>& f) { return t.add(f.data(), f.size()); }

static std::vector<uint8_t> chunkFrame(uint8_t seq, const std::string& s) {
    std::vector<uint8_t> f = {kTokenChunk, seq};
    f.insert(f.end(), s.begin(), s.end());
    return f;
}

static std::vector<uint8_t> endFrame(size_t len, uint32_t crc) {
    return {kTokenEnd,
            static_cast<uint8_t>(len),
            static_cast<uint8_t>(len >> 8),
            static_cast<uint8_t>(crc),
            static_cast<uint8_t>(crc >> 8),
            static_cast<uint8_t>(crc >> 16),
            static_cast<uint8_t>(crc >> 24)};
}

static uint32_t crcOf(const std::string& s) {
    return crc32(reinterpret_cast<const uint8_t*>(s.data()), s.size());
}

// Sends `tok` the way the app does: 180-byte chunks, then the end frame.
static R sendToken(TokenAssembler& t, const std::string& tok) {
    uint8_t seq = 0;
    for (size_t at = 0; at < tok.size(); at += 180) {
        if (frame(t, chunkFrame(seq++, tok.substr(at, 180))) != R::More) {
            return R::Error;
        }
    }
    return frame(t, endFrame(tok.size(), crcOf(tok)));
}

// A ~1 KB token, like a real Firebase custom token (the emulator's are shorter).
static std::string bigToken() {
    std::string s = "eyJhbGciOiJSUzI1NiJ9.";
    while (s.size() < 1000) {
        s += static_cast<char>('A' + (s.size() * 7) % 26);
    }
    return s;
}

void test_crc32() {
    TEST_ASSERT_EQUAL_HEX32(0xCBF43926u, crcOf("123456789"));
    TEST_ASSERT_EQUAL_HEX32(0x00000000u, crc32(nullptr, 0));
}

void test_token_assembler() {
    const std::string tok = bigToken();
    TokenAssembler t(1536);
    TEST_ASSERT_TRUE(sendToken(t, tok) == R::Complete);
    TEST_ASSERT_EQUAL_STRING(tok.c_str(), t.token().c_str());
    t.clear();
    TEST_ASSERT_TRUE(t.token().empty());

    // Single chunk; a new seq 0 after Complete starts over.
    TEST_ASSERT_TRUE(sendToken(t, "abc") == R::Complete);
    TEST_ASSERT_TRUE(sendToken(t, "xyz") == R::Complete);
    TEST_ASSERT_EQUAL_STRING("xyz", t.token().c_str());
    // A new seq 0 mid-token restarts.
    TEST_ASSERT_TRUE(frame(t, chunkFrame(0, "old")) == R::More);
    TEST_ASSERT_TRUE(frame(t, chunkFrame(0, "new")) == R::More);
    TEST_ASSERT_TRUE(frame(t, endFrame(3, crcOf("new"))) == R::Complete);
    TEST_ASSERT_EQUAL_STRING("new", t.token().c_str());
}

void test_token_assembler_errors() {
    const std::string tok = bigToken();
    TokenAssembler t(1536);
    // Bad checksum.
    TEST_ASSERT_TRUE(frame(t, chunkFrame(0, "abc")) == R::More);
    TEST_ASSERT_TRUE(frame(t, endFrame(3, crcOf("abd"))) == R::Error);
    TEST_ASSERT_TRUE(t.token().empty());
    // Wrong length.
    TEST_ASSERT_TRUE(frame(t, chunkFrame(0, "abc")) == R::More);
    TEST_ASSERT_TRUE(frame(t, endFrame(4, crcOf("abc"))) == R::Error);
    // Missing chunk (seq 1 skipped).
    TEST_ASSERT_TRUE(frame(t, chunkFrame(0, tok.substr(0, 180))) == R::More);
    TEST_ASSERT_TRUE(frame(t, chunkFrame(2, tok.substr(360, 180))) == R::Error);
    TEST_ASSERT_TRUE(t.token().empty());
    // Duplicate chunk.
    TEST_ASSERT_TRUE(frame(t, chunkFrame(0, "ab")) == R::More);
    TEST_ASSERT_TRUE(frame(t, chunkFrame(1, "cd")) == R::More);
    TEST_ASSERT_TRUE(frame(t, chunkFrame(1, "cd")) == R::Error);
    // Continuation or end without seq 0.
    TEST_ASSERT_TRUE(frame(t, chunkFrame(1, "x")) == R::Error);
    TEST_ASSERT_TRUE(frame(t, endFrame(1, crcOf("x"))) == R::Error);
    // Oversized: 1600 bytes into a 1536-byte buffer.
    TEST_ASSERT_TRUE(sendToken(t, std::string(1600, 'z')) == R::Error);
    TEST_ASSERT_TRUE(t.token().empty());
    TokenAssembler small(10);
    TEST_ASSERT_TRUE(frame(small, chunkFrame(0, "123456")) == R::More);
    TEST_ASSERT_TRUE(frame(small, chunkFrame(1, "78901")) == R::Error);
    // Chunk over one attribute value, empty chunk, unknown or short frames.
    TEST_ASSERT_TRUE(frame(t, chunkFrame(0, std::string(kTokenChunkMax + 1, 'a'))) == R::Error);
    TEST_ASSERT_TRUE(frame(t, chunkFrame(0, "")) == R::Error);
    TEST_ASSERT_TRUE(frame(t, {0x01, 'a', 'b'}) == R::Error);  // proto 1 first/last flags
    TEST_ASSERT_TRUE(frame(t, {0x03, 'a', 'b'}) == R::Error);
    TEST_ASSERT_TRUE(frame(t, {kTokenEnd, 3, 0}) == R::Error);
    TEST_ASSERT_TRUE(t.add(nullptr, 0) == R::Error);
    // An error mid-token wipes it: the end frame for the old data then fails.
    TEST_ASSERT_TRUE(frame(t, chunkFrame(0, "abc")) == R::More);
    TEST_ASSERT_TRUE(frame(t, {0x99, 0}) == R::Error);
    TEST_ASSERT_TRUE(frame(t, endFrame(3, crcOf("abc"))) == R::Error);
}

void test_machine_happy_path() {
    SetupMachine m(3, 1000);
    m.begin(0, 0);
    TEST_ASSERT_TRUE(m.advertising());
    TEST_ASSERT_FALSE(m.onCreds());  // not connected
    m.onConnect();
    TEST_ASSERT_FALSE(m.onCreds());  // not paired yet
    TEST_ASSERT_FALSE(m.onToken());
    m.onAuth(true, 10);
    TEST_ASSERT_TRUE(m.state() == State::Ready);
    TEST_ASSERT_FALSE(m.onToken());  // token before Wi-Fi
    TEST_ASSERT_TRUE(m.onCreds());
    TEST_ASSERT_EQUAL_STRING("wifi_connecting", m.statusName());
    m.onWifiResult(false);
    TEST_ASSERT_EQUAL_STRING("wifi_failed", m.statusName());
    TEST_ASSERT_TRUE(m.onCreds());  // retry with the right password
    m.onWifiResult(true);
    TEST_ASSERT_EQUAL_STRING("wifi_ok", m.statusName());
    TEST_ASSERT_TRUE(m.onToken());
    m.onSignInResult(false);  // rejected token: may send another
    TEST_ASSERT_TRUE(m.state() == State::WifiOk);
    TEST_ASSERT_TRUE(m.onToken());
    m.onSignInResult(true);
    TEST_ASSERT_EQUAL_STRING("signed_in", m.statusName());
    m.onDisconnect(50);
    TEST_ASSERT_TRUE(m.state() == State::SignedIn);  // stays done
}

void test_machine_lockout_and_timeout() {
    SetupMachine m(3, 1000);
    m.begin(0, 1);  // one wrong passkey before a reboot
    m.onConnect();
    m.onAuth(false, 10);
    TEST_ASSERT_EQUAL(2, m.fails());
    TEST_ASSERT_TRUE(m.advertising());
    m.onConnect();
    m.onAuth(false, 20);
    TEST_ASSERT_TRUE(m.state() == State::Locked);
    m.onConnect();
    TEST_ASSERT_TRUE(m.state() == State::Locked);
    m.onDisconnect(30);
    m.tick(5000);
    TEST_ASSERT_TRUE(m.state() == State::Locked);
    m.onBootHold(6000);
    TEST_ASSERT_TRUE(m.advertising());
    TEST_ASSERT_EQUAL(0, m.fails());

    // Locked from the stored count at boot.
    SetupMachine b(3, 1000);
    b.begin(0, 3);
    TEST_ASSERT_TRUE(b.state() == State::Locked);

    // A good pairing clears the count.
    SetupMachine g(3, 1000);
    g.begin(0, 2);
    g.onConnect();
    g.onAuth(true, 1);
    TEST_ASSERT_EQUAL(0, g.fails());

    // Window: times out only while nobody is connected.
    SetupMachine w(3, 1000);
    w.begin(0, 0);
    w.tick(999);
    TEST_ASSERT_TRUE(w.advertising());
    w.onConnect();
    w.tick(5000);
    TEST_ASSERT_TRUE(w.state() == State::Connected);
    w.onDisconnect(5000);
    w.tick(5999);
    TEST_ASSERT_TRUE(w.advertising());
    w.tick(6000);
    TEST_ASSERT_TRUE(w.state() == State::TimedOut);
    TEST_ASSERT_EQUAL_STRING("timed_out", w.statusName());
}

void test_long_press() {
    using A = hs::LongPress::Action;
    hs::LongPress p(30, 1000, 5000);
    TEST_ASSERT_TRUE(p.update(false, 0) == A::None);
    // Tap: down at 100, up at 400.
    TEST_ASSERT_TRUE(p.update(true, 100) == A::None);
    TEST_ASSERT_TRUE(p.update(true, 130) == A::None);
    TEST_ASSERT_TRUE(p.pressed());
    TEST_ASSERT_EQUAL(200, p.heldMs(300));
    TEST_ASSERT_TRUE(p.update(false, 400) == A::None);
    TEST_ASSERT_TRUE(p.update(false, 430) == A::Tap);
    TEST_ASSERT_EQUAL(100, p.pressStartMs());  // pairing confirm: press must start after the code
    TEST_ASSERT_EQUAL(0, p.heldMs(500));

    // Medium press (2 s): nothing.
    p.update(true, 1000);
    p.update(true, 1030);
    p.update(false, 3000);
    TEST_ASSERT_TRUE(p.update(false, 3030) == A::None);

    // Hold: fires once at 5 s, no tap on release.
    p.update(true, 10000);
    TEST_ASSERT_TRUE(p.update(true, 14999) == A::None);
    TEST_ASSERT_TRUE(p.update(true, 15000) == A::Hold);
    TEST_ASSERT_TRUE(p.update(true, 20000) == A::None);
    p.update(false, 21000);
    TEST_ASSERT_TRUE(p.update(false, 21030) == A::None);

    // Bounces shorter than the debounce never count.
    TEST_ASSERT_TRUE(p.update(true, 30000) == A::None);
    TEST_ASSERT_TRUE(p.update(false, 30010) == A::None);
    TEST_ASSERT_TRUE(p.update(false, 30100) == A::None);
    TEST_ASSERT_FALSE(p.pressed());
}

void test_review_gaps() {
    // SetupMachine: auth events after pairing are ignored; disconnect mid Wi-Fi
    // test goes back to advertising; a refused token can be retried.
    SetupMachine m(3, 1000);
    m.begin(0, 0);
    m.onConnect();
    m.onAuth(true, 1);
    m.onAuth(false, 2);
    TEST_ASSERT_TRUE(m.state() == State::Ready);
    TEST_ASSERT_EQUAL(0, m.fails());
    TEST_ASSERT_TRUE(m.onCreds());
    m.onDisconnect(3);
    TEST_ASSERT_TRUE(m.advertising());
    m.onWifiResult(true);  // a late result is ignored
    TEST_ASSERT_TRUE(m.advertising());

    SetupMachine r(3, 1000);
    r.begin(0, 0);
    r.onConnect();
    r.onAuth(true, 1);
    r.onCreds();
    r.onWifiResult(true);
    for (int i = 0; i < 3; i++) {
        TEST_ASSERT_TRUE(r.onToken());
        r.onSignInResult(false);
        TEST_ASSERT_TRUE(r.state() == State::WifiOk);
    }

    // LongPress: bounce during a hold neither taps nor fires the hold again.
    using A = hs::LongPress::Action;
    hs::LongPress p(30, 1000, 5000);
    p.update(true, 0);
    p.update(true, 30);
    TEST_ASSERT_TRUE(p.update(true, 5000) == A::Hold);
    TEST_ASSERT_TRUE(p.update(false, 6000) == A::None);  // 10 ms bounce
    TEST_ASSERT_TRUE(p.update(true, 6010) == A::None);
    TEST_ASSERT_TRUE(p.update(true, 12000) == A::None);
    TEST_ASSERT_TRUE(p.pressed());
}

int main(int, char**) {
    UNITY_BEGIN();
    RUN_TEST(test_wifi_creds);
    RUN_TEST(test_wifi_pages_basic);
    RUN_TEST(test_wifi_pages_many);
    RUN_TEST(test_wifi_pages_escaping);
    RUN_TEST(test_scan_command);
    RUN_TEST(test_info_status_reasons);
    RUN_TEST(test_crc32);
    RUN_TEST(test_token_assembler);
    RUN_TEST(test_token_assembler_errors);
    RUN_TEST(test_machine_happy_path);
    RUN_TEST(test_machine_lockout_and_timeout);
    RUN_TEST(test_long_press);
    RUN_TEST(test_review_gaps);
    return UNITY_END();
}
