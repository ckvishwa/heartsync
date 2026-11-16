# 0003: Cloud is Firebase

- **Date:** 2026-11-16
- **Status:** Accepted

## Decision

The backend is Firebase: Auth, Firestore, Cloud Storage, Cloud Functions
(TypeScript), and Cloud Messaging. Local development and tests use the emulator
suite with the project id `demo-heartsync`.

## Why

- Two users and two devices: no need to run servers.
- Firestore gives realtime sync to the app and the web, and a REST/stream API the
  ESP32 can use.
- Security rules express "only this couple" directly and are testable in the emulator.
- Auth is per person, which matches "both people use an iPhone and an Android phone".
- FCM covers push notifications on both platforms.

## Alternatives

- **MQTT broker plus custom backend:** better fit for devices, but adds hosting,
  auth, and a separate store for the app.
- **Supabase:** good, but weaker push story and less mature ESP32 client support.
- **Peer to peer:** devices are behind home NAT and on LTE-M; not practical.

## Consequences

- The device talks to Firestore over TLS, which costs flash and RAM; watch the
  1.75 MB app slot size.
- Devices authenticate as their owner with a custom token (see `docs/architecture.md`).
- Rules are written first and tested for every collection (`cloud/CLAUDE.md`).
- Trusted writes (couples, releases) go through Cloud Functions or CI, never clients.
- Vendor lock-in is accepted for a two-device gift.
