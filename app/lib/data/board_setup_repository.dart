import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter_blue_plus/flutter_blue_plus.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'board_setup_protocol.dart';

/// A board found while scanning (advertising the setup service).
class FoundBoard {
  const FoundBoard({required this.id, required this.name, required this.rssi});
  final String id; // platform id (MAC on Android, UUID on iOS)
  final String name; // heartsync-xxxx
  final int rssi;
}

class BoardSetupFailure implements Exception {
  const BoardSetupFailure(this.message);
  final String message;

  @override
  String toString() => message;
}

/// One open, paired link to a board in setup mode.
abstract class BoardLink {
  Future<BoardInfo> readInfo();

  /// Asks the board to scan and returns its list (2.4 GHz networks it can see).
  Future<List<WifiNetwork>> scanWifi();

  Future<void> writeCreds(String ssid, String password);
  Future<void> writeToken(String token);

  /// Status notifications. The current value is emitted first.
  Stream<BoardStatus> status();

  Future<void> disconnect();
}

/// BLE access for the setup flow. See docs/protocol.md "BLE provisioning".
abstract class BoardSetupRepository {
  /// Boards in setup mode nearby. Ends after [timeout].
  Stream<List<FoundBoard>> scan({Duration timeout});

  /// Connects and pairs. Numeric comparison: the phone shows the same 6-digit
  /// code as the board; the user taps Pair on the phone and BOOT on the board.
  Future<BoardLink> connect(FoundBoard board);
}

/// flutter_blue_plus implementation. Logging is off (it would print written
/// values, which include the Wi-Fi password and the token).
class BluetoothBoardSetupRepository implements BoardSetupRepository {
  BluetoothBoardSetupRepository() {
    FlutterBluePlus.setLogLevel(LogLevel.none, color: false);
  }

  @override
  Stream<List<FoundBoard>> scan({Duration timeout = const Duration(seconds: 10)}) async* {
    if (!await FlutterBluePlus.isSupported) {
      throw const BoardSetupFailure('This phone does not support Bluetooth Low Energy.');
    }
    if (FlutterBluePlus.adapterStateNow != BluetoothAdapterState.on) {
      if (defaultTargetPlatform == TargetPlatform.android) {
        try {
          await FlutterBluePlus.turnOn();
        } catch (_) {
          throw const BoardSetupFailure('Turn on Bluetooth to set up a board.');
        }
      }
      await FlutterBluePlus.adapterState
          .firstWhere((s) => s == BluetoothAdapterState.on)
          .timeout(
            const Duration(seconds: 10),
            onTimeout: () => throw const BoardSetupFailure('Turn on Bluetooth to set up a board.'),
          );
    }
    try {
      await FlutterBluePlus.startScan(withServices: [Guid(BoardUuids.service)], timeout: timeout);
    } on FlutterBluePlusException catch (e) {
      throw BoardSetupFailure('Could not scan for boards (${e.description ?? e.code}).');
    }
    // Results until the scan stops (timeout or stopScan).
    final out = StreamController<List<FoundBoard>>();
    final results = FlutterBluePlus.scanResults.listen(
      (results) => out.add([
        for (final r in results)
          FoundBoard(
            id: r.device.remoteId.str,
            name: r.advertisementData.advName.isNotEmpty
                ? r.advertisementData.advName
                : r.device.platformName,
            rssi: r.rssi,
          ),
      ]),
    );
    final stopped = FlutterBluePlus.isScanning.where((s) => !s).first.then((_) => out.close());
    out.onCancel = () async {
      await results.cancel();
      await FlutterBluePlus.stopScan();
    };
    unawaited(stopped);
    yield* out.stream;
    await results.cancel();
  }

  @override
  Future<BoardLink> connect(FoundBoard board) async {
    await FlutterBluePlus.stopScan();
    final device = BluetoothDevice.fromId(board.id);
    final android = defaultTargetPlatform == TargetPlatform.android;
    try {
      if (android) {
        // The board forgets every bond when setup starts: drop the phone's old one.
        await device.removeBond().catchError((_) {});
      }
      // License: personal, non-commercial use (see docs/adr/0009).
      await device.connect(license: License.nonprofit, mtu: 247);
      if (android) {
        // System dialog "Pair? code 123456". The board also waits for a BOOT tap.
        await device.createBond(timeout: 60);
      }
      final services = await device.discoverServices();
      final service = services.firstWhere(
        (s) => s.uuid == Guid(BoardUuids.service),
        orElse: () => throw const BoardSetupFailure('That is not a heartsync board.'),
      );
      BluetoothCharacteristic char(String uuid) => service.characteristics.firstWhere(
        (c) => c.uuid == Guid(uuid),
        orElse: () => throw const BoardSetupFailure('The board firmware is too old.'),
      );
      return _BluetoothBoardLink(
        device,
        info: char(BoardUuids.info),
        wifiScan: char(BoardUuids.wifiScan),
        wifiList: char(BoardUuids.wifiList),
        wifiCreds: char(BoardUuids.wifiCreds),
        token: char(BoardUuids.token),
        statusChar: char(BoardUuids.status),
      );
    } on BoardSetupFailure {
      await device.disconnect().catchError((_) {});
      rethrow;
    } on FlutterBluePlusException catch (e) {
      await device.disconnect().catchError((_) {});
      throw BoardSetupFailure(
        'Could not pair with the board. Check that the codes matched and tap BOOT '
        'on the board within 25 seconds (${e.description ?? e.code}).',
      );
    } on TimeoutException {
      await device.disconnect().catchError((_) {});
      throw const BoardSetupFailure('The board did not answer. Is it still showing SET UP?');
    }
  }
}

class _BluetoothBoardLink implements BoardLink {
  _BluetoothBoardLink(
    this._device, {
    required this.info,
    required this.wifiScan,
    required this.wifiList,
    required this.wifiCreds,
    required this.token,
    required this.statusChar,
  });

  final BluetoothDevice _device;
  final BluetoothCharacteristic info, wifiScan, wifiList, wifiCreds, token, statusChar;

  Future<T> _guard<T>(String what, Future<T> Function() op) async {
    try {
      return await op();
    } on FlutterBluePlusException catch (e) {
      throw BoardSetupFailure('Lost the board while $what (${e.description ?? e.code}).');
    } on FormatException {
      throw BoardSetupFailure('The board sent something unexpected while $what.');
    }
  }

  @override
  Future<BoardInfo> readInfo() =>
      _guard('reading its id', () async => BoardInfo.decode(await info.read()));

  /// The notification is only a "page n ready" signal (1 byte). The page itself
  /// is read with a (long) read: a notification holds just MTU-3 bytes.
  Future<void> _ready(int page, Duration timeout) => wifiList.onValueReceived
      .firstWhere((v) => v.length == 1 && v[0] == page)
      .timeout(timeout);

  @override
  Future<List<WifiNetwork>> scanWifi() => _guard('scanning Wi-Fi', () async {
    await wifiList.setNotifyValue(true);
    return collectWifiPages((page) async {
      // Listen before writing so the signal cannot be missed.
      final ready = _ready(page, Duration(seconds: page == 0 ? 15 : 5));
      ready.ignore(); // if the write throws, this wait is abandoned
      await wifiScan.write(page == 0 ? wifiScanStart : wifiSelectPage(page));
      await ready;
      return wifiList.read();
    });
  });

  @override
  Future<void> writeCreds(String ssid, String password) =>
      _guard('sending Wi-Fi details', () => wifiCreds.write(encodeWifiCreds(ssid, password)));

  @override
  Future<void> writeToken(String value) => _guard('sending the board key', () async {
    for (final frame in tokenFrames(value)) {
      await token.write(frame); // with response: in order, and errors surface
    }
  });

  @override
  Stream<BoardStatus> status() async* {
    await _guard('reading status', () => statusChar.setNotifyValue(true));
    yield BoardStatus.decode(await _guard('reading status', statusChar.read));
    yield* statusChar.onValueReceived.map(BoardStatus.decode);
  }

  @override
  Future<void> disconnect() => _device.disconnect().catchError((_) {});
}

final boardSetupRepositoryProvider = Provider<BoardSetupRepository>(
  (ref) => BluetoothBoardSetupRepository(),
);
