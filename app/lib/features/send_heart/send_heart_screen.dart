import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/theme.dart';
import '../../data/auth_repository.dart';
import '../../data/event_repository.dart';

class SendHeartScreen extends ConsumerStatefulWidget {
  const SendHeartScreen({super.key});

  @override
  ConsumerState<SendHeartScreen> createState() => _SendHeartScreenState();
}

class _SendHeartScreenState extends ConsumerState<SendHeartScreen> {
  bool _busy = false;

  Future<void> _sendHeart() async {
    setState(() => _busy = true);
    final messenger = ScaffoldMessenger.of(context);
    String message;
    try {
      await ref.read(eventRepositoryProvider).sendHeart();
      message = 'Heart sent';
    } on EventFailure catch (e) {
      message = e.message;
    }
    if (!mounted) return;
    setState(() => _busy = false);
    messenger
      ..hideCurrentSnackBar()
      ..showSnackBar(SnackBar(content: Text(message)));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('heartsync'),
        actions: [
          IconButton(
            tooltip: 'Sign out',
            icon: const Icon(Icons.logout),
            onPressed: () => ref.read(authRepositoryProvider).signOut(),
          ),
        ],
      ),
      body: Center(
        child: FilledButton.icon(
          onPressed: _busy ? null : _sendHeart,
          style: FilledButton.styleFrom(
            backgroundColor: heartRed,
            foregroundColor: Colors.white,
            padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 20),
          ),
          icon: const Icon(Icons.favorite),
          label: Text(_busy ? 'Sending...' : 'Send heart'),
        ),
      ),
    );
  }
}
