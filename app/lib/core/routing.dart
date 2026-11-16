import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/auth_repository.dart';
import '../features/auth/login_screen.dart';
import '../features/send_heart/send_heart_screen.dart';

/// Shows the login screen when signed out and the home screen when signed in.
/// A real router replaces this when more screens exist (Phase 3).
class AuthGate extends ConsumerWidget {
  const AuthGate({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final uid = ref.watch(currentUidProvider);
    return uid.when(
      data: (value) => value == null ? const LoginScreen() : const SendHeartScreen(),
      loading: () => const Scaffold(body: Center(child: CircularProgressIndicator())),
      error: (error, _) => Scaffold(body: Center(child: Text('Something went wrong: $error'))),
    );
  }
}
