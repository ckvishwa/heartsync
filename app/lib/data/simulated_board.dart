import 'dart:async';
import 'dart:convert';

import 'board_setup_protocol.dart';
import 'board_setup_repository.dart';

/// A board in setup mode without Bluetooth, for the Android emulator (AVD),
/// which has no BLE radio to reach a real board. Debug builds only, switched on
/// with `--dart-define=SIMULATED_BOARD=true` (see boardSetupRepositoryProvider).
///
/// It answers like the firmware (docs/protocol.md "BLE provisioning", proto 2):
/// - the Wi-Fi list as pages of at most 512 bytes, read one by one through the
///   same [collectWifiPages] the real link uses;
/// - Wi-Fi: protected networks join only with [password]; a typed name it does
///   not see gives `no_ap`;
/// - the token arrives as the same [tokenFrames] and is reassembled and checked
///   (seq, length, CRC-32) like the firmware's TokenAssembler.
/// Registration is not simulated: the app calls the real `registerDevice`.
const bool simulatedBoardEnabled = bool.fromEnvironment('SIMULATED_BOARD');

class SimulatedBoardSetupRepository implements BoardSetupRepository {
  SimulatedBoardSetupRepository({this.delay = const Duration(milliseconds: 600)});

  static const deviceId = 'hs-5e1a00000001';
  static const name = 'heartsync-sim1';

  /// Password of every protected simulated network (test fixture, not a secret).
  static const password = 'heartsync-wifi';

  /// Speed of the simulated board (pairing, scan, Wi-Fi test).
  final Duration delay;

  /// The last link, so tests can check page reads and the received token.
  static SimulatedBoardLink? lastLink;

  @override
  Stream<List<FoundBoard>> scan({Duration timeout = const Duration(seconds: 10)}) async* {
    await Future<void>.delayed(delay);
    yield const [FoundBoard(id: 'SIM:00:01', name: name, rssi: -52)];
    await Future<void>.delayed(delay * 2);
  }

  @override
  Future<BoardLink> connect(FoundBoard board) async {
    await Future<void>.delayed(delay * 2); // pairing (codes compared, BOOT tapped)
    return lastLink = SimulatedBoardLink(delay);
  }
}

/// Networks the simulated board "sees": more than one page holds, with the
/// awkward names real lists have (trailing space, quotes, non-ASCII, long).
const List<WifiNetwork> simulatedNetworks = [
  WifiNetwork(ssid: 'Peace', rssi: -48, open: false),
  WifiNetwork(ssid: 'DeltaForce ', rssi: -52, open: true),
  WifiNetwork(ssid: 'Café ☕ Guest', rssi: -58, open: true),
  WifiNetwork(ssid: 'say "hi"', rssi: -61, open: false),
  WifiNetwork(ssid: 'A-very-long-network-name-32bytes', rssi: -63, open: false),
  WifiNetwork(ssid: 'NETGEAR42', rssi: -66, open: false),
  WifiNetwork(ssid: 'TP-Link_8F2A', rssi: -67, open: false),
  WifiNetwork(ssid: 'xfinitywifi', rssi: -69, open: true),
  WifiNetwork(ssid: 'Linksys00917', rssi: -70, open: false),
  WifiNetwork(ssid: 'HP-Print-3C-LaserJet', rssi: -71, open: false),
  WifiNetwork(ssid: 'Pixel_7781', rssi: -72, open: false),
  WifiNetwork(ssid: 'Verizon_7QX4LP', rssi: -73, open: false),
  WifiNetwork(ssid: 'ATTq9Xc2sP', rssi: -74, open: false),
  WifiNetwork(ssid: 'SpectrumSetup-A1', rssi: -75, open: false),
  WifiNetwork(ssid: 'DIRECT-roku-118', rssi: -76, open: false),
  WifiNetwork(ssid: 'Galaxy S24 5501', rssi: -77, open: false),
  WifiNetwork(ssid: 'Apartment 4B', rssi: -78, open: false),
  WifiNetwork(ssid: 'Library Public', rssi: -79, open: true),
  WifiNetwork(ssid: 'ORBI88', rssi: -80, open: false),
  WifiNetwork(ssid: 'eero', rssi: -81, open: false),
  WifiNetwork(ssid: 'Google Home 4FD2', rssi: -82, open: false),
  WifiNetwork(ssid: 'ASUS_RT-AX58U', rssi: -83, open: false),
  WifiNetwork(ssid: 'FiOS-NT7YD', rssi: -84, open: false),
  WifiNetwork(ssid: 'BELL519', rssi: -85, open: false),
  WifiNetwork(ssid: 'MySpectrumWiFi7a-2G', rssi: -86, open: false),
  WifiNetwork(ssid: 'Starbucks WiFi', rssi: -86, open: true),
  WifiNetwork(ssid: 'dlink-6F3C', rssi: -87, open: false),
  WifiNetwork(ssid: 'CenturyLink2207', rssi: -88, open: false),
  WifiNetwork(ssid: 'Tenda_1A2B3C', rssi: -88, open: false),
  WifiNetwork(ssid: 'Mesh-Node-Upstairs', rssi: -89, open: false),
  WifiNetwork(ssid: 'Garage', rssi: -90, open: false),
  WifiNetwork(ssid: 'Neighbours', rssi: -91, open: false),
  WifiNetwork(ssid: 'Last One', rssi: -92, open: false),
];

/// The firmware's page split (SetupCodec encodeWifiPages): greedy, each page's
/// UTF-8 JSON at most 512 bytes, at least one page.
List<String> encodeSimulatedPages(List<WifiNetwork> nets) {
  String page(int from, int to, int n, int of) => jsonEncode({
    'page': n,
    'pages': of,
    'nets': [
      for (final w in nets.sublist(from, to)) {'ssid': w.ssid, 'rssi': w.rssi, 'open': w.open},
    ],
  });
  final ranges = <(int, int)>[];
  var from = 0;
  while (from < nets.length) {
    var to = from + 1;
    while (to < nets.length && utf8.encode(page(from, to + 1, 99, 99)).length <= 512) {
      to++;
    }
    ranges.add((from, to));
    from = to;
  }
  if (ranges.isEmpty) ranges.add((0, 0));
  return [for (var i = 0; i < ranges.length; i++) page(ranges[i].$1, ranges[i].$2, i, ranges.length)];
}

class SimulatedBoardLink implements BoardLink {
  SimulatedBoardLink(this._delay);
  final Duration _delay;
  final _status = StreamController<BoardStatus>.broadcast();
  var _state = 'idle';
  var _wifiOk = false;

  /// Pages served by the last scan and which ones the app read, in order.
  List<String> pages = const [];
  final pageReads = <int>[];
  int get tokenBytes => _tokenBytes;
  int _tokenBytes = 0;
  bool disconnected = false;

  void _emit(String state, [String? reason]) {
    _state = state;
    _status.add(BoardStatus(state, reason));
  }

  @override
  Future<BoardInfo> readInfo() async =>
      const BoardInfo(deviceId: SimulatedBoardSetupRepository.deviceId, firmware: 'sim', protocol: setupProtocolVersion);

  @override
  Future<List<WifiNetwork>> scanWifi() async {
    await Future<void>.delayed(_delay * 2);
    pages = encodeSimulatedPages(simulatedNetworks);
    pageReads.clear();
    return collectWifiPages((n) async {
      await Future<void>.delayed(const Duration(milliseconds: 80));
      pageReads.add(n);
      if (n < 0 || n >= pages.length) throw TimeoutException('page out of range');
      return utf8.encode(pages[n]);
    });
  }

  @override
  Future<void> writeCreds(String ssid, String password) async {
    if (disconnected) throw const BoardSetupFailure('Lost the board while sending Wi-Fi details.');
    final invalid = validateWifi(ssid, password);
    final known = simulatedNetworks.where((n) => n.ssid == ssid).firstOrNull;
    unawaited(() async {
      if (invalid != null) {
        _emit(_state, 'bad_creds');
        return;
      }
      _emit('wifi_connecting');
      await Future<void>.delayed(_delay * 2);
      if (known == null) {
        _emit('wifi_failed', 'no_ap');
      } else if (known.open ? password.isNotEmpty : password != SimulatedBoardSetupRepository.password) {
        _emit('wifi_failed', 'auth');
      } else {
        _wifiOk = true;
        _emit('wifi_ok');
      }
    }());
  }

  @override
  Future<void> writeToken(String token) async {
    final ok = _wifiOk && _reassemble(tokenFrames(token)) == token;
    _tokenBytes = utf8.encode(token).length;
    unawaited(() async {
      if (!ok) {
        _emit(_state, 'bad_token');
        return;
      }
      _emit('signing_in');
      await Future<void>.delayed(_delay);
      _emit('signed_in');
    }());
  }

  /// Firmware TokenAssembler: seq order, length and CRC-32; null on any error.
  static String? _reassemble(List<List<int>> frames) {
    final buf = <int>[];
    var next = 0;
    for (final f in frames) {
      if (f.length > 512 || f.length < 2) return null;
      if (f[0] == 0x10) {
        if (f[1] != next++ || f.length == 2) return null;
        buf.addAll(f.sublist(2));
      } else if (f[0] == 0x11 && f.length == 7) {
        final len = f[1] | (f[2] << 8);
        final crc = f[3] | (f[4] << 8) | (f[5] << 16) | (f[6] << 24);
        return len == buf.length && crc == crc32(buf) ? utf8.decode(buf) : null;
      } else {
        return null;
      }
    }
    return null;
  }

  @override
  Stream<BoardStatus> status() async* {
    yield BoardStatus(_state);
    yield* _status.stream;
  }

  @override
  Future<void> disconnect() async => disconnected = true;
}
