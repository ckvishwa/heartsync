import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../data/connection_repository.dart';

/// Runs the connection check. Invalidate it to check again.
final connectionReportProvider = FutureProvider.autoDispose<ConnectionReport>(
  (ref) => ref.watch(connectionRepositoryProvider).check(),
);

/// Shows whether the phone reaches the cloud and which boards are online.
class ConnectionPanel extends ConsumerWidget {
  const ConnectionPanel({super.key, this.now});

  /// For tests. Defaults to the current time.
  final DateTime? now;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final report = ref.watch(connectionReportProvider);
    return Card(
      margin: const EdgeInsets.all(16),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          mainAxisSize: MainAxisSize.min,
          children: [
            Row(
              children: [
                Text('Connection check', style: Theme.of(context).textTheme.titleMedium),
                const Spacer(),
                IconButton(
                  tooltip: 'Check again',
                  icon: const Icon(Icons.refresh),
                  onPressed: () => ref.invalidate(connectionReportProvider),
                ),
              ],
            ),
            report.when(
              loading: () => const Padding(
                padding: EdgeInsets.all(8),
                child: Center(child: CircularProgressIndicator()),
              ),
              error: (e, _) => _Line(ok: false, label: 'Check failed', detail: '$e'),
              data: (r) => _ReportView(report: r, now: now ?? DateTime.now()),
            ),
          ],
        ),
      ),
    );
  }
}

class _ReportView extends StatelessWidget {
  const _ReportView({required this.report, required this.now});
  final ConnectionReport report;
  final DateTime now;

  @override
  Widget build(BuildContext context) {
    final mine = report.devices.where((d) => d.ownerUid == report.uid);
    final partner = report.devices.where((d) => d.ownerUid != report.uid);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        for (final c in report.checks) _Line(ok: c.ok, label: c.label, detail: c.detail),
        if (report.devices.isNotEmpty) const Divider(),
        for (final d in mine) _deviceLine('Your board', d),
        for (final d in partner) _deviceLine("Partner's board", d),
      ],
    );
  }

  Widget _deviceLine(String who, DeviceStatus d) {
    final online = d.isOnline(now);
    final seen = d.lastSeen == null
        ? 'never seen'
        : 'seen ${_ago(now.difference(d.lastSeen!))} ago';
    return _Line(
      ok: online,
      label: '$who ${d.deviceId}',
      detail: '${online ? 'online' : 'offline'}, $seen, fw ${d.firmwareVersion}',
    );
  }

  static String _ago(Duration d) {
    final s = d.inSeconds.abs();
    if (s < 60) return '${s}s';
    if (s < 3600) return '${s ~/ 60}m';
    return '${s ~/ 3600}h';
  }
}

class _Line extends StatelessWidget {
  const _Line({required this.ok, required this.label, required this.detail});
  final bool ok;
  final String label;
  final String detail;

  @override
  Widget build(BuildContext context) {
    return ListTile(
      dense: true,
      contentPadding: EdgeInsets.zero,
      leading: Icon(
        ok ? Icons.check_circle : Icons.error,
        color: ok ? Colors.green : Colors.red,
        semanticLabel: ok ? 'ok' : 'problem',
      ),
      title: Text(label),
      subtitle: Text(detail),
    );
  }
}
