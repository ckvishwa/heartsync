// Pure encode/decode for the Firebase REST calls the device makes.
// Hardware-free: compiles in native tests. No logging here: these strings can
// carry tokens.
//
// Calls (see docs/adr/0008-device-sync-rest-polling.md):
//   Auth   accounts:signInWithCustomToken, securetoken token refresh
//   Store  :commit (heartbeat), :runQuery (events)
// Board tokens (ADR 0009) cannot read users/ or the couple document: the couple
// and owner come from the ID token's claims.
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

// Claims of a board's ID token (ADR 0009).
struct BoardClaims {
    std::string uid;       // always "dev_" + deviceId
    std::string deviceId;
    std::string coupleId;
    std::string owner;     // the person the board acts for
};

// Reads the board claims from an ID token. False unless deviceId, coupleId and
// owner are all set and the uid is "dev_" + deviceId.
bool claimsFromIdToken(const std::string& idToken, BoardClaims& out);

// Response of accounts:signInWithCustomToken (camelCase fields). The uid comes
// from localId when present, else from the ID token.
bool parseSignIn(const char* json, AuthSession& out);
// Response of securetoken.googleapis.com/v1/token (snake_case fields).
bool parseRefresh(const char* json, AuthSession& out);

std::string signInBody(const std::string& customToken);
// application/x-www-form-urlencoded body for the refresh call.
std::string refreshBody(const std::string& refreshToken);

// :commit body for the device heartbeat. Sets owner, firmwareVersion, online,
// and lastSeen to the server time.
std::string heartbeatBody(const std::string& projectId, const std::string& coupleId,
                          const std::string& deviceId, const std::string& ownerUid,
                          const char* firmwareVersion, bool online);
// :commit response -> commitTime (RFC 3339, server clock). False if missing.
bool parseCommitTime(const char* json, std::string& commitTime);

// :runQuery body (run on couples/{id}): events from anyone created after
// `afterTimestamp`, oldest first. The caller drops its owner's own events.
std::string eventsQueryBody(const std::string& afterTimestamp, uint8_t limit);

struct RemoteEvent {
    Event event;
    std::string id;         // document id
    std::string createdAt;  // RFC 3339, for the next query cursor
};

// :runQuery response -> events. Skips entries that are not documents, events
// with an unknown type, and any event from `ownerUid` (a device never reacts to
// its own owner). Returns false only if the JSON is not a query response.
// `newestCreatedAt`, if given, gets the newest createdAt of every returned
// document, skipped ones included, so the cursor moves past the owner's own
// events instead of fetching them again forever.
bool parseEventsQuery(const char* json, const std::string& ownerUid,
                      std::vector<RemoteEvent>& out, std::string* newestCreatedAt = nullptr);

}  // namespace fs
}  // namespace hs
