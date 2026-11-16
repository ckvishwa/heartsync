# 0008: Device sync over Firebase REST with polling, tokens provisioned over serial

- **Date:** 2026-11-16
- **Status:** Proposed

## Decision

The firmware talks to Firebase with plain REST calls (Auth, Firestore, the
`sendHeart` callable) through `HTTPClient`, and **polls** the partner's events
every 2 s instead of holding a streaming listener. A board's first credential is
a Firebase custom token loaded into NVS over USB serial
(`tools/provision_device.py`); after the first sign-in the board keeps only the
refresh token in NVS and erases the custom token.

## Why

- Firestore's realtime `Listen` is gRPC or WebChannel; neither has a maintained
  ESP32 Arduino client. REST `runQuery` is small, testable, and fits in RAM.
- A 2 s poll on a LAN is fast enough for a heart and costs one small query.
- Query: `from == partner AND createdAt > cursor ORDER BY createdAt`, which uses
  the existing `(from, createdAt)` index. The cursor starts at the heartbeat's
  `commitTime` (server clock), so the board needs no NTP and does not replay old
  hearts on boot.
- Sending goes through the `sendHeart` function, the same path as the app, so the
  server sets `from` and `createdAt` and rules stay unchanged.
- Both boards build from one `secrets.h`, so a per-board token cannot live there.
  Serial provisioning checks the board's device ID before sending the token.
  Custom tokens expire after an hour; the refresh token does not.

## Alternatives

- **Firebase ESP Client libraries:** large, and their streaming uses the RTDB, not Firestore.
- **Realtime Database stream for events:** would split the data model across two stores.
- **Token in `secrets.h` per board:** needs a rebuild per board and per hour.
- **Email and password on the device:** stores a reusable user password on the board.

## Consequences

- Up to about 2 s latency; hearts sent while a board is offline are skipped.
- Emulator only for now (plain HTTP). The real project needs HTTPS with a root
  CA bundle, a phase item under "Create the real Firebase project".
- Each network call blocks `loop()` for up to 3 s on failure; backoff (2 to 30 s)
  keeps a missing emulator from stalling the board. Move the client to its own
  task if this becomes visible.
- The refresh token in NVS is a credential: never logged, erased with `forget`.
