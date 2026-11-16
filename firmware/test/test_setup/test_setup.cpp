// Native tests for the BLE setup codec, state machine and BOOT gestures.
// Run: pio test -e native
#include <unity.h>

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

void test_wifi_list() {
    std::vector<WifiNetwork> nets = {
        {"Weak", -90, false}, {"", -30, true},  // hidden: dropped
        {"Home", -70, false}, {"Home", -50, false},  // duplicate: strongest kept
        {"Cafe \"Q\"", -60, true},
    };
    const std::string json = encodeWifiList(nets, 20);
    TEST_ASSERT_EQUAL_STRING(
        R"([{"ssid":"Home","rssi":-50,"open":false},{"ssid":"Cafe \"Q\"","rssi":-60,"open":true},)"
        R"({"ssid":"Weak","rssi":-90,"open":false}])",
        json.c_str());
    TEST_ASSERT_EQUAL_STRING(R"([{"ssid":"Home","rssi":-50,"open":false}])",
                             encodeWifiList(nets, 1).c_str());
    TEST_ASSERT_EQUAL_STRING("[]", encodeWifiList({}, 20).c_str());

    // 30 long names never exceed one attribute value.
    std::vector<WifiNetwork> many;
    for (int i = 0; i < 30; i++) {
        many.push_back({std::string(30, 'a' + (i % 26)) + std::to_string(i), -40 - i, false});
    }
    const std::string big = encodeWifiList(many, 20);
    TEST_ASSERT_TRUE(big.size() <= kAttrMax);
    TEST_ASSERT_TRUE(big.find("-40") != std::string::npos);  // strongest kept
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

static TokenAssembler::Result chunk(TokenAssembler& t, uint8_t flags, const std::string& s) {
    std::string b(1, static_cast<char>(flags));
    b += s;
    return t.add(reinterpret_cast<const uint8_t*>(b.data()), b.size());
}

void test_token_assembler() {
    TokenAssembler t(1536);
    TEST_ASSERT_TRUE(chunk(t, 0x01, std::string(500, 'a')) == TokenAssembler::Result::More);
    TEST_ASSERT_TRUE(chunk(t, 0x00, std::string(500, 'b')) == TokenAssembler::Result::More);
    TEST_ASSERT_TRUE(chunk(t, 0x02, "end") == TokenAssembler::Result::Complete);
    TEST_ASSERT_EQUAL(1003, t.token().size());
    TEST_ASSERT_EQUAL('b', t.token()[999]);
    t.clear();
    TEST_ASSERT_TRUE(t.token().empty());

    // Single chunk.
    TEST_ASSERT_TRUE(chunk(t, 0x03, "abc") == TokenAssembler::Result::Complete);
    TEST_ASSERT_EQUAL_STRING("abc", t.token().c_str());
    // Continuation without a first chunk.
    t.clear();
    TEST_ASSERT_TRUE(chunk(t, 0x00, "x") == TokenAssembler::Result::Error);
    TEST_ASSERT_TRUE(chunk(t, 0x02, "x") == TokenAssembler::Result::Error);
    // A new first chunk restarts.
    TEST_ASSERT_TRUE(chunk(t, 0x01, "old") == TokenAssembler::Result::More);
    TEST_ASSERT_TRUE(chunk(t, 0x03, "new") == TokenAssembler::Result::Complete);
    TEST_ASSERT_EQUAL_STRING("new", t.token().c_str());
    // Too long.
    TokenAssembler small(10);
    TEST_ASSERT_TRUE(chunk(small, 0x01, "123456") == TokenAssembler::Result::More);
    TEST_ASSERT_TRUE(chunk(small, 0x02, "78901") == TokenAssembler::Result::Error);
    TEST_ASSERT_TRUE(small.token().empty());
    // Empty token, empty write.
    TEST_ASSERT_TRUE(chunk(small, 0x03, "") == TokenAssembler::Result::Error);
    TEST_ASSERT_TRUE(small.add(nullptr, 0) == TokenAssembler::Result::Error);
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

int main(int, char**) {
    UNITY_BEGIN();
    RUN_TEST(test_wifi_creds);
    RUN_TEST(test_wifi_list);
    RUN_TEST(test_info_status_reasons);
    RUN_TEST(test_token_assembler);
    RUN_TEST(test_machine_happy_path);
    RUN_TEST(test_machine_lockout_and_timeout);
    RUN_TEST(test_long_press);
    return UNITY_END();
}
