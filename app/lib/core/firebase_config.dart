import 'package:firebase_core/firebase_core.dart';

/// Firebase options read from `--dart-define` / `--dart-define-from-file`.
///
/// Emulator (default): `flutter run --dart-define-from-file=config/emulator.json`
/// (copy `config/emulator.example.json`; the copy is git-ignored).
/// Real project: a git-ignored file with the values from `flutterfire configure`,
/// plus `"USE_EMULATOR": "false"`.
///
/// Nothing here is hardcoded: missing values fail at startup with a message.
class FirebaseConfig {
  const FirebaseConfig({
    required this.apiKey,
    required this.appId,
    required this.messagingSenderId,
    required this.projectId,
  });

  factory FirebaseConfig.fromEnvironment() => const FirebaseConfig(
    apiKey: String.fromEnvironment('FIREBASE_API_KEY'),
    appId: String.fromEnvironment('FIREBASE_APP_ID'),
    messagingSenderId: String.fromEnvironment('FIREBASE_MESSAGING_SENDER_ID'),
    projectId: String.fromEnvironment('FIREBASE_PROJECT_ID'),
  );

  final String apiKey;
  final String appId;
  final String messagingSenderId;
  final String projectId;

  /// Marks the emulator placeholder key. A key containing it must never reach
  /// a real project.
  static const placeholderMarker = 'EmulatorOnly';

  /// Shape the Android SDK checks (Firebase Installations): "AIza" + 35 chars.
  static final _apiKeyShape = RegExp(r'^AIza[0-9A-Za-z_-]{35}$');
  static final _appIdShape = RegExp(r'^\d+:\d+:(android|ios|web):[0-9a-f]+$');

  /// Throws [StateError] naming every problem. Call before Firebase.initializeApp.
  void validate({required bool emulator}) {
    final problems = <String>[];
    if (!_apiKeyShape.hasMatch(apiKey)) {
      problems.add('FIREBASE_API_KEY must look like "AIza" + 35 characters');
    }
    if (!_appIdShape.hasMatch(appId)) {
      problems.add('FIREBASE_APP_ID must look like "1:<sender>:android:<hex>"');
    }
    if (messagingSenderId.isEmpty) {
      problems.add('FIREBASE_MESSAGING_SENDER_ID is empty');
    }
    if (projectId.isEmpty) {
      problems.add('FIREBASE_PROJECT_ID is empty');
    }
    if (emulator) {
      if (projectId.isNotEmpty && !projectId.startsWith('demo-')) {
        problems.add('emulator mode needs a "demo-" project id, got "$projectId"');
      }
    } else {
      if (apiKey.contains(placeholderMarker)) {
        problems.add('FIREBASE_API_KEY is the emulator placeholder; use the real key');
      }
      if (projectId.startsWith('demo-')) {
        problems.add('"$projectId" is an emulator project; set the real project id');
      }
    }
    if (problems.isNotEmpty) {
      throw StateError(
        'Firebase config invalid (${emulator ? 'emulator' : 'REAL project'}): '
        '${problems.join('; ')}. See app/config/emulator.example.json.',
      );
    }
  }

  FirebaseOptions toOptions() => FirebaseOptions(
    apiKey: apiKey,
    appId: appId,
    messagingSenderId: messagingSenderId,
    projectId: projectId,
    storageBucket: '$projectId.appspot.com',
  );
}
