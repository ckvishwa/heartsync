import 'package:cloud_functions/cloud_functions.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/firebase_init.dart';

/// Board registration (docs/protocol.md "Callable functions", ADR 0009).
abstract class DeviceRepository {
  /// Registers the board to the signed-in person and returns the one-time
  /// custom token to hand to the board over BLE. The token is never stored or
  /// logged. Throws [DeviceFailure] with a message that is safe to show.
  Future<String> registerDevice(String deviceId);
}

class DeviceFailure implements Exception {
  const DeviceFailure(this.message);
  final String message;

  @override
  String toString() => message;
}

class FirebaseDeviceRepository implements DeviceRepository {
  FirebaseDeviceRepository(this._functions);
  final FirebaseFunctions _functions;

  @override
  Future<String> registerDevice(String deviceId) async {
    try {
      final result = await _functions.httpsCallable('registerDevice').call<Map<Object?, Object?>>({
        'deviceId': deviceId,
      });
      final token = result.data['token'];
      if (token is! String || token.isEmpty) {
        throw const DeviceFailure('The server returned no board token.');
      }
      return token;
    } on FirebaseFunctionsException catch (e) {
      throw DeviceFailure(switch (e.code) {
        'already-exists' => 'This board is registered to someone else.',
        'failed-precondition' => 'You are not paired with a partner yet.',
        'invalid-argument' => 'The board sent an invalid id.',
        'unauthenticated' => 'Please sign in again.',
        'unavailable' => 'Cannot reach the server. Are the Firebase emulators running?',
        _ => 'Could not register the board (${e.code}).',
      });
    }
  }
}

final deviceRepositoryProvider = Provider<DeviceRepository>(
  (ref) => FirebaseDeviceRepository(FirebaseFunctions.instanceFor(region: functionsRegion)),
);
