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
            detail:
                'Check that the code on your phone matches the board, tap Pair on the '
                'phone, then tap the BOOT button on the board.',
          ),
          SetupStep.pickWifi =>
            state.networkPageOpen
                ? _NetworkPage(
                    key: ValueKey('page-${state.selected?.ssid ?? '(manual)'}'),
                    state: state,
                    controller: controller,
                  )
                : _NetworkList(state: state, controller: controller),
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

IconData _wifiIcon(int bars) => switch (bars) {
  4 => Icons.network_wifi,
  3 => Icons.network_wifi_3_bar,
  2 => Icons.network_wifi_2_bar,
  _ => Icons.network_wifi_1_bar,
};

/// A board-reported problem with what to try next.
class _ErrorCard extends StatelessWidget {
  const _ErrorCard({required this.message, this.help, this.attempts = 0});
  final String message;
  final String? help;
  final int attempts;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Card(
      key: const ValueKey('wifi-error'),
      color: scheme.errorContainer,
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(Icons.error_outline, color: scheme.onErrorContainer),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    message,
                    style: TextStyle(color: scheme.onErrorContainer, fontWeight: FontWeight.bold),
                  ),
                  if (help != null) ...[
                    const SizedBox(height: 4),
                    Text(help!, style: TextStyle(color: scheme.onErrorContainer)),
                  ],
                  if (attempts > 1) ...[
                    const SizedBox(height: 4),
                    Text(
                      'Failed attempts: $attempts',
                      style: TextStyle(color: scheme.onErrorContainer, fontSize: 12),
                    ),
                  ],
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// Step 1 of Wi-Fi: the networks the board can see.
class _NetworkList extends StatelessWidget {
  const _NetworkList({required this.state, required this.controller});
  final SetupState state;
  final SetupController controller;

  @override
  Widget build(BuildContext context) {
    final s = state;
    return ListView(
      children: [
        Text(
          'Board ${s.info?.deviceId ?? ''} paired. Choose its Wi-Fi.',
          style: Theme.of(context).textTheme.bodyLarge,
        ),
        const SizedBox(height: 4),
        Text(
          'Only 2.4 GHz networks are shown. Use Other network... for hidden ones.',
          style: Theme.of(context).textTheme.bodySmall,
        ),
        const SizedBox(height: 8),
        if (s.wifiError != null) _ErrorCard(message: s.wifiError!),
        if (s.scanningWifi) const LinearProgressIndicator(),
        if (!s.scanningWifi && s.networks.isNotEmpty)
          Padding(
            padding: const EdgeInsets.only(top: 4),
            child: Text(
              '${s.networks.length} networks',
              style: Theme.of(context).textTheme.labelMedium,
            ),
          ),
        for (final n in s.networks)
          ListTile(
            key: ValueKey('net-${n.ssid}'),
            leading: Icon(_wifiIcon(n.bars)),
            title: Text(n.ssid),
            subtitle: Text('${n.signalLabel}${n.open ? ', open' : ''}'),
            trailing: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                if (!n.open) const Icon(Icons.lock_outline, size: 18),
                const Icon(Icons.chevron_right),
              ],
            ),
            onTap: () => controller.selectNetwork(n),
          ),
        ListTile(
          leading: const Icon(Icons.edit),
          title: const Text('Other network...'),
          subtitle: const Text('Type the name of a hidden network'),
          trailing: const Icon(Icons.chevron_right),
          onTap: controller.enterManually,
        ),
        TextButton.icon(
          onPressed: s.scanningWifi ? null : controller.refreshWifi,
          icon: const Icon(Icons.refresh),
          label: const Text('Scan again'),
        ),
      ],
    );
  }
}

/// Step 2 of Wi-Fi: one network's details, its password and Connect. A failed
/// attempt comes back to this page with the reason on top (not to the list).
class _NetworkPage extends StatefulWidget {
  const _NetworkPage({super.key, required this.state, required this.controller});
  final SetupState state;
  final SetupController controller;

  @override
  State<_NetworkPage> createState() => _NetworkPageState();
}

class _NetworkPageState extends State<_NetworkPage> {
  late final TextEditingController _ssid = TextEditingController(
    text: widget.state.manualEntry ? widget.state.manualSsid : '',
  );
  final _password = TextEditingController();
  final _passwordFocus = FocusNode();
  bool _show = false;
  late bool _open = widget.state.selected?.open ?? false;

  @override
  void dispose() {
    _ssid.dispose();
    _password.clear();
    _password.dispose();
    _passwordFocus.dispose();
    super.dispose();
  }

  String get _name => widget.state.manualEntry ? _ssid.text : widget.state.selected!.ssid;

  /// Null when Connect can be pressed; otherwise why not (shown under the field).
  String? get _problem {
    if (_name.isEmpty) return 'Enter the network name.';
    // An empty password means "open network" to the board, so a protected
    // network must never be sent one.
    if (!_open && _password.text.isEmpty) return 'Enter the Wi-Fi password.';
    return validateWifi(_name, _open ? '' : _password.text);
  }

  void _connect() {
    final password = _open ? '' : _password.text;
    _password.clear(); // not kept on screen or in state
    widget.controller.joinWifi(_name, password);
  }

  @override
  Widget build(BuildContext context) {
    final s = widget.state;
    final n = s.selected;
    final theme = Theme.of(context);
    final problem = _problem;
    final typing = _password.text.isNotEmpty || (s.manualEntry && _ssid.text.isNotEmpty);
    return ListView(
      children: [
        Align(
          alignment: Alignment.centerLeft,
          child: TextButton.icon(
            onPressed: widget.controller.backToNetworks,
            icon: const Icon(Icons.arrow_back),
            label: const Text('All networks'),
          ),
        ),
        if (s.wifiError != null)
          _ErrorCard(
            message: s.wifiError!,
            help: reasonHelp(s.wifiErrorReason),
            attempts: s.wifiAttempts,
          ),
        const SizedBox(height: 8),
        if (s.manualEntry) ...[
          Text('Other network', style: theme.textTheme.titleLarge),
          const SizedBox(height: 8),
          TextField(
            key: const ValueKey('ssid'),
            controller: _ssid,
            autofocus: s.manualSsid.isEmpty,
            decoration: const InputDecoration(
              labelText: 'Network name',
              helperText: 'Exactly as the router shows it, spaces included.',
            ),
            onChanged: (_) => setState(() {}),
          ),
          SwitchListTile(
            contentPadding: EdgeInsets.zero,
            title: const Text('Open network (no password)'),
            value: _open,
            onChanged: (v) => setState(() => _open = v),
          ),
        ] else ...[
          Row(
            children: [
              Icon(_wifiIcon(n!.bars), size: 32),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  n.ssid,
                  key: const ValueKey('network-title'),
                  style: theme.textTheme.titleLarge,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          _InfoRow(label: 'Signal', value: '${n.signalLabel} (${n.rssi} dBm)'),
          _InfoRow(label: 'Security', value: n.open ? 'Open (no password)' : 'Password protected'),
          const _InfoRow(label: 'Band', value: '2.4 GHz'),
        ],
        const SizedBox(height: 8),
        if (!_open)
          TextField(
            key: const ValueKey('password'),
            controller: _password,
            focusNode: _passwordFocus,
            autofocus: !s.manualEntry,
            obscureText: !_show,
            enableSuggestions: false,
            autocorrect: false,
            decoration: InputDecoration(
              labelText: 'Wi-Fi password',
              helperText: 'Case-sensitive, 8 to 63 characters.',
              errorText: typing && problem != null ? problem : null,
              suffixIcon: IconButton(
                tooltip: _show ? 'Hide password' : 'Show password',
                icon: Icon(_show ? Icons.visibility_off : Icons.visibility),
                onPressed: () => setState(() => _show = !_show),
              ),
            ),
            onChanged: (_) => setState(() {}),
            onSubmitted: (_) {
              if (_problem == null) _connect();
            },
          ),
        const SizedBox(height: 16),
        FilledButton(
          onPressed: problem == null ? _connect : null,
          child: const Text('Connect board'),
        ),
        const SizedBox(height: 8),
        Text(
          'The board tests the network first and saves it only if it can join.',
          style: theme.textTheme.bodySmall,
          textAlign: TextAlign.center,
        ),
      ],
    );
  }
}

class _InfoRow extends StatelessWidget {
  const _InfoRow({required this.label, required this.value});
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 2),
    child: Row(
      children: [
        SizedBox(width: 80, child: Text(label, style: Theme.of(context).textTheme.labelLarge)),
        Expanded(child: Text(value)),
      ],
    ),
  );
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
          'If the board shows LOCKED, hold its BOOT button for 5 seconds, then try '
          'again.',
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 16),
        FilledButton(onPressed: onRetry, child: const Text('Try again')),
      ],
    ),
  );
}
