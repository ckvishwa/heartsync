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

const int setupProtocolVersion = 1;
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

  static List<WifiNetwork> decodeList(List<int> bytes) {
    final json = jsonDecode(utf8.decode(bytes));
    if (json is! List) throw const FormatException('bad Wi-Fi list');
    return [
      for (final n in json)
        if (n is Map && n['ssid'] is String && n['rssi'] is int && n['open'] is bool)
          WifiNetwork(ssid: n['ssid'] as String, rssi: n['rssi'] as int, open: n['open'] as bool),
    ];
  }
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

/// Splits the custom token into token-characteristic writes: one flags byte
/// (0x01 first, 0x02 last) then up to [maxWrite] - 1 token bytes. A BLE
/// attribute value is at most 512 bytes, and the token is about 1 KB.
List<List<int>> tokenChunks(String token, int maxWrite) {
  final bytes = utf8.encode(token);
  if (bytes.isEmpty) throw ArgumentError('empty token');
  final size = min(maxWrite, 512) - 1;
  if (size < 1) throw ArgumentError('write size too small');
  final chunks = <List<int>>[];
  for (var at = 0; at < bytes.length; at += size) {
    final end = min(at + size, bytes.length);
    final flags = (at == 0 ? 0x01 : 0) | (end == bytes.length ? 0x02 : 0);
    chunks.add([flags, ...bytes.sublist(at, end)]);
  }
  return chunks;
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
