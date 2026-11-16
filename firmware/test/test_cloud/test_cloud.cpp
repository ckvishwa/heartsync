// Native tests for the Firebase REST codec and the button debouncer.
// Run: pio test -e native
#include <unity.h>

#include <string>
#include <vector>

#include "cloud/FirestoreCodec.h"
#include "input/Debouncer.h"

void setUp() {}
void tearDown() {}

// Shape of a real emulator :runQuery response (trimmed).
static const char* kQueryResponse = R"([
  {"document":{"name":"projects/demo-heartsync/databases/(default)/documents/couples/demo-couple/events/e1",
    "fields":{"type":{"stringValue":"heart"},"from":{"stringValue":"bob"},
              "payload":{"mapValue":{}},"createdAt":{"timestampValue":"2026-11-16T10:00:01.123456Z"}},
    "createTime":"2026-11-16T10:00:01.123456Z","updateTime":"2026-11-16T10:00:01.123456Z"},
   "readTime":"2026-11-16T10:00:02Z"},
  {"document":{"name":"projects/demo-heartsync/databases/(default)/documents/couples/demo-couple/events/e2",
    "fields":{"type":{"stringValue":"mood"},"from":{"stringValue":"bob"},
              "payload":{"mapValue":{"fields":{"mood":{"stringValue":"happy"},"level":{"integerValue":"3"}}}},
              "createdAt":{"timestampValue":"2026-11-16T10:00:03Z"}}},
   "readTime":"2026-11-16T10:00:04Z"}
])";

void test_decode_events_query() {
    std::vector<hs::fs::RemoteEvent> events;
    TEST_ASSERT_TRUE(hs::fs::parseEventsQuery(kQueryResponse, "alice", events));
    TEST_ASSERT_EQUAL(2, events.size());
    TEST_ASSERT_TRUE(events[0].event.type == hs::EventType::Heart);
    TEST_ASSERT_EQUAL_STRING("bob", events[0].event.from.c_str());
    TEST_ASSERT_EQUAL_STRING("{}", events[0].event.payloadJson.c_str());
    TEST_ASSERT_EQUAL_STRING("e1", events[0].id.c_str());
    TEST_ASSERT_EQUAL_STRING("2026-11-16T10:00:01.123456Z", events[0].createdAt.c_str());
    TEST_ASSERT_TRUE(events[1].event.type == hs::EventType::Mood);
    TEST_ASSERT_EQUAL_STRING("{\"mood\":\"happy\",\"level\":3}", events[1].event.payloadJson.c_str());
}

void test_decode_skips_own_and_unknown_events() {
    const char* json = R"([
      {"document":{"name":"x/events/a","fields":{"type":{"stringValue":"heart"},"from":{"stringValue":"alice"},
        "createdAt":{"timestampValue":"2026-11-16T10:00:00Z"}}}},
      {"document":{"name":"x/events/b","fields":{"type":{"stringValue":"explode"},"from":{"stringValue":"bob"},
        "createdAt":{"timestampValue":"2026-11-16T10:00:00Z"}}}},
      {"document":{"name":"x/events/c","fields":{"type":{"stringValue":"heart"},
        "createdAt":{"timestampValue":"2026-11-16T10:00:00Z"}}}},
      {"readTime":"2026-11-16T10:00:00Z"}
    ])";
    std::vector<hs::fs::RemoteEvent> events;
    TEST_ASSERT_TRUE(hs::fs::parseEventsQuery(json, "alice", events));
    TEST_ASSERT_EQUAL(0, events.size());  // own event, unknown type, no sender
}

void test_decode_empty_and_bad_query() {
    std::vector<hs::fs::RemoteEvent> events;
    TEST_ASSERT_TRUE(hs::fs::parseEventsQuery("[{\"readTime\":\"2026-11-16T10:00:00Z\"}]", "a", events));
    TEST_ASSERT_EQUAL(0, events.size());
    TEST_ASSERT_FALSE(hs::fs::parseEventsQuery("{\"error\":{\"code\":403}}", "a", events));
    TEST_ASSERT_FALSE(hs::fs::parseEventsQuery("not json", "a", events));
    TEST_ASSERT_FALSE(hs::fs::parseEventsQuery(nullptr, "a", events));
}

void test_events_query_body() {
    const std::string body = hs::fs::eventsQueryBody("bob", "2026-11-16T10:00:00Z", 5);
    TEST_ASSERT_NOT_EQUAL(std::string::npos, body.find("\"collectionId\":\"events\""));
    TEST_ASSERT_NOT_EQUAL(std::string::npos,
                          body.find("\"fieldPath\":\"from\"},\"op\":\"EQUAL\",\"value\":{\"stringValue\":\"bob\"}"));
    TEST_ASSERT_NOT_EQUAL(std::string::npos, body.find("\"op\":\"GREATER_THAN\""));
    TEST_ASSERT_NOT_EQUAL(std::string::npos, body.find("\"timestampValue\":\"2026-11-16T10:00:00Z\""));
    TEST_ASSERT_NOT_EQUAL(std::string::npos, body.find("\"direction\":\"ASCENDING\""));
    TEST_ASSERT_NOT_EQUAL(std::string::npos, body.find("\"limit\":5"));
}

void test_sign_in_and_refresh() {
    hs::fs::AuthSession s;
    TEST_ASSERT_TRUE(hs::fs::parseSignIn(
        R"({"idToken":"ID","refreshToken":"RT","expiresIn":"3600","localId":"alice"})", s));
    TEST_ASSERT_EQUAL_STRING("ID", s.idToken.c_str());
    TEST_ASSERT_EQUAL_STRING("RT", s.refreshToken.c_str());
    TEST_ASSERT_EQUAL_STRING("alice", s.uid.c_str());
    TEST_ASSERT_EQUAL(3600, s.expiresInS);
    TEST_ASSERT_FALSE(hs::fs::parseSignIn(R"({"error":{"message":"INVALID_CUSTOM_TOKEN"}})", s));

    hs::fs::AuthSession r;
    TEST_ASSERT_TRUE(hs::fs::parseRefresh(
        R"({"id_token":"ID2","refresh_token":"RT2","expires_in":"3600","user_id":"bob"})", r));
    TEST_ASSERT_EQUAL_STRING("ID2", r.idToken.c_str());
    TEST_ASSERT_EQUAL_STRING("bob", r.uid.c_str());
    TEST_ASSERT_FALSE(hs::fs::parseRefresh("{}", r));

    TEST_ASSERT_EQUAL_STRING("{\"token\":\"T\",\"returnSecureToken\":true}",
                             hs::fs::signInBody("T").c_str());
    // Emulator refresh tokens contain JSON characters: they must be form-encoded.
    TEST_ASSERT_EQUAL_STRING("grant_type=refresh_token&refresh_token=%7B%22a%22%3A1%7D",
                             hs::fs::refreshBody("{\"a\":1}").c_str());
}

void test_sign_in_without_local_id_reads_uid_from_token() {
    // Header {"alg":"none","typ":"JWT"}, payload {"sub":"bob","user_id":"bob"} (base64url).
    const std::string idToken =
        "eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJzdWIiOiJib2IiLCJ1c2VyX2lkIjoiYm9iIn0.";
    TEST_ASSERT_EQUAL_STRING("bob", hs::fs::uidFromIdToken(idToken).c_str());
    hs::fs::AuthSession s;
    const std::string json = "{\"kind\":\"identitytoolkit#VerifyCustomTokenResponse\",\"idToken\":\"" +
                             idToken + "\",\"refreshToken\":\"RT\",\"expiresIn\":\"3600\",\"isNewUser\":false}";
    TEST_ASSERT_TRUE(hs::fs::parseSignIn(json.c_str(), s));
    TEST_ASSERT_EQUAL_STRING("bob", s.uid.c_str());
    TEST_ASSERT_TRUE(hs::fs::uidFromIdToken("garbage").empty());
    TEST_ASSERT_TRUE(hs::fs::uidFromIdToken("a.!!!.b").empty());
}

void test_user_and_couple_documents() {
    std::string couple;
    TEST_ASSERT_TRUE(hs::fs::parseUserCoupleId(
        R"({"name":"x/users/alice","fields":{"displayName":{"stringValue":"Alice"},"coupleId":{"stringValue":"demo-couple"}}})",
        couple));
    TEST_ASSERT_EQUAL_STRING("demo-couple", couple.c_str());
    TEST_ASSERT_FALSE(hs::fs::parseUserCoupleId(R"({"fields":{}})", couple));

    const char* coupleDoc =
        R"({"fields":{"members":{"arrayValue":{"values":[{"stringValue":"alice"},{"stringValue":"bob"}]}}}})";
    std::string partner;
    TEST_ASSERT_TRUE(hs::fs::parseCouplePartner(coupleDoc, "alice", partner));
    TEST_ASSERT_EQUAL_STRING("bob", partner.c_str());
    TEST_ASSERT_TRUE(hs::fs::parseCouplePartner(coupleDoc, "bob", partner));
    TEST_ASSERT_EQUAL_STRING("alice", partner.c_str());
    TEST_ASSERT_FALSE(hs::fs::parseCouplePartner(coupleDoc, "mallory", partner));  // not a member
}

void test_heartbeat_body_and_commit_time() {
    const std::string body =
        hs::fs::heartbeatBody("demo-heartsync", "demo-couple", "hs-20500dcdfd18", "alice", "0.1.0", true);
    TEST_ASSERT_NOT_EQUAL(
        std::string::npos,
        body.find("\"name\":\"projects/demo-heartsync/databases/(default)/documents/couples/"
                  "demo-couple/devices/hs-20500dcdfd18\""));
    TEST_ASSERT_NOT_EQUAL(std::string::npos, body.find("\"owner\":{\"stringValue\":\"alice\"}"));
    TEST_ASSERT_NOT_EQUAL(std::string::npos, body.find("\"online\":{\"booleanValue\":true}"));
    TEST_ASSERT_NOT_EQUAL(std::string::npos,
                          body.find("\"fieldPath\":\"lastSeen\",\"setToServerValue\":\"REQUEST_TIME\""));
    // The heartbeat never touches anything outside the device document.
    TEST_ASSERT_EQUAL(std::string::npos, body.find("private"));

    std::string t;
    TEST_ASSERT_TRUE(hs::fs::parseCommitTime(
        R"({"writeResults":[{"updateTime":"2026-11-16T10:00:00Z"}],"commitTime":"2026-11-16T10:00:00.5Z"})", t));
    TEST_ASSERT_EQUAL_STRING("2026-11-16T10:00:00.5Z", t.c_str());
    TEST_ASSERT_FALSE(hs::fs::parseCommitTime("{}", t));
}

void test_debouncer() {
    hs::Debouncer d(30);
    TEST_ASSERT_FALSE(d.update(false, 0));
    TEST_ASSERT_FALSE(d.update(true, 100));   // edge seen, not stable yet
    TEST_ASSERT_FALSE(d.update(false, 105));  // bounce
    TEST_ASSERT_FALSE(d.update(true, 110));
    TEST_ASSERT_FALSE(d.update(true, 130));   // 20 ms stable
    TEST_ASSERT_TRUE(d.update(true, 140));    // 30 ms stable: one press
    TEST_ASSERT_FALSE(d.update(true, 200));   // held: no repeat
    TEST_ASSERT_TRUE(d.pressed());
    TEST_ASSERT_FALSE(d.update(false, 300));
    TEST_ASSERT_FALSE(d.update(false, 340));  // release is not a press
    TEST_ASSERT_FALSE(d.pressed());
    TEST_ASSERT_FALSE(d.update(true, 400));
    TEST_ASSERT_TRUE(d.update(true, 430));    // second press
}

int main(int, char**) {
    UNITY_BEGIN();
    RUN_TEST(test_decode_events_query);
    RUN_TEST(test_decode_skips_own_and_unknown_events);
    RUN_TEST(test_decode_empty_and_bad_query);
    RUN_TEST(test_events_query_body);
    RUN_TEST(test_sign_in_and_refresh);
    RUN_TEST(test_sign_in_without_local_id_reads_uid_from_token);
    RUN_TEST(test_user_and_couple_documents);
    RUN_TEST(test_heartbeat_body_and_commit_time);
    RUN_TEST(test_debouncer);
    return UNITY_END();
}
