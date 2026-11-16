# Architecture

```
  Phone A (Flutter)                                     Phone B (Flutter)
        |                                                      |
        |  callable: sendHeart                                 |
        v                                                      v
  +------------------------------ Firebase ------------------------------+
  |  Auth    Firestore (users, couples, devices, events)   Storage  FCM  |
  |          Cloud Functions (pairing, events, notifications, ota)       |
  +-----------------------------------------------------------------------+
        ^                                                      ^
        |  listen: couples/{id}/events where from != me        |
  Device A (ESP32)                                       Device B (ESP32)

  Web dashboard (Next.js): device status, pixel editor, OTA releases
```

## The one rule: the display abstraction

All drawing goes through `IDisplay` (`firmware/src/display/IDisplay.h`). Art,
animation, and event code never see an LED library. `DisplayFactory` picks the
driver at compile time from the `DISPLAY_DRIVER` build flag:

| `DISPLAY_DRIVER` | Driver            | Hardware                        | Status            |
|------------------|-------------------|---------------------------------|-------------------|
| `small_led`      | `SmallLedDisplay` | WS2812B matrix or strip, FastLED | Phase 1           |
| `hub75`          | `Hub75Display`    | 64x32 P2 HUB75 panel            | Stub, Phase 1b    |

See [ADR 0002](adr/0002-display-abstraction.md).

## Firmware

| Module     | Responsibility                                             | Hardware-free? |
|------------|------------------------------------------------------------|----------------|
| `display/` | `IDisplay`, drivers, factory                               | interface only |
| `art/`     | Sprites and drawing them onto an `IDisplay`                | yes            |
| `events/`  | Event types, JSON encoding, in-process `EventBus`          | yes            |
| `net/`     | Wi-Fi, cloud sync (`CloudClient`), OTA health and rollback | no             |
| `input/`   | Touch, IMU (stubs until Phases 4 and 5)                    | no             |
| `power/`   | Battery, charging (stub until Phase 8)                     | no             |

Hardware-free modules build and run in the `native` test environment.

Flow for a received heart: `CloudClient` receives an event document, decodes it
with `decodeEvent`, publishes it on the `EventBus`; a subscriber in `main.cpp`
draws through `Animator` onto `IDisplay`.

## Cloud

- **Firestore** holds all state. The data model and rules are in [protocol.md](protocol.md).
- **Functions** do anything that needs trust: creating couples, writing events on
  behalf of a user (`sendHeart`), sending notifications, publishing OTA releases.
- **Rules** are deny-by-default and tested in the emulator.
- Local development uses the emulator suite with project id `demo-heartsync`,
  which needs no real Firebase project.

## App and web

- **App** (Flutter, Riverpod): feature folders, repositories in `data/`, no business
  logic in widgets. Accounts are per person; one person may sign in on several phones.
- **Web** (Next.js App Router): device list, pixel-art editor, OTA release management.

## OTA

Two app slots plus a data partition. Releases are signed (ECDSA P-256) and the
device verifies before booting into a new slot. New firmware must mark itself
healthy within 60 seconds or the bootloader rolls back.
See [ADR 0005](adr/0005-ota-dual-slot-signed.md).

## Device identity and auth (Phase 2 plan)

A device has a stable ID derived from its MAC (`hs-xxxxxxxxxxxx`). It
authenticates as its **owner** using a Firebase custom token minted during pairing
(`tools/seed_couple.py` for the gift, the app's pairing flow later). Rules therefore
see the owner's uid, which is what "a device can only write as its owner" means.
