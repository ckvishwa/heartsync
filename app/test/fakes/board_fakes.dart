import 'dart:async';
import 'dart:convert';

import 'package:heartsync/data/board_setup_protocol.dart';
import 'package:heartsync/data/board_setup_repository.dart';
import 'package:heartsync/data/device_repository.dart';

/// A board in setup mode that answers like the firmware does.
class FakeBoardLink implements BoardLink {
  final _status = StreamController<BoardStatus>.broadcast();
  final creds = <(String, String)>[];
  final tokens = <String>[];
  bool disconnected = false;
  bool dropOnCreds = false;
  int protocol = setupProtocolVersion;

  /// One entry per Wi-Fi attempt: null = joins, else the wifi_failed reason.
  List<String?> wifiAnswers = [null];
  String? signInReason; // null = signs in

  @override
  Future<BoardInfo> readInfo() async =>
      BoardInfo(deviceId: 'hs-20500dcd63f4', firmware: '0.1.0', protocol: protocol);

  /// wifiList pages as the firmware sends them (two pages, to exercise paging).
  List<String> pages = const [
    '{"page":0,"pages":2,"nets":[{"ssid":"Home","rssi":-50,"open":false}]}',
    '{"page":1,"pages":2,"nets":[{"ssid":"DeltaForce ","rssi":-70,"open":true}]}',
  ];
  final pageReads = <int>[];

  @override
  Future<List<WifiNetwork>> scanWifi() async {
    try {
      return await collectWifiPages((n) async {
        pageReads.add(n);
        return utf8.encode(pages[n]);
      });
    } on FormatException {
      throw const BoardSetupFailure('The board sent something unexpected while scanning Wi-Fi.');
    }
  }

  /// Frames written to the token characteristic, as the real link writes them.
  final tokenWrites = <List<int>>[];

  @override
  Future<void> writeCreds(String ssid, String password) async {
    if (dropOnCreds) throw const BoardSetupFailure('Lost the board while sending Wi-Fi details.');
    creds.add((ssid, password));
    final answer = wifiAnswers.isEmpty ? null : wifiAnswers.removeAt(0);
    scheduleMicrotask(() {
      _status.add(const BoardStatus('wifi_connecting'));
      _status.add(
        answer == null ? const BoardStatus('wifi_ok') : BoardStatus('wifi_failed', answer),
      );
    });
  }

  @override
  Future<void> writeToken(String token) async {
    tokens.add(token);
    tokenWrites.addAll(tokenFrames(token));
    scheduleMicrotask(() {
      _status.add(const BoardStatus('signing_in'));
      _status.add(
        signInReason == null
            ? const BoardStatus('signed_in')
            : BoardStatus('wifi_ok', signInReason),
      );
    });
  }

  @override
  Stream<BoardStatus> status() async* {
    yield const BoardStatus('idle');
    yield* _status.stream;
  }

  @override
  Future<void> disconnect() async => disconnected = true;
}

class FakeBoardSetupRepository implements BoardSetupRepository {
  final link = FakeBoardLink();
  BoardSetupFailure? connectFailure;

  @override
  Stream<List<FoundBoard>> scan({Duration timeout = const Duration(seconds: 10)}) =>
      Stream.value(const [FoundBoard(id: 'AA:BB', name: 'heartsync-63f4', rssi: -60)]);

  @override
  Future<BoardLink> connect(FoundBoard board) async {
    if (connectFailure != null) throw connectFailure!;
    return link;
  }
}

class FakeDeviceRepository implements DeviceRepository {
  final registered = <String>[];
  DeviceFailure? failure;
  String? token; // default: a short emulator-style token

  @override
  Future<String> registerDevice(String deviceId) async {
    if (failure != null) throw failure!;
    registered.add(deviceId);
    return token ?? 'custom-token-for-$deviceId';
  }
}
