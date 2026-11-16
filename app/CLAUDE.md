# app

Flutter app for iOS and Android. One codebase, Riverpod for state.

## Commands (run in `app/`)

- `flutter run --dart-define-from-file=config/emulator.json`: run on a device or emulator.
  First `cp config/emulator.example.json config/emulator.json` (git-ignored). Needs the
  Firebase emulators running (`npm run emulators` then `npm run seed` in `cloud/`).
- `flutter test`: widget tests with fake repositories (no emulator needed).
- `flutter analyze`: must be clean before finishing.

## Structure

- `lib/core/`: theme, routing (`AuthGate`), Firebase init.
- `lib/data/`: repositories (abstract class plus Firebase implementation) and models.
- `lib/features/<name>/`: one folder per feature; screens and their controllers.
- Stubs carry a comment naming the phase that fills them in.

## Conventions

- **No business logic in widgets.** Widgets call repositories or controllers through
  Riverpod providers. Firebase SDK calls appear only in `lib/data/` and `lib/core/`.
- Every repository is an abstract class with a provider, so tests override it
  (`provider.overrideWithValue(fake)`).
- Repositories turn SDK exceptions into failures with messages that are safe to show.
- Accounts are per person, not per phone. Never store state keyed by the device.

## Emulator setup

- `lib/core/firebase_init.dart` uses the emulators by default. Firebase options come from
  `--dart-define-from-file` (`lib/core/firebase_config.dart`); startup fails loudly on a bad
  or missing value. The Android SDK rejects API keys not shaped `AIza` + 35 characters, even
  on the emulator, so the placeholder key keeps that shape.
- The real project refuses the emulator placeholder key and any `demo-` project id.
- Android emulator reaches the host at `10.0.2.2` (handled). iOS simulator uses `localhost`.
- Physical phone: `flutter run --dart-define=EMULATOR_HOST=<your PC's LAN IP>` and start
  the emulators bound to `0.0.0.0` (`host` in `cloud/firebase.json`).
- Demo logins after seeding: `alice@example.com` / `bob@example.com`, password `heartsync`.

## Gotchas

- Cleartext HTTP is allowed in the **debug** manifest only, for the emulators.
- The real project needs `flutterfire configure` and `--dart-define=USE_EMULATOR=false`.
- Cycle data is health data: never log it, never cache it locally. See `features/mood_cycle/`.
- No BLE yet (Phase 3). Do not edit generated files under `ios/` and `android/` build output.
