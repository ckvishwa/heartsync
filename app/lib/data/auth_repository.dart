import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Accounts are per person, not per phone: the same account may be signed in
/// on several phones at once.
abstract class AuthRepository {
  /// Emits the signed-in user's uid, or null when signed out.
  Stream<String?> uidChanges();

  /// Throws [AuthFailure] with a message that is safe to show.
  Future<void> signIn({required String email, required String password});

  Future<void> signOut();
}

class AuthFailure implements Exception {
  const AuthFailure(this.message);
  final String message;

  @override
  String toString() => message;
}

class FirebaseAuthRepository implements AuthRepository {
  FirebaseAuthRepository(this._auth);
  final FirebaseAuth _auth;

  @override
  Stream<String?> uidChanges() => _auth.authStateChanges().map((user) => user?.uid);

  @override
  Future<void> signIn({required String email, required String password}) async {
    try {
      await _auth.signInWithEmailAndPassword(email: email.trim(), password: password);
    } on FirebaseAuthException catch (e) {
      throw AuthFailure(switch (e.code) {
        'invalid-email' => 'That email address does not look right.',
        'user-not-found' || 'wrong-password' || 'invalid-credential' =>
          'Wrong email or password.',
        'network-request-failed' =>
          'Cannot reach the server. Are the Firebase emulators running?',
        _ => 'Could not sign in (${e.code}).',
      });
    }
  }

  @override
  Future<void> signOut() => _auth.signOut();
}

final authRepositoryProvider = Provider<AuthRepository>(
  (ref) => FirebaseAuthRepository(FirebaseAuth.instance),
);

final currentUidProvider = StreamProvider<String?>(
  (ref) => ref.watch(authRepositoryProvider).uidChanges(),
);
