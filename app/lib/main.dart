import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'core/firebase_init.dart';
import 'core/routing.dart';
import 'core/theme.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  try {
    await initFirebase();
  } on StateError catch (e) {
    // Fail loudly: a misconfigured build must not reach Firebase at all.
    runApp(ConfigErrorApp(message: e.message));
    return;
  }
  runApp(const ProviderScope(child: HeartsyncApp()));
}

class ConfigErrorApp extends StatelessWidget {
  const ConfigErrorApp({super.key, required this.message});
  final String message;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      home: Scaffold(
        body: SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Text('Configuration error:\n\n$message'),
          ),
        ),
      ),
    );
  }
}

class HeartsyncApp extends StatelessWidget {
  const HeartsyncApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(title: 'heartsync', theme: buildTheme(), home: const AuthGate());
  }
}
