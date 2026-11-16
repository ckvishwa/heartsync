import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/theme.dart';
import '../../data/auth_repository.dart';
import '../../data/connection_repository.dart';
import '../../data/event_repository.dart';
import '../connection/connection_panel.dart';
import '../pairing/setup_board_screen.dart';

class SendHeartScreen extends ConsumerStatefulWidget {
  const SendHeartScreen({super.key});

  @override
  ConsumerState<SendHeartScreen> createState() => _SendHeartScreenState();
}

class _SendHeartScreenState extends ConsumerState<SendHeartScreen> {
  /// After a setup the board restarts, joins Wi-Fi and sends its first
  /// heartbeat; check again once that has had time to happen.
  static const recheckAfterSetup = Duration(seconds: 15);

  bool _busy = false;
  Timer? _recheck;

  @override
  void dispose() {
    _recheck?.cancel();
    super.dispose();
  }

  Future<void> _openSetup() async {
    await Navigator.of(
      context,
    ).push(MaterialPageRoute<void>(builder: (_) => const SetupBoardScreen()));
    if (!mounted) return;
    ref.invalidate(connectionReportProvider);
    _recheck?.cancel();
    _recheck = Timer(recheckAfterSetup, () {
      if (mounted) ref.invalidate(connectionReportProvider);
    });
  }

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
          const _AccountBadge(),
          const SizedBox(width: 8),
        ],
      ),
      body: ListView(
        children: [
          const ConnectionPanel(),
          const SizedBox(height: 24),
          Center(
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
          const SizedBox(height: 24),
          _BoardSetupSection(onSetup: _openSetup),
        ],
      ),
    );
  }
}

/// "Set up a board" when the person has no board yet; once one is registered,
/// shows it as set up and keeps setup as a smaller "set up again" link.
class _BoardSetupSection extends ConsumerWidget {
  const _BoardSetupSection({required this.onSetup});
  final VoidCallback onSetup;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final boards = ref.watch(connectionReportProvider).value?.myBoards ?? const <DeviceStatus>[];
    if (boards.isEmpty) {
      return Center(
        child: OutlinedButton.icon(
          onPressed: onSetup,
          icon: const Icon(Icons.bluetooth_searching),
          label: const Text('Set up a board'),
        ),
      );
    }
    final board = boards.first;
    final online = board.isOnline(DateTime.now());
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Column(
        children: [
          ListTile(
            leading: Icon(
              Icons.check_circle,
              color: online ? Colors.green : Theme.of(context).colorScheme.outline,
            ),
            title: Text('Your board ${board.deviceId} is set up'),
            subtitle: Text(
              online
                  ? 'Online.'
                  : 'Offline right now. It shows online a minute after it joins Wi-Fi.',
            ),
          ),
          TextButton.icon(
            onPressed: onSetup,
            icon: const Icon(Icons.wifi),
            label: const Text('Change Wi-Fi or set up again'),
          ),
          Text(
            'Hold the BOOT button on the board for 5 seconds first.',
            style: Theme.of(context).textTheme.bodySmall,
          ),
        ],
      ),
    );
  }
}

/// The signed-in account as a circle with its first letter (top right). Each
/// account gets its own colour, so two copies of the app (e.g. a dual app) are
/// easy to tell apart. Tap it to see the full email.
class _AccountBadge extends ConsumerWidget {
  const _AccountBadge();

  static const _colors = [
    Color(0xFF1E88E5),
    Color(0xFF8E24AA),
    Color(0xFF00897B),
    Color(0xFFF4511E),
    Color(0xFF3949AB),
    Color(0xFF6D4C41),
  ];

  /// Stable per account (not String.hashCode, which may vary between runs).
  static Color colorFor(String email) =>
      _colors[email.codeUnits.fold<int>(0, (a, c) => (a * 31 + c) & 0x7fffffff) % _colors.length];

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final email = ref.watch(currentEmailProvider).value;
    if (email == null || email.isEmpty) return const SizedBox.shrink();
    final letter = email.characters.first.toUpperCase();
    return Tooltip(
      message: 'Signed in as $email',
      child: InkWell(
        customBorder: const CircleBorder(),
        onTap: () => ScaffoldMessenger.of(context)
          ..hideCurrentSnackBar()
          ..showSnackBar(SnackBar(content: Text('Signed in as $email'))),
        child: CircleAvatar(
          key: const ValueKey('account-badge'),
          radius: 16,
          backgroundColor: colorFor(email),
          foregroundColor: Colors.white,
          child: Text(letter, style: const TextStyle(fontWeight: FontWeight.bold)),
        ),
      ),
    );
  }
}
