import 'dart:convert';
import 'dart:math';

/// BLE setup wire format. Mirrors firmware/include/config.h ("BLE Wi-Fi setup")
/// and firmware/src/setup/SetupCodec.h. See docs/protocol.md "BLE provisioning".
///
/// Pure Dart: no BLE calls here, so it is unit tested directly. Nothing in this
/// file logs; values passing through it can hold the Wi-Fi password or the
/// board's custom token.
class BoardUuids {
  static const service = '6a350000-4898-4679-a24f-021d40cfd52a';
  static const info = '6a350001-4898-4679-a24f-021d40cfd52a';
  static const wifiScan = '6a350002-4898-4679-a24f-021d40cfd52a';
  static const wifiList = '6a350003-4898-4679-a24f-021d40cfd52a';
  static const wifiCreds = '6a350004-4898-4679-a24f-021d40cfd52a';
  static const token = '6a350005-4898-4679-a24f-021d40cfd52a';
  static const status = '6a350006-4898-4679-a24f-021d40cfd52a';
}

/// 2: numeric comparison pairing, paged Wi-Fi list, numbered token chunks + CRC32.
const int setupProtocolVersion = 2;
const String boardNamePrefix = 'heartsync-';

class BoardInfo {
  const BoardInfo({required this.deviceId, required this.firmware, required this.protocol});
  final String deviceId;
  final String firmware;
  final int protocol;

  static final _deviceIdRe = RegExp(r'^hs-[0-9a-f]{12}$');

  /// Throws [FormatException] for anything that is not a valid info value.
  factory BoardInfo.decode(List<int> bytes) {
    final json = jsonDecode(utf8.decode(bytes));
    if (json is! Map ||
        json['deviceId'] is! String ||
        json['fw'] is! String ||
        json['proto'] is! int) {
      throw const FormatException('bad board info');
    }
    final id = json['deviceId'] as String;
    if (!_deviceIdRe.hasMatch(id)) throw const FormatException('bad device id');
    return BoardInfo(deviceId: id, firmware: json['fw'] as String, protocol: json['proto'] as int);
  }
}

class WifiNetwork {
  const WifiNetwork({required this.ssid, required this.rssi, required this.open});
  final String ssid;
  final int rssi;
  final bool open;

  /// 0..4 signal bars.
  int get bars => rssi >= -55
      ? 4
      : rssi >= -65
      ? 3
      : rssi >= -75
      ? 2
      : rssi >= -85
      ? 1
      : 0;

  /// One wifiList page: {"page":n,"pages":N,"nets":[{"ssid","rssi","open"}]}.
  /// SSIDs are kept exactly; malformed entries are skipped.
  static ({int page, int pages, List<WifiNetwork> nets}) decodePage(List<int> bytes) {
    // SSIDs are raw bytes and need not be UTF-8: one odd name must not hide the
    // whole page (it shows with replacement characters instead).
    final json = jsonDecode(utf8.decode(bytes, allowMalformed: true));
    if (json is! Map ||
        json['page'] is! int ||
        json['pages'] is! int ||
        json['nets'] is! List ||
        (json['pages'] as int) < 1 ||
        (json['page'] as int) < 0 ||
        (json['page'] as int) >= (json['pages'] as int)) {
      throw const FormatException('bad Wi-Fi page');
    }
    return (
      page: json['page'] as int,
      pages: json['pages'] as int,
      nets: [
        for (final n in json['nets'] as List)
          if (n is Map && n['ssid'] is String && n['rssi'] is int && n['open'] is bool)
            WifiNetwork(ssid: n['ssid'] as String, rssi: n['rssi'] as int, open: n['open'] as bool),
      ],
    );
  }
}

/// wifiScan writes: start a scan, or select the page wifiList returns.
const List<int> wifiScanStart = [0x01];
List<int> wifiSelectPage(int page) => [0x02, page];

/// Most pages the app asks for (the board caps the list at 40 networks).
const int wifiMaxPages = 40;

/// Reads every page of the board's list, in order. [readPage] returns the raw
/// value of page n (page 0 right after a scan). Throws [FormatException] if a
/// page is not the one asked for or the page count changes midway.
Future<List<WifiNetwork>> collectWifiPages(Future<List<int>> Function(int page) readPage) async {
  final first = WifiNetwork.decodePage(await readPage(0));
  if (first.page != 0 || first.pages > wifiMaxPages) {
    throw const FormatException('bad Wi-Fi page');
  }
  final nets = [...first.nets];
  for (var n = 1; n < first.pages; n++) {
    final p = WifiNetwork.decodePage(await readPage(n));
    if (p.page != n || p.pages != first.pages) throw const FormatException('bad Wi-Fi page');
    nets.addAll(p.nets);
  }
  return nets;
}

class BoardStatus {
  const BoardStatus(this.state, [this.reason]);
  final String state;
  final String? reason;

  static BoardStatus decode(List<int> bytes) {
    final json = jsonDecode(utf8.decode(bytes));
    if (json is! Map || json['state'] is! String) throw const FormatException('bad status');
    return BoardStatus(json['state'] as String, json['reason'] as String?);
  }

  @override
  String toString() => reason == null ? state : '$state ($reason)';
}

/// Why a Wi-Fi password is refused before it is sent (the board checks too).
String? validateWifi(String ssid, String password) {
  final ssidBytes = utf8.encode(ssid).length;
  if (ssidBytes == 0) return 'Enter the network name.';
  if (ssidBytes > 32) return 'Network names are at most 32 bytes.';
  final passBytes = utf8.encode(password).length;
  if (passBytes != 0 && (passBytes < 8 || passBytes > 63)) {
    return 'Wi-Fi passwords are 8 to 63 characters.';
  }
  return null;
}

/// wifiCreds value. The SSID is sent exactly as given (spaces included).
List<int> encodeWifiCreds(String ssid, String password) =>
    utf8.encode(jsonEncode({'ssid': ssid, 'pass': password}));

/// Largest token the board accepts (HS_SETUP_TOKEN_MAX).
const int tokenMaxBytes = 1536;

/// Token bytes per chunk write. 2 header bytes + 180 = 182 fits one plain
/// write at the default iOS MTU (185), so no long write is needed.
const int tokenChunkBytes = 180;

/// CRC-32 (IEEE 802.3, the zlib one): crc32("123456789") == 0xCBF43926.
int crc32(List<int> data) {
  var crc = 0xFFFFFFFF;
  for (final b in data) {
    crc ^= b & 0xFF;
    for (var i = 0; i < 8; i++) {
      crc = (crc & 1) != 0 ? (crc >> 1) ^ 0xEDB88320 : crc >> 1;
    }
  }
  return (~crc) & 0xFFFFFFFF;
}

/// Splits the custom token into token-characteristic writes (proto 2). A real
/// custom token is about 1 KB and one BLE attribute value is at most 512 bytes:
///   chunk: 0x10, seq, up to [tokenChunkBytes] token bytes  (seq 0 first)
///   end:   0x11, length (uint16 LE), crc32 (uint32 LE)
/// The board rejects gaps, repeats, a wrong length or a wrong checksum.
List<List<int>> tokenFrames(String token) {
  final bytes = utf8.encode(token);
  if (bytes.isEmpty) throw ArgumentError('empty token');
  if (bytes.length > tokenMaxBytes) throw ArgumentError('token too long for the board');
  final frames = <List<int>>[];
  var seq = 0;
  for (var at = 0; at < bytes.length; at += tokenChunkBytes) {
    frames.add([0x10, seq++, ...bytes.sublist(at, min(at + tokenChunkBytes, bytes.length))]);
  }
  final len = bytes.length;
  final crc = crc32(bytes);
  frames.add([
    0x11,
    len & 0xFF,
    (len >> 8) & 0xFF,
    crc & 0xFF,
    (crc >> 8) & 0xFF,
    (crc >> 16) & 0xFF,
    (crc >> 24) & 0xFF,
  ]);
  return frames;
}

/// Why a board with another setup protocol cannot be set up, or null.
String? protocolMismatch(int boardProtocol) {
  if (boardProtocol == setupProtocolVersion) return null;
  return boardProtocol < setupProtocolVersion
      ? 'Update the board firmware: it uses an older setup protocol '
            '($boardProtocol, this app needs $setupProtocolVersion).'
      : 'Update the app: this board uses a newer setup protocol '
            '($boardProtocol, this app knows $setupProtocolVersion).';
}

/// Message for a board status reason, safe to show.
String describeReason(String? reason) => switch (reason) {
  'auth' => 'Wrong Wi-Fi password.',
  'no_ap' => 'The board cannot see that network. It needs 2.4 GHz Wi-Fi.',
  'timeout' => 'The board could not join the network in time.',
  'token_rejected' => 'The cloud refused the board. Try setting it up again.',
  'wrong_board' => 'That registration was for another board.',
  'network' => 'The board cannot reach the cloud from this network.',
  'cloud_disabled' => 'This board has no cloud address configured.',
  'bad_creds' => 'The board refused that network name or password.',
  'bad_token' || 'not_ready' => 'The board was not ready. Try again.',
  _ => 'The board reported a problem (${reason ?? 'unknown'}).',
};
