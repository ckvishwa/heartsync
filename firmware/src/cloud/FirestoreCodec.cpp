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

bool parseSignIn(const char* json, AuthSession& out) {
    JsonDocument doc;
    if (!parse(json, doc)) {
        return false;
    }
    const char* id = doc["idToken"];
    const char* refresh = doc["refreshToken"];
    const char* uid = doc["localId"];
    if (id == nullptr || refresh == nullptr || uid == nullptr || *id == '\0' || *uid == '\0') {
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

bool parseUserCoupleId(const char* json, std::string& coupleId) {
    JsonDocument doc;
    if (!parse(json, doc)) {
        return false;
    }
    const char* id = stringField(doc["fields"], "coupleId");
    if (id == nullptr || *id == '\0') {
        return false;
    }
    coupleId = id;
    return true;
}

bool parseCouplePartner(const char* json, const std::string& ownerUid, std::string& partnerUid) {
    JsonDocument doc;
    if (!parse(json, doc)) {
        return false;
    }
    bool ownerFound = false;
    std::string partner;
    for (JsonVariantConst v : doc["fields"]["members"]["arrayValue"]["values"].as<JsonArrayConst>()) {
        const char* uid = v["stringValue"];
        if (uid == nullptr) {
            continue;
        }
        if (ownerUid == uid) {
            ownerFound = true;
        } else if (partner.empty()) {
            partner = uid;
        }
    }
    if (!ownerFound || partner.empty()) {
        return false;
    }
    partnerUid = partner;
    return true;
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

std::string eventsQueryBody(const std::string& fromUid, const std::string& afterTimestamp,
                            uint8_t limit) {
    JsonDocument doc;
    JsonObject q = doc["structuredQuery"].to<JsonObject>();
    q["from"].add<JsonObject>()["collectionId"] = "events";
    JsonObject composite = q["where"]["compositeFilter"].to<JsonObject>();
    composite["op"] = "AND";
    JsonArray filters = composite["filters"].to<JsonArray>();
    JsonObject f1 = filters.add<JsonObject>()["fieldFilter"].to<JsonObject>();
    f1["field"]["fieldPath"] = "from";
    f1["op"] = "EQUAL";
    f1["value"]["stringValue"] = fromUid;
    JsonObject f2 = filters.add<JsonObject>()["fieldFilter"].to<JsonObject>();
    f2["field"]["fieldPath"] = "createdAt";
    f2["op"] = "GREATER_THAN";
    f2["value"]["timestampValue"] = afterTimestamp;
    JsonObject order = q["orderBy"].add<JsonObject>();
    order["field"]["fieldPath"] = "createdAt";
    order["direction"] = "ASCENDING";
    q["limit"] = limit;
    std::string out;
    serializeJson(doc, out);
    return out;
}

bool parseEventsQuery(const char* json, const std::string& ownerUid,
                      std::vector<RemoteEvent>& out) {
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
