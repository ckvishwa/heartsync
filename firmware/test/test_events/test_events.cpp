// Native tests for event encoding and the event bus. Run: pio test -e native
#include <unity.h>

#include <string>

#include "events/Event.h"
#include "events/EventBus.h"
#include "events/EventCodec.h"

void setUp() {}
void tearDown() {}

void test_type_names_round_trip() {
    const hs::EventType types[] = {hs::EventType::Heart, hs::EventType::Touch, hs::EventType::Art,
                                   hs::EventType::Mood, hs::EventType::Voice};
    for (hs::EventType t : types) {
        TEST_ASSERT_TRUE(hs::eventTypeFromName(hs::eventTypeName(t)) == t);
    }
    TEST_ASSERT_EQUAL_STRING("heart", hs::eventTypeName(hs::EventType::Heart));
    TEST_ASSERT_TRUE(hs::eventTypeFromName("nope") == hs::EventType::Unknown);
    TEST_ASSERT_TRUE(hs::eventTypeFromName(nullptr) == hs::EventType::Unknown);
}

void test_encode_heart() {
    hs::Event e;
    e.type = hs::EventType::Heart;
    e.from = "uidA";
    TEST_ASSERT_EQUAL_STRING("{\"type\":\"heart\",\"from\":\"uidA\",\"payload\":{}}",
                             hs::encodeEvent(e).c_str());
}

void test_encode_with_payload() {
    hs::Event e;
    e.type = hs::EventType::Mood;
    e.from = "uidB";
    e.payloadJson = "{\"mood\":\"happy\"}";
    TEST_ASSERT_EQUAL_STRING("{\"type\":\"mood\",\"from\":\"uidB\",\"payload\":{\"mood\":\"happy\"}}",
                             hs::encodeEvent(e).c_str());
}

void test_encode_rejects_invalid() {
    hs::Event e;
    TEST_ASSERT_TRUE(hs::encodeEvent(e).empty());  // unknown type
    e.type = hs::EventType::Heart;
    TEST_ASSERT_TRUE(hs::encodeEvent(e).empty());  // no sender
    e.from = "uidA";
    e.payloadJson = "[1,2]";
    TEST_ASSERT_TRUE(hs::encodeEvent(e).empty());  // payload not an object
    e.payloadJson = "{broken";
    TEST_ASSERT_TRUE(hs::encodeEvent(e).empty());
}

void test_decode_round_trip() {
    hs::Event in;
    in.type = hs::EventType::Touch;
    in.from = "uidA";
    in.payloadJson = "{\"pattern\":\"tap\"}";
    hs::Event out;
    TEST_ASSERT_TRUE(hs::decodeEvent(hs::encodeEvent(in).c_str(), out));
    TEST_ASSERT_TRUE(out.type == hs::EventType::Touch);
    TEST_ASSERT_EQUAL_STRING("uidA", out.from.c_str());
    TEST_ASSERT_EQUAL_STRING("{\"pattern\":\"tap\"}", out.payloadJson.c_str());
}

void test_decode_ignores_extra_fields_and_defaults_payload() {
    hs::Event out;
    TEST_ASSERT_TRUE(
        hs::decodeEvent("{\"type\":\"heart\",\"from\":\"uidB\",\"createdAt\":123}", out));
    TEST_ASSERT_TRUE(out.type == hs::EventType::Heart);
    TEST_ASSERT_EQUAL_STRING("{}", out.payloadJson.c_str());
}

void test_decode_rejects_bad_input() {
    hs::Event out;
    out.from = "untouched";
    TEST_ASSERT_FALSE(hs::decodeEvent(nullptr, out));
    TEST_ASSERT_FALSE(hs::decodeEvent("", out));
    TEST_ASSERT_FALSE(hs::decodeEvent("not json", out));
    TEST_ASSERT_FALSE(hs::decodeEvent("{\"type\":\"explode\",\"from\":\"uidA\"}", out));
    TEST_ASSERT_FALSE(hs::decodeEvent("{\"type\":\"heart\"}", out));
    TEST_ASSERT_FALSE(hs::decodeEvent("{\"type\":\"heart\",\"from\":\"\"}", out));
    TEST_ASSERT_EQUAL_STRING("untouched", out.from.c_str());
}

namespace {
int g_calls = 0;
std::string g_order;
void handlerA(const hs::Event&, void*) {
    ++g_calls;
    g_order += "A";
}
void handlerB(const hs::Event& e, void* ctx) {
    ++g_calls;
    g_order += "B";
    *static_cast<hs::EventType*>(ctx) = e.type;
}
}  // namespace

void test_bus_delivers_in_order() {
    hs::EventBus bus;
    hs::EventType seen = hs::EventType::Unknown;
    g_calls = 0;
    g_order.clear();
    TEST_ASSERT_TRUE(bus.subscribe(handlerA));
    TEST_ASSERT_TRUE(bus.subscribe(handlerB, &seen));
    hs::Event e;
    e.type = hs::EventType::Heart;
    e.from = "uidA";
    bus.publish(e);
    TEST_ASSERT_EQUAL(2, g_calls);
    TEST_ASSERT_EQUAL_STRING("AB", g_order.c_str());
    TEST_ASSERT_TRUE(seen == hs::EventType::Heart);
}

void test_bus_rejects_null_and_overflow() {
    hs::EventBus bus;
    TEST_ASSERT_FALSE(bus.subscribe(nullptr));
    for (size_t i = 0; i < hs::EventBus::kMaxSubscribers; ++i) {
        TEST_ASSERT_TRUE(bus.subscribe(handlerA));
    }
    TEST_ASSERT_FALSE(bus.subscribe(handlerA));
    TEST_ASSERT_EQUAL(hs::EventBus::kMaxSubscribers, bus.subscriberCount());
}

int main(int, char**) {
    UNITY_BEGIN();
    RUN_TEST(test_type_names_round_trip);
    RUN_TEST(test_encode_heart);
    RUN_TEST(test_encode_with_payload);
    RUN_TEST(test_encode_rejects_invalid);
    RUN_TEST(test_decode_round_trip);
    RUN_TEST(test_decode_ignores_extra_fields_and_defaults_payload);
    RUN_TEST(test_decode_rejects_bad_input);
    RUN_TEST(test_bus_delivers_in_order);
    RUN_TEST(test_bus_rejects_null_and_overflow);
    return UNITY_END();
}
