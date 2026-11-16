#include "cloud/FirestoreCodec.h"

#include <ArduinoJson.h>
#include <stdlib.h>
#include <string.h>

namespace hs {
namespace fs {

namespace {

bool parse(const char* json, JsonDocument& doc) {
    return json != nullptr && deserializeJson(doc, json) == DeserializationError::Ok;
}

uint32_t toSeconds(JsonVariantConst v) {
    if (v.is<const char*>()) {
        return static_cast<uint32_t>(strtoul(v.as<const char*>(), nullptr, 10));
    }
    return v.as<uint32_t>();
}

std::string formEncode(const std::string& in) {
    static const char* kHex = "0123456789ABCDEF";
    std::string out;
    out.reserve(in.size() * 3);
    for (unsigned char c : in) {
        if ((c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') || (c >= '0' && c <= '9') ||
            c == '-' || c == '_' || c == '.' || c == '~') {
            out += static_cast<char>(c);
        } else {
            out += '%';
            out += kHex[c >> 4];
            out += kHex[c & 0x0F];
        }
    }
    return out;
}

int b64Value(char c) {
    if (c >= 'A' && c <= 'Z') return c - 'A';
    if (c >= 'a' && c <= 'z') return c - 'a' + 26;
    if (c >= '0' && c <= '9') return c - '0' + 52;
    if (c == '-' || c == '+') return 62;
    if (c == '_' || c == '/') return 63;
    return -1;
}

// base64url without padding, as used in JWTs. Stops at the first invalid char.
std::string base64UrlDecode(const std::string& in) {
    std::string out;
    uint32_t acc = 0;
    int bits = 0;
    for (char c : in) {
        const int v = b64Value(c);
        if (v < 0) {
            break;
        }
        acc = (acc << 6) | static_cast<uint32_t>(v);
        bits += 6;
        if (bits >= 8) {
            bits -= 8;
            out += static_cast<char>((acc >> bits) & 0xFF);
        }
    }
    return out;
}

const char* stringField(JsonVariantConst fields, const char* name) {
    return fields[name]["stringValue"].as<const char*>();
}

// Firestore mapValue -> plain JSON object. Scalars only; nested values are skipped.
std::string mapValueToJson(JsonVariantConst mapValue) {
    JsonDocument doc;
    JsonObject obj = doc.to<JsonObject>();
    for (JsonPairConst kv : mapValue["fields"].as<JsonObjectConst>()) {
        JsonVariantConst v = kv.value();
        if (v["stringValue"].is<const char*>()) {
            obj[kv.key()] = v["stringValue"].as<const char*>();
        } else if (v["integerValue"].is<const char*>()) {
            obj[kv.key()] = strtoll(v["integerValue"].as<const char*>(), nullptr, 10);
        } else if (v["booleanValue"].is<bool>()) {
            obj[kv.key()] = v["booleanValue"].as<bool>();
        } else if (v["doubleValue"].is<double>()) {
            obj[kv.key()] = v["doubleValue"].as<double>();
        }
    }
    std::string out;
    serializeJson(doc, out);
    return out;
}

}  // namespace

namespace {

// Decodes the payload (middle part) of a JWT into `payload`. No signature check:
// the token came straight from the Auth server over our own request.
bool jwtPayload(const std::string& jwt, JsonDocument& payload) {
    const size_t a = jwt.find('.');
    const size_t b = a == std::string::npos ? a : jwt.find('.', a + 1);
    if (b == std::string::npos) {
        return false;
    }
    return deserializeJson(payload, base64UrlDecode(jwt.substr(a + 1, b - a - 1))) ==
               DeserializationError::Ok &&
           payload.is<JsonObject>();
}

}  // namespace

std::string uidFromIdToken(const std::string& idToken) {
    JsonDocument payload;
    if (!jwtPayload(idToken, payload)) {
        return {};
    }
    const char* uid = payload["user_id"].is<const char*>() ? payload["user_id"].as<const char*>()
                                                           : payload["sub"].as<const char*>();
    return uid != nullptr ? uid : "";
}

bool claimsFromIdToken(const std::string& idToken, BoardClaims& out) {
    JsonDocument payload;
    if (!jwtPayload(idToken, payload)) {
        return false;
    }
    const char* uid = payload["user_id"].is<const char*>() ? payload["user_id"].as<const char*>()
                                                           : payload["sub"].as<const char*>();
    const char* deviceId = payload["deviceId"];
    const char* coupleId = payload["coupleId"];
    const char* owner = payload["owner"];
    if (uid == nullptr || deviceId == nullptr || coupleId == nullptr || owner == nullptr ||
        *deviceId == '\0' || *coupleId == '\0' || *owner == '\0') {
        return false;
    }
    if (std::string(uid) != std::string("dev_") + deviceId) {
        return false;  // a board token is always for the board's own uid (ADR 0009)
    }
    out.uid = uid;
    out.deviceId = deviceId;
    out.coupleId = coupleId;
    out.owner = owner;
    return true;
}

bool parseSignIn(const char* json, AuthSession& out) {
    JsonDocument doc;
    if (!parse(json, doc)) {
        return false;
    }
    const char* id = doc["idToken"];
    const char* refresh = doc["refreshToken"];
    if (id == nullptr || refresh == nullptr || *id == '\0') {
        return false;
    }
    // signInWithCustomToken returns no localId: the uid is inside the ID token.
    const std::string uid = doc["localId"].is<const char*>() ? doc["localId"].as<const char*>()
                                                             : uidFromIdToken(id);
    if (uid.empty()) {
        return false;
    }
    out.idToken = id;
    out.refreshToken = refresh;
    out.uid = uid;
    out.expiresInS = toSeconds(doc["expiresIn"]);
    return true;
}

bool parseRefresh(const char* json, AuthSession& out) {
    JsonDocument doc;
    if (!parse(json, doc)) {
        return false;
    }
    const char* id = doc["id_token"];
    const char* refresh = doc["refresh_token"];
    const char* uid = doc["user_id"];
    if (id == nullptr || refresh == nullptr || uid == nullptr || *id == '\0' || *uid == '\0') {
        return false;
    }
    out.idToken = id;
    out.refreshToken = refresh;
    out.uid = uid;
    out.expiresInS = toSeconds(doc["expires_in"]);
    return true;
}

std::string signInBody(const std::string& customToken) {
    JsonDocument doc;
    doc["token"] = customToken;
    doc["returnSecureToken"] = true;
    std::string out;
    serializeJson(doc, out);
    return out;
}

std::string refreshBody(const std::string& refreshToken) {
    return "grant_type=refresh_token&refresh_token=" + formEncode(refreshToken);
}

std::string heartbeatBody(const std::string& projectId, const std::string& coupleId,
                          const std::string& deviceId, const std::string& ownerUid,
                          const char* firmwareVersion, bool online) {
    JsonDocument doc;
    JsonObject write = doc["writes"].add<JsonObject>();
    write["update"]["name"] = "projects/" + projectId + "/databases/(default)/documents/couples/" +
                              coupleId + "/devices/" + deviceId;
    JsonObject fields = write["update"]["fields"].to<JsonObject>();
    fields["owner"]["stringValue"] = ownerUid;
    fields["firmwareVersion"]["stringValue"] = firmwareVersion;
    fields["online"]["booleanValue"] = online;
    JsonArray mask = write["updateMask"]["fieldPaths"].to<JsonArray>();
    mask.add("owner");
    mask.add("firmwareVersion");
    mask.add("online");
    JsonObject t = write["updateTransforms"].add<JsonObject>();
    t["fieldPath"] = "lastSeen";
    t["setToServerValue"] = "REQUEST_TIME";
    std::string out;
    serializeJson(doc, out);
    return out;
}

bool parseCommitTime(const char* json, std::string& commitTime) {
    JsonDocument doc;
    if (!parse(json, doc)) {
        return false;
    }
    const char* t = doc["commitTime"];
    if (t == nullptr || *t == '\0') {
        return false;
    }
    commitTime = t;
    return true;
}

std::string eventsQueryBody(const std::string& afterTimestamp, uint8_t limit) {
    JsonDocument doc;
    JsonObject q = doc["structuredQuery"].to<JsonObject>();
    q["from"].add<JsonObject>()["collectionId"] = "events";
    JsonObject f = q["where"]["fieldFilter"].to<JsonObject>();
    f["field"]["fieldPath"] = "createdAt";
    f["op"] = "GREATER_THAN";
    f["value"]["timestampValue"] = afterTimestamp;
    JsonObject order = q["orderBy"].add<JsonObject>();
    order["field"]["fieldPath"] = "createdAt";
    order["direction"] = "ASCENDING";
    q["limit"] = limit;
    std::string out;
    serializeJson(doc, out);
    return out;
}

bool parseEventsQuery(const char* json, const std::string& ownerUid,
                      std::vector<RemoteEvent>& out, std::string* newestCreatedAt) {
    JsonDocument doc;
    if (!parse(json, doc) || !doc.is<JsonArray>()) {
        return false;
    }
    for (JsonVariantConst item : doc.as<JsonArrayConst>()) {
        JsonVariantConst d = item["document"];
        if (d.isNull()) {
            continue;  // e.g. the trailing {"readTime": ...} entry
        }
        JsonVariantConst fields = d["fields"];
        const char* type = stringField(fields, "type");
        const char* from = stringField(fields, "from");
        const char* createdAt = fields["createdAt"]["timestampValue"];
        const char* name = d["name"];
        if (createdAt != nullptr && newestCreatedAt != nullptr) {
            *newestCreatedAt = createdAt;  // results are oldest first
        }
        if (from == nullptr || *from == '\0' || createdAt == nullptr || name == nullptr) {
            continue;
        }
        if (ownerUid == from) {
            continue;
        }
        const EventType t = eventTypeFromName(type);
        if (t == EventType::Unknown) {
            continue;
        }
        RemoteEvent r;
        r.event.type = t;
        r.event.from = from;
        if (fields["payload"]["mapValue"].is<JsonObjectConst>()) {
            r.event.payloadJson = mapValueToJson(fields["payload"]["mapValue"]);
        }
        const char* slash = strrchr(name, '/');
        r.id = slash != nullptr ? slash + 1 : name;
        r.createdAt = createdAt;
        out.push_back(std::move(r));
    }
    return true;
}

}  // namespace fs
}  // namespace hs
