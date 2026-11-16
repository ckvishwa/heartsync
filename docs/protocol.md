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
Read: members. Create: `registerDevice` (server), or the board itself for its own id;
people cannot create records, so nobody can pre-claim a partner's board. Update: the owner
(person or board), owner unchanged. Delete: server only.

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

### `deviceRegistry/{deviceId}` (server only)

| Field          | Type      | Notes                                   |
|----------------|-----------|-----------------------------------------|
| `owner`        | string    | uid of the person who registered it     |
| `coupleId`     | string    | that person's couple at registration    |
| `registeredAt` | timestamp | server time                             |

Written only by `registerDevice` (Admin SDK). No client rule: people and boards are
denied. It stops one couple from claiming, or revoking, a board another couple owns.

## Device tokens (from Phase 3 provisioning)

A board has its **own uid**, `dev_<deviceId>`, never its owner's (ADR 0009). It
signs in with a custom token minted by `registerDevice` for that uid, with custom
claims:

| Claim      | Value                         |
|------------|-------------------------------|
| `deviceId` | `hs-` + 12 hex digits of the MAC |
| `coupleId` | the owner's couple at mint time |
| `owner`    | uid of the person who set the board up |

The board exchanges it for a refresh token immediately; custom claims carry over
to every ID token refreshed from it. Because the uid is the board's own, a board
token can never use Firebase Auth account APIs on the owner's account.

Any token with a `deviceId` claim is in board mode. A board token is valid only if
`uid == "dev_" + deviceId` and `owner` is present, and the owner is a member of
the couple. It may only:

- read and create `couples/{coupleId}/events` (create needs `from == owner`), and
- read, create and update `couples/{coupleId}/devices/{deviceId}` for its own
  `deviceId`, with `owner == token.owner`,

where `coupleId` must equal the claim. It is denied everything else: all of
`users/**` (profile, `private/**`, cycle data), the couple document, other device
records, `releases`, and all of Storage. Rules tests: "device-scoped tokens" in
`cloud/test/rules.test.mjs`. Bench boards provisioned before Phase 3 still hold
plain owner tokens (no claims) until they are re-provisioned.

## BLE provisioning (Phase 3, ADR 0009)

A board in setup mode advertises as `heartsync-<last 4 hex of its id>` with one
service. UUIDs share the base `6a35xxxx-4898-4679-a24f-021d40cfd52a`
(`firmware/include/config.h`, `app/lib/data/board_setup_protocol.dart`).

| Characteristic | UUID prefix | Access | Value (UTF-8 JSON unless noted) |
|---|---|---|---|
| service   | `6a350000` | | |
| `info`      | `6a350001` | read | `{"deviceId","fw","proto":2}` |
| `wifiScan`  | `6a350002` | write | `0x01`: start a scan. `0x02 <n>`: make page `n` the `wifiList` value (out of range: ignored) |
| `wifiList`  | `6a350003` | read, notify | one page, see below |
| `wifiCreds` | `6a350004` | write | `{"ssid","pass"}`: SSID 1..32 bytes kept exactly (spaces too), pass empty (open) or 8..63 bytes |
| `token`     | `6a350005` | write | token frames, see below |
| `status`    | `6a350006` | read, notify | `{"state","reason"?}` |

**Protocol version.** `proto` is 2 (`HS_SETUP_PROTO`, `setupProtocolVersion`).
Proto 1 had passkey entry, a single list value and first/last token flags. The
app reads `info` right after pairing; if `proto` differs it shows "Update the
board firmware" (board older) or "Update the app" (board newer) and disconnects.
A proto 2 board also refuses proto 1 token writes (`bad_token`).

**Wi-Fi list pages.** `{"page":n,"pages":N,"nets":[{"ssid","rssi","open"}]}`.
- Strongest first, one entry per SSID (the strongest), hidden networks dropped,
  at most 40 networks (`HS_SETUP_WIFI_LIST_MAX`) over all pages.
- Each page is at most 512 bytes (one attribute value). There is always at least
  one page; an empty list is `{"page":0,"pages":1,"nets":[]}`.
- Control characters in SSIDs are escaped as `\u00XX`. SSID bytes that are not
  valid UTF-8 are passed through; the app decodes leniently, so such a name shows
  with replacement characters (use "Other network..." for it).
- The board sees only 2.4 GHz networks; 5 GHz names never appear.

**Notify is only a signal.** A notification carries at most MTU-3 bytes (about
244 here, about 182 on a default iOS link), so a page never travels in one.
After a scan, and after each `0x02 <n>`, the board notifies `wifiList` with one
byte: the page number now readable. The app then reads the value (a long read,
up to 512 bytes). App order: enable notify, write `0x01`, wait for the `0`
signal (15 s), read page 0; for each further page write `0x02 n`, wait for `n`
(5 s), read; then merge in order. The app never asks for a new scan while
paging, so a page read does not race a new list.

**Token frames.** A real Firebase custom token is about 900 to 1,000 bytes, more
than one attribute value. (Emulator tokens are shorter, so emulator tests alone
would hide this.) The app writes, each with response:
- chunk: `0x10, seq, data`, seq 0, 1, 2, ..., 180 data bytes each (182 bytes in
  all fits one plain write at the default iOS MTU of 185; the board accepts up to
  510).
- end: `0x11, len (uint16 LE), crc32 (uint32 LE)`, exactly 7 bytes. CRC-32 is the
  IEEE/zlib one (`crc32("123456789") = 0xCBF43926`).

The board reassembles into a RAM-only buffer (never NVS), at most 1536 bytes
(`HS_SETUP_TOKEN_MAX`). Seq 0 starts over. A gap, a repeat, an unknown frame, an
oversized token, or an end frame whose length or CRC does not match wipes the
buffer and reports `bad_token`. The buffer is also wiped on disconnect and after
sign-in.

**Security.** Every characteristic requires an encrypted and authenticated link:
- LE Secure Connections only (`CONFIG_BT_NIMBLE_SM_SC_ONLY`, plus a 16-byte key
  check).
- Numeric comparison (both sides DisplayYesNo, MITM-protected). The same 6-digit
  code shows on the OLED (`TAP BOOT 123456`) and on the phone. The user compares
  them, taps Pair on the phone, then taps BOOT on the board.
- The BOOT tap is the board's "yes". It counts only while a pairing is waiting
  and only for a press that began after the code appeared; a tap with nothing
  waiting does nothing and is not remembered. The tap proves someone is at the
  board, so nobody nearby can pair without touching it. It only protects if the
  user really compares the codes: a blind tap would accept a stranger's request.
- No BOOT tap within 25 s (`HS_SETUP_CONFIRM_MS`, under the 30 s SMP timeout)
  rejects the pairing.
- Bonds are deleted at every setup start and after each session.
- A failed pairing, or a code shown in a session that ends unpaired, is one try.
  3 tries lock BLE (stored in NVS) until BOOT is held 5 s. Someone nearby can
  burn the 3 tries on purpose (a lock-out nuisance, no access); the BOOT hold
  clears it. Accepted.
- A connection that does not pair within 60 s is dropped.
- Advertising stops after 15 min without a connection.

**Status states:**
- `idle`
- `wifi_connecting`
- `wifi_ok`
- `wifi_failed`, with `reason`: `auth` (wrong password), `no_ap`, `timeout` or `other`
- `signing_in`
- `signed_in`

Other reasons that can appear: `bad_creds`, `bad_token`, `not_ready`,
`token_rejected`, `wrong_board`, `network`, `cloud_disabled`. Secrets never appear
in any value the board sends.

**Order:**
1. The app connects and pairs (codes compared, Pair on the phone, BOOT on the
   board), then reads `info` and checks `proto`.
2. It writes `wifiScan` and reads every page (or lets the user type a hidden SSID).
3. It writes `wifiCreds`. The board tests the network and saves it only if it joins.
4. It waits for `wifi_ok`.
5. It calls `registerDevice({deviceId})` and writes the token frames.
6. The board signs in once (token in RAM only), stores the refresh token, reports
   `signed_in`, and restarts into normal mode after 3 s.

**Modes.** The board enters setup when no Wi-Fi is stored, or after BOOT is held 5 s
while running (that wipes Wi-Fi and tokens). It stays in setup until sign-in
succeeds. GPIO 0 is a strapping pin, so the gesture is never "hold at power-up".

## Rules summary

1. Deny by default.
2. Only members of a couple can read or write that couple's data.
3. A device can only write as its owner (`owner == request.auth.uid`, or
   `token.owner` for a board).
4. No one can write another person's events (`from == request.auth.uid`, or
   `token.owner` for a board).
5. Membership (`coupleId`, `members`) is server-set only.
6. Storage objects are scoped by couple: `couples/{coupleId}/...`.
7. Firmware binaries (`firmware/...`) are readable by signed-in people, written only by CI.
8. Board tokens (`deviceId` claim) reach only their couple's events and their own device record.

## Callable functions

| Name        | Input | Effect                                                             | Phase |
|-------------|-------|--------------------------------------------------------------------|-------|
| `sendHeart` | none  | Writes `{type: heart, from: caller}` to the caller's couple events. A board posts as its `owner` claim; its `coupleId` claim must equal the owner's couple. | 2, 3 |
| `registerDevice` | `{deviceId}` | People only. Records the board (`deviceRegistry`, `couples/{c}/devices/{deviceId}`), refuses a board owned by anyone else, revokes the board's old sessions, returns `{token}`: a custom token for `dev_<deviceId>` with claims `{deviceId, coupleId, owner}`. | 3 |

## Device wire format

On the device, an event is encoded as compact JSON (`firmware/src/events/EventCodec.h`):

```json
{"type":"heart","from":"<uid>","payload":{}}
```

`createdAt` is added by the server and is not part of the device encoding.

## Device sync (firmware, Phases 2 and 3)

See ADRs 0008 and 0009. The board signs in as its own uid `dev_<deviceId>` and
takes `coupleId` and `owner` from its ID token claims. It makes only these calls:

| Call | Path | Purpose |
|------|------|---------|
| Auth `signInWithCustomToken` | - | once, with the token from BLE setup (bench builds: serial). The token itself is reusable for 1 h; the board uses it once and wipes it |
| Auth `securetoken` refresh | - | every boot and before the ID token expires (refresh token in NVS) |
| Firestore `:commit` | `couples/{coupleId}/devices/{deviceId}` | heartbeat: `owner` (the claim), `firmwareVersion`, `online`, `lastSeen` (server time) every 60 s |
| Firestore `:runQuery` | `couples/{coupleId}/events` | `createdAt > cursor`, any sender, every 2 s; the board drops its owner's own events and moves the cursor past them |
| Callable | `sendHeart` | BOOT tap or `heart` serial command; the server posts as the owner |

The firmware never reads `users/**` or the couple document (its token cannot).

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
