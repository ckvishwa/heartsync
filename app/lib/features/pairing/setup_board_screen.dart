import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../data/board_setup_protocol.dart';
import 'setup_controller.dart';

/// "Set up a board": BLE pairing, Wi-Fi, registration (Phase 3, ADR 0009).
class SetupBoardScreen extends ConsumerStatefulWidget {
  const SetupBoardScreen({super.key});

  @override
  ConsumerState<SetupBoardScreen> createState() => _SetupBoardScreenState();
}

class _SetupBoardScreenState extends ConsumerState<SetupBoardScreen> {
  @override
  void initState() {
    super.initState();
    Future.microtask(() => ref.read(setupControllerProvider.notifier).startScan());
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(setupControllerProvider);
    final controller = ref.read(setupControllerProvider.notifier);
    return Scaffold(
      appBar: AppBar(title: const Text('Set up a board')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: switch (state.step) {
          SetupStep.idle || SetupStep.scanning => _BoardList(state: state, controller: controller),
          SetupStep.connecting => const _Progress(
            title: 'Pairing',
            detail: 'When your phone asks, enter the 6-digit PIN shown on the board.',
          ),
          SetupStep.pickWifi => _WifiForm(state: state, controller: controller),
          SetupStep.joiningWifi ||
          SetupStep.registering ||
          SetupStep.sendingKey ||
          SetupStep.finishing => _Steps(step: state.step),
          SetupStep.done => _Done(onDone: () => Navigator.of(context).pop()),
          SetupStep.failed => _Failed(
            message: state.message ?? 'Something went wrong.',
            onRetry: controller.startScan,
          ),
        },
      ),
    );
  }
}

class _BoardList extends StatelessWidget {
  const _BoardList({required this.state, required this.controller});
  final SetupState state;
  final SetupController controller;

  @override
  Widget build(BuildContext context) {
    final scanning = state.step == SetupStep.scanning;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        const Text(
          'Power the board. If it is not showing SET UP, hold its BOOT button for '
          '5 seconds.',
        ),
        const SizedBox(height: 16),
        if (scanning) const LinearProgressIndicator(),
        Expanded(
          child: state.boards.isEmpty
              ? Center(child: Text(scanning ? 'Looking for boards...' : 'No boards found.'))
              : ListView(
                  children: [
                    for (final b in state.boards)
                      ListTile(
                        leading: const Icon(Icons.favorite_border),
                        title: Text(b.name.isEmpty ? 'heartsync board' : b.name),
                        subtitle: Text('Signal ${b.rssi} dBm'),
                        onTap: () => controller.choose(b),
                      ),
                  ],
                ),
        ),
        if (!scanning)
          OutlinedButton.icon(
            onPressed: controller.startScan,
            icon: const Icon(Icons.refresh),
            label: const Text('Scan again'),
          ),
      ],
    );
  }
}

class _WifiForm extends StatefulWidget {
  const _WifiForm({required this.state, required this.controller});
  final SetupState state;
  final SetupController controller;

  @override
  State<_WifiForm> createState() => _WifiFormState();
}

class _WifiFormState extends State<_WifiForm> {
  final _ssid = TextEditingController();
  final _password = TextEditingController();
  bool _manual = false;
  bool _open = false;

  @override
  void dispose() {
    _ssid.dispose();
    _password.clear();
    _password.dispose();
    super.dispose();
  }

  void _pick(WifiNetwork n) => setState(() {
    _manual = false;
    _ssid.text = n.ssid;
    _open = n.open;
    _password.clear();
  });

  void _join() {
    final password = _open ? '' : _password.text;
    _password.clear();
    widget.controller.joinWifi(_ssid.text, password);
  }

  @override
  Widget build(BuildContext context) {
    final s = widget.state;
    final selected = _ssid.text.isNotEmpty || _manual;
    return ListView(
      children: [
        Text(
          'Board ${s.info?.deviceId ?? ''} paired. Choose its Wi-Fi (2.4 GHz).',
          style: Theme.of(context).textTheme.bodyLarge,
        ),
        const SizedBox(height: 8),
        if (s.scanningWifi) const LinearProgressIndicator(),
        for (final n in s.networks)
          ListTile(
            key: ValueKey('net-${n.ssid}'),
            leading: Icon(switch (n.bars) {
              4 => Icons.network_wifi,
              3 => Icons.network_wifi_3_bar,
              2 => Icons.network_wifi_2_bar,
              _ => Icons.network_wifi_1_bar,
            }),
            title: Text(n.ssid),
            trailing: n.open ? null : const Icon(Icons.lock_outline, size: 18),
            selected: !_manual && _ssid.text == n.ssid,
            onTap: () => _pick(n),
          ),
        ListTile(
          leading: const Icon(Icons.edit),
          title: const Text('Other network...'),
          onTap: () => setState(() {
            _manual = true;
            _open = false;
            _ssid.clear();
            _password.clear();
          }),
        ),
        TextButton.icon(
          onPressed: s.scanningWifi ? null : widget.controller.refreshWifi,
          icon: const Icon(Icons.refresh),
          label: const Text('Scan again'),
        ),
        if (selected) ...[
          const Divider(),
          if (_manual)
            TextField(
              key: const ValueKey('ssid'),
              controller: _ssid,
              decoration: const InputDecoration(labelText: 'Network name'),
              onChanged: (_) => setState(() {}),
            )
          else
            Text(_ssid.text, style: Theme.of(context).textTheme.titleMedium),
          if (!_open)
            TextField(
              key: const ValueKey('password'),
              controller: _password,
              obscureText: true,
              enableSuggestions: false,
              autocorrect: false,
              decoration: const InputDecoration(labelText: 'Wi-Fi password'),
            ),
          if (s.wifiError != null)
            Padding(
              padding: const EdgeInsets.only(top: 8),
              child: Text(
                s.wifiError!,
                style: TextStyle(color: Theme.of(context).colorScheme.error),
              ),
            ),
          const SizedBox(height: 16),
          FilledButton(onPressed: _join, child: const Text('Connect board')),
        ] else if (s.wifiError != null)
          Text(s.wifiError!, style: TextStyle(color: Theme.of(context).colorScheme.error)),
      ],
    );
  }
}

class _Steps extends StatelessWidget {
  const _Steps({required this.step});
  final SetupStep step;

  static const _labels = {
    SetupStep.joiningWifi: 'Board joins Wi-Fi',
    SetupStep.registering: 'Registering the board to you',
    SetupStep.sendingKey: 'Sending the board its key',
    SetupStep.finishing: 'Board signs in',
  };

  @override
  Widget build(BuildContext context) {
    final current = _labels.keys.toList().indexOf(step);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        for (final (i, e) in _labels.entries.indexed)
          ListTile(
            leading: i < current
                ? const Icon(Icons.check_circle, color: Colors.green)
                : i == current
                ? const SizedBox(
                    width: 24,
                    height: 24,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.radio_button_unchecked),
            title: Text(e.value),
          ),
      ],
    );
  }
}

class _Progress extends StatelessWidget {
  const _Progress({required this.title, required this.detail});
  final String title;
  final String detail;

  @override
  Widget build(BuildContext context) => Center(
    child: Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        const CircularProgressIndicator(),
        const SizedBox(height: 16),
        Text(title, style: Theme.of(context).textTheme.titleLarge),
        const SizedBox(height: 8),
        Text(detail, textAlign: TextAlign.center),
      ],
    ),
  );
}

class _Done extends StatelessWidget {
  const _Done({required this.onDone});
  final VoidCallback onDone;

  @override
  Widget build(BuildContext context) => Center(
    child: Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        const Icon(Icons.check_circle, color: Colors.green, size: 64),
        const SizedBox(height: 16),
        const Text(
          'Board set up. It restarts and shows as online in a moment.',
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 16),
        FilledButton(onPressed: onDone, child: const Text('Done')),
      ],
    ),
  );
}

class _Failed extends StatelessWidget {
  const _Failed({required this.message, required this.onRetry});
  final String message;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) => Center(
    child: Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(Icons.error_outline, color: Theme.of(context).colorScheme.error, size: 48),
        const SizedBox(height: 16),
        Text(message, textAlign: TextAlign.center),
        const SizedBox(height: 8),
        const Text(
          'If the board shows LOCKED, hold its BOOT button for 5 seconds.',
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 16),
        FilledButton(onPressed: onRetry, child: const Text('Try again')),
      ],
    ),
  );
}
