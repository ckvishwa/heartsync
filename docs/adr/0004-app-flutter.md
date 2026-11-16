# 0004: App is Flutter

- **Date:** 2026-11-16
- **Status:** Accepted

## Decision

The companion app is one Flutter codebase for iOS and Android, with Riverpod for
state management and a feature-folder structure. A small Next.js (TypeScript)
dashboard covers the pixel-art editor, device status, and OTA release management.

## Why

- Both people use an iPhone and an Android phone, so both platforms are required
  from day one. One codebase keeps that affordable.
- First-party Firebase plugins (FlutterFire) for Auth, Firestore, Functions, FCM.
- Custom pixel-art UI is easy with Flutter's canvas.
- Riverpod keeps logic out of widgets and makes repositories easy to fake in tests.
- The dashboard is web because release management and a large editor grid are
  desk tasks.

## Alternatives

- **Two native apps:** double the work.
- **React Native:** viable; Flutter chosen for canvas work and plugin maturity for BLE.
- **Web app only:** no reliable BLE provisioning or push on iOS.
- **Bloc or Provider for state:** Riverpod is lighter and compile-safe.

## Consequences

- Accounts are per person, not per phone: a user may be signed in on several
  phones, so notification tokens will need to become a list (Phase 3).
- BLE pairing and Wi-Fi provisioning need platform permissions on both OSes (Phase 3).
- iOS builds need a Mac and an Apple developer account.
- Some logic (pixel editor) exists in both the app and the web dashboard; keep the
  art format defined once in `docs/protocol.md`.
