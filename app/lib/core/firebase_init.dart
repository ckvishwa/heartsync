import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:cloud_functions/cloud_functions.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:flutter/foundation.dart';

/// Phases 1 and 2 run against the local Firebase emulators only
/// (project id `demo-heartsync`, see cloud/CLAUDE.md).
///
/// When the real Firebase project exists: run `flutterfire configure`, pass
/// `DefaultFirebaseOptions.currentPlatform` below, and build with
/// `--dart-define=USE_EMULATOR=false`.
const bool useEmulator = bool.fromEnvironment('USE_EMULATOR', defaultValue: true);

/// Host of the machine running the emulators. Override for a physical phone:
/// `flutter run --dart-define=EMULATOR_HOST=192.168.1.20`
const String _emulatorHostOverride = String.fromEnvironment('EMULATOR_HOST');

/// Must match `setGlobalOptions({ region })` in cloud/functions/src/index.ts.
const String functionsRegion = 'us-central1';

String get emulatorHost {
  if (_emulatorHostOverride.isNotEmpty) return _emulatorHostOverride;
  // The Android emulator reaches the host machine at 10.0.2.2.
  if (!kIsWeb && defaultTargetPlatform == TargetPlatform.android) return '10.0.2.2';
  return 'localhost';
}

Future<void> initFirebase() async {
  await Firebase.initializeApp(
    options: const FirebaseOptions(
      apiKey: 'demo-key',
      appId: '1:1234567890:android:0000000000000000',
      messagingSenderId: '1234567890',
      projectId: 'demo-heartsync',
      storageBucket: 'demo-heartsync.appspot.com',
    ),
  );
  if (useEmulator) {
    final host = emulatorHost;
    await FirebaseAuth.instance.useAuthEmulator(host, 9099);
    FirebaseFirestore.instance.useFirestoreEmulator(host, 8080);
    FirebaseFunctions.instanceFor(region: functionsRegion).useFunctionsEmulator(host, 5001);
  }
}
