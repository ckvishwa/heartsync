import 'package:cloud_functions/cloud_functions.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/firebase_init.dart';

/// Sends events to the couple's event stream. See docs/protocol.md.
abstract class EventRepository {
  /// Sends a heart to the partner. Returns the new event id.
  /// Throws [EventFailure] with a message that is safe to show.
  Future<String> sendHeart();
}

class EventFailure implements Exception {
  const EventFailure(this.message);
  final String message;

  @override
  String toString() => message;
}

class FirebaseEventRepository implements EventRepository {
  FirebaseEventRepository(this._functions);
  final FirebaseFunctions _functions;

  @override
  Future<String> sendHeart() async {
    try {
      final result = await _functions.httpsCallable('sendHeart').call<Map<Object?, Object?>>();
      return result.data['eventId']! as String;
    } on FirebaseFunctionsException catch (e) {
      throw EventFailure(switch (e.code) {
        'failed-precondition' => 'You are not paired with a partner yet.',
        'unauthenticated' => 'Please sign in again.',
        'unavailable' => 'Cannot reach the server. Are the Firebase emulators running?',
        _ => 'Could not send the heart (${e.code}: ${e.message ?? 'no details'}).',
      });
    }
  }
}

final eventRepositoryProvider = Provider<EventRepository>(
  (ref) => FirebaseEventRepository(FirebaseFunctions.instanceFor(region: functionsRegion)),
);
