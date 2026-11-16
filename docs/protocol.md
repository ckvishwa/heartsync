# Protocol and data model

Firestore is the source of truth. Rules live in `cloud/firestore.rules` and
`cloud/storage.rules`, with tests in `cloud/test/`.

## Collections

### `users/{uid}`

| Field         | Type      | Notes                                              |
|---------------|-----------|----------------------------------------------------|
| `displayName` | string    | profile                                            |
| `avatar`      | map       | avatar spec (Phase 3)                              |
| `fcmToken`    | string    | notification token                                 |
| `coupleId`    | string    | **server-set only** (Cloud Functions or seed script) |

Read: the user and their partner. Write: the user, except `coupleId`.

### `couples/{coupleId}`

| Field       | Type          |
|-------------|---------------|
| `members`   | `[uidA, uidB]` |
| `createdAt` | timestamp     |

Read: members. Write: server only.

### `couples/{coupleId}/devices/{deviceId}`

| Field             | Type      | Notes                              |
|-------------------|-----------|------------------------------------|
| `owner`           | string    | uid; must equal the writer's uid   |
| `firmwareVersion` | string    |                                    |
| `lastSeen`        | timestamp |                                    |
| `battery`         | number    | 0 to 100, or null before Phase 8   |
| `online`          | bool      |                                    |

`deviceId` is `hs-` plus the 12 hex digits of the MAC.
Read: members. Create/update: a member, only as `owner == self`. Delete: server only.

### `couples/{coupleId}/events/{eventId}`

| Field       | Type      | Notes                                          |
|-------------|-----------|------------------------------------------------|
| `type`      | string    | `heart`, `touch`, `art`, `mood`, `voice`       |
| `from`      | string    | uid of the sender; must equal the writer's uid |
| `payload`   | map       | type-specific, see below                       |
| `createdAt` | timestamp | server time                                    |

Events are immutable (no update or delete from clients).
**Devices listen to events from the other member only**: query
`where from != <owner uid> order by createdAt`, starting after the last seen event.

Payloads:

| Type    | Payload                                    | Phase |
|---------|--------------------------------------------|-------|
| `heart` | `{}`                                       | 2     |
| `touch` | `{ pattern: string }`                      | 4     |
| `art`   | `{ storagePath: string }` or inline pixels | 3     |
| `mood`  | `{ mood: string }`                         | 3     |
| `voice` | `{ storagePath: string, durationMs: number }` | 7  |

### `users/{uid}/private/cycle` (health data)

| Field            | Type | Notes                                  |
|------------------|------|----------------------------------------|
| `sharingEnabled` | bool | required; the app creates it as `true` |
| ...              |      | cycle data, defined in Phase 3         |

- Sharing is **on by default** (the couple agreed). She has an on/off toggle.
- Write: owner only. `sharingEnabled` must be a bool on every write.
- Read: owner always; partner **only while `sharingEnabled == true`**.
- Never logged, never put in notifications, never copied into other documents.

## Device tokens (from Phase 3 provisioning)

A board signs in with a custom token minted by `registerDevice` (Phase 3) for its
owner's uid, with custom claims:

| Claim      | Value                         |
|------------|-------------------------------|
| `deviceId` | `hs-` + 12 hex digits of the MAC |
| `coupleId` | the owner's couple at mint time |

The board exchanges it for a refresh token immediately; custom claims carry over
to every ID token refreshed from it. A token with a `deviceId` claim may only:

- read and create `couples/{coupleId}/events` (create still needs `from == uid`), and
- read, create and update `couples/{coupleId}/devices/{deviceId}` for its own `deviceId`,

where `coupleId` must equal the claim. It is denied everything else: all of
`users/**` (profile, `private/**`, cycle data), the couple document, other device
records, `releases`, and all of Storage. Rules tests: "device-scoped tokens" in
`cloud/test/rules.test.mjs`. Bench boards provisioned before Phase 3 still hold
plain owner tokens (no claims) until they are re-provisioned.

## Rules summary

1. Deny by default.
2. Only members of a couple can read or write that couple's data.
3. A device can only write as its owner (`owner == request.auth.uid`).
4. No one can write another person's events (`from == request.auth.uid`).
5. Membership (`coupleId`, `members`) is server-set only.
6. Storage objects are scoped by couple: `couples/{coupleId}/...`.
7. Firmware binaries (`firmware/...`) are readable by signed-in people, written only by CI.
8. Board tokens (`deviceId` claim) reach only their couple's events and their own device record.

## Callable functions

| Name        | Input | Effect                                                             | Phase |
|-------------|-------|--------------------------------------------------------------------|-------|
| `sendHeart` | none  | Writes `{type: heart, from: caller}` to the caller's couple events | 2     |

## Device wire format

On the device, an event is encoded as compact JSON (`firmware/src/events/EventCodec.h`):

```json
{"type":"heart","from":"<uid>","payload":{}}
```

`createdAt` is added by the server and is not part of the device encoding.

## Device sync (firmware, Phase 2)

See ADR 0008. The board signs in as its owner and makes only these calls:

| Call | Path | Purpose |
|------|------|---------|
| Auth `signInWithCustomToken` | - | first sign-in with the serial-provisioned custom token |
| Auth `securetoken` refresh | - | every boot and before the ID token expires (refresh token in NVS) |
| Firestore GET | `users/{owner}` | read `coupleId` |
| Firestore GET | `couples/{coupleId}` | read `members`, pick the partner |
| Firestore `:commit` | `couples/{coupleId}/devices/{deviceId}` | heartbeat: `owner`, `firmwareVersion`, `online`, `lastSeen` (server time) every 60 s |
| Firestore `:runQuery` | `couples/{coupleId}/events` | `from == partner`, `createdAt > cursor`, every 2 s |
| Callable | `sendHeart` | BOOT button or `heart` serial command |

The firmware never reads or writes `users/{uid}/private/*`.

### Check-in intervals (firmware `config.h`, app `connection_repository.dart`)

| What | Interval | Constant |
|------|----------|----------|
| Event poll | 2 s | `HS_CLOUD_POLL_MS` |
| Device heartbeat (`lastSeen`, `online`, fw) | 60 s | `HS_CLOUD_HEARTBEAT_MS` |
| "Online" in the app | `lastSeen` within 150 s (two missed heartbeats) | `DeviceStatus.onlineWindow` |
| ID token refresh | 5 min before expiry (tokens last 1 h) | `CloudClient::signIn` |
| Retry after a failed call | 2 s, doubling to 30 s | `HS_CLOUD_RETRY_MIN_MS`, `HS_CLOUD_RETRY_MAX_MS` |
| HTTP timeout | 3 s; 10 s for `sendHeart` | `HS_CLOUD_HTTP_TIMEOUT_MS`, `HS_CLOUD_CALL_TIMEOUT_MS` |
| Wi-Fi reconnect | 15 s | `HS_WIFI_RETRY_MS` |

`online` is set to `true` by every heartbeat and never cleared by the board, so
readers must judge freshness from `lastSeen`.

## Firmware release manifest

Written by `firmware/tools/sign_firmware.py`:

```json
{"version":"0.1.0","env":"esp32-s3-devkitc-1","size":123456,
 "sha256":"<hex>","signature":"<base64 ECDSA P-256 over the binary, DER>","alg":"ecdsa-p256-sha256"}
```
