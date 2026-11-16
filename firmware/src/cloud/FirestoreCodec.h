// Pure encode/decode for the Firebase REST calls the device makes.
// Hardware-free: compiles in native tests. No logging here: these strings can
// carry tokens.
//
// Calls (see docs/adr/0008-device-sync-rest-polling.md):
//   Auth   accounts:signInWithCustomToken, securetoken token refresh
//   Store  GET users/{uid}, GET couples/{id}, :commit (heartbeat), :runQuery (events)
#pragma once

#include <stdint.h>

#include <string>
#include <vector>

#include "events/Event.h"

namespace hs {
namespace fs {

struct AuthSession {
    std::string idToken;
    std::string refreshToken;
    std::string uid;
    uint32_t expiresInS = 0;
};

// uid ("user_id", else "sub") from a Firebase ID token's payload. No signature
// check: the token came straight from the Auth server over our own request.
std::string uidFromIdToken(const std::string& idToken);

// Response of accounts:signInWithCustomToken (camelCase fields). The uid comes
// from localId when present, else from the ID token.
bool parseSignIn(const char* json, AuthSession& out);
// Response of securetoken.googleapis.com/v1/token (snake_case fields).
bool parseRefresh(const char* json, AuthSession& out);

std::string signInBody(const std::string& customToken);
// application/x-www-form-urlencoded body for the refresh call.
std::string refreshBody(const std::string& refreshToken);

// users/{uid} document -> coupleId. False if missing.
bool parseUserCoupleId(const char* json, std::string& coupleId);
// couples/{id} document -> the member that is not `ownerUid`. False if not found.
bool parseCouplePartner(const char* json, const std::string& ownerUid, std::string& partnerUid);

// :commit body for the device heartbeat. Sets owner, firmwareVersion, online,
// and lastSeen to the server time.
std::string heartbeatBody(const std::string& projectId, const std::string& coupleId,
                          const std::string& deviceId, const std::string& ownerUid,
                          const char* firmwareVersion, bool online);
// :commit response -> commitTime (RFC 3339, server clock). False if missing.
bool parseCommitTime(const char* json, std::string& commitTime);

// :runQuery body (run on couples/{id}): events from `fromUid` created after
// `afterTimestamp`, oldest first.
std::string eventsQueryBody(const std::string& fromUid, const std::string& afterTimestamp,
                            uint8_t limit);

struct RemoteEvent {
    Event event;
    std::string id;         // document id
    std::string createdAt;  // RFC 3339, for the next query cursor
};

// :runQuery response -> events. Skips entries that are not documents, events
// with an unknown type, and any event from `ownerUid` (a device never reacts to
// its own owner). Returns false only if the JSON is not a query response.
bool parseEventsQuery(const char* json, const std::string& ownerUid,
                      std::vector<RemoteEvent>& out);

}  // namespace fs
}  // namespace hs
