import 'dart:async';
import 'dart:io';

import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/firebase_init.dart';

/// One line of the connection check.
class CheckResult {
  const CheckResult({required this.label, required this.ok, required this.detail});
  final String label;
  final bool ok;
  final String detail;
}

/// A heartsync board as the cloud sees it (couples/{id}/devices/{deviceId}).
class DeviceStatus {
  const DeviceStatus({
    required this.deviceId,
    required this.ownerUid,
    required this.firmwareVersion,
    required this.lastSeen,
  });

  final String deviceId;
  final String ownerUid;
  final String firmwareVersion;
  final DateTime? lastSeen;

  /// Boards heartbeat every 60 s. Two missed heartbeats means offline.
  static const onlineWindow = Duration(seconds: 150);

  bool isOnline(DateTime now) =>
      lastSeen != null && now.difference(lastSeen!).abs() <= onlineWindow;
}

class ConnectionReport {
  const ConnectionReport({required this.checks, required this.devices, required this.uid});
  final List<CheckResult> checks;
  final List<DeviceStatus> devices;
  final String? uid;

  bool get allOk => checks.every((c) => c.ok);

  /// Boards registered to the signed-in person.
  List<DeviceStatus> get myBoards => [
    for (final d in devices)
      if (d.ownerUid == uid) d,
  ];
}

/// Checks that the phone reaches the cloud and that the couple's boards are online.
abstract class ConnectionRepository {
  Future<ConnectionReport> check();
}

class FirebaseConnectionRepository implements ConnectionRepository {
  FirebaseConnectionRepository(this._auth, this._db);
  final FirebaseAuth _auth;
  final FirebaseFirestore _db;

  static const _timeout = Duration(seconds: 5);

  @override
  Future<ConnectionReport> check() async {
    final checks = <CheckResult>[];
    final devices = <DeviceStatus>[];

    if (useEmulator) {
      for (final (label, port) in [
        ('Auth server', 9099),
        ('Database', 8080),
        ('Functions', 5001),
      ]) {
        checks.add(await _port(label, emulatorHost, port));
      }
    }

    final user = _auth.currentUser;
    if (user == null) {
      checks.add(const CheckResult(label: 'Signed in', ok: false, detail: 'Not signed in.'));
      return ConnectionReport(checks: checks, devices: devices, uid: null);
    }
    try {
      await user.getIdToken(true).timeout(_timeout);
      checks.add(CheckResult(label: 'Signed in', ok: true, detail: user.email ?? user.uid));
    } catch (e) {
      checks.add(CheckResult(label: 'Signed in', ok: false, detail: _short(e)));
      return ConnectionReport(checks: checks, devices: devices, uid: user.uid);
    }

    String? coupleId;
    try {
      final me = await _db
          .doc('users/${user.uid}')
          .get(const GetOptions(source: Source.server))
          .timeout(_timeout);
      coupleId = me.data()?['coupleId'] as String?;
      checks.add(
        CheckResult(
          label: 'Paired',
          ok: coupleId != null,
          detail: coupleId == null ? 'No couple on this account.' : 'Couple $coupleId',
        ),
      );
    } catch (e) {
      checks.add(CheckResult(label: 'Paired', ok: false, detail: _short(e)));
    }
    if (coupleId == null) {
      return ConnectionReport(checks: checks, devices: devices, uid: user.uid);
    }

    try {
      final snap = await _db
          .collection('couples/$coupleId/devices')
          .get(const GetOptions(source: Source.server))
          .timeout(_timeout);
      for (final doc in snap.docs) {
        final data = doc.data();
        final seen = data['lastSeen'];
        devices.add(
          DeviceStatus(
            deviceId: doc.id,
            ownerUid: data['owner'] as String? ?? '?',
            firmwareVersion: data['firmwareVersion'] as String? ?? '?',
            lastSeen: seen is Timestamp ? seen.toDate() : null,
          ),
        );
      }
      devices.sort((a, b) => a.deviceId.compareTo(b.deviceId));
      checks.add(
        CheckResult(label: 'Boards listed', ok: true, detail: '${devices.length} registered'),
      );
    } catch (e) {
      checks.add(CheckResult(label: 'Boards listed', ok: false, detail: _short(e)));
    }
    return ConnectionReport(checks: checks, devices: devices, uid: user.uid);
  }

  /// Raw TCP reachability of an emulator port.
  Future<CheckResult> _port(String label, String host, int port) async {
    try {
      final socket = await Socket.connect(host, port, timeout: _timeout);
      socket.destroy();
      return CheckResult(label: label, ok: true, detail: '$host:$port reachable');
    } catch (e) {
      return CheckResult(label: label, ok: false, detail: '$host:$port unreachable');
    }
  }

  static String _short(Object e) {
    final s = e is FirebaseException ? '${e.code}: ${e.message ?? ''}' : e.toString();
    return s.length > 160 ? '${s.substring(0, 160)}...' : s;
  }
}

final connectionRepositoryProvider = Provider<ConnectionRepository>(
  (ref) => FirebaseConnectionRepository(FirebaseAuth.instance, FirebaseFirestore.instance),
);
