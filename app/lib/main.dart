import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'core/firebase_init.dart';
import 'core/routing.dart';
import 'core/theme.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await initFirebase();
  runApp(const ProviderScope(child: HeartsyncApp()));
}

class HeartsyncApp extends StatelessWidget {
  const HeartsyncApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'heartsync',
      theme: buildTheme(),
      home: const AuthGate(),
    );
  }
}
