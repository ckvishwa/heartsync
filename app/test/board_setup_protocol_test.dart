import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:heartsync/data/board_setup_protocol.dart';

void main() {
  test('UUIDs match the firmware (config.h)', () {
    expect(BoardUuids.service, '6a350000-4898-4679-a24f-021d40cfd52a');
    expect(BoardUuids.token, '6a350005-4898-4679-a24f-021d40cfd52a');
  });

  test('board info decodes and rejects bad ids', () {
    final info = BoardInfo.decode(
      utf8.encode('{"deviceId":"hs-20500dcd63f4","fw":"0.1.0","proto":1}'),
    );
    expect(info.deviceId, 'hs-20500dcd63f4');
    expect(info.protocol, 1);
    expect(setupProtocolVersion, 2); // must match HS_SETUP_PROTO in config.h
    expect(
      () => BoardInfo.decode(utf8.encode('{"deviceId":"x","fw":"0","proto":1}')),
      throwsFormatException,
    );
    expect(() => BoardInfo.decode(utf8.encode('nope')), throwsFormatException);
  });

  test('Wi-Fi page keeps SSIDs exactly and skips malformed entries', () {
    final p = WifiNetwork.decodePage(
      utf8.encode(
        '{"page":0,"pages":1,"nets":[{"ssid":"DeltaForce ","rssi":-50,"open":true},{"ssid":1},'
        '{"ssid":"say \\"hi\\"\\\\","rssi":-80,"open":false},{"ssid":"\\u0001x","rssi":-90,"open":false}]}',
      ),
    );
    expect(p.page, 0);
    expect(p.pages, 1);
    expect(p.nets.map((n) => n.ssid), ['DeltaForce ', 'say "hi"\\', '\u0001x']);
    expect(p.nets.first.bars, 4);
    expect(p.nets[1].bars, 1);
    // Bad pages.
    for (final bad in [
      '[]',
      '{"page":0,"nets":[]}',
      '{"page":2,"pages":2,"nets":[]}',
      '{"page":0,"pages":0,"nets":[]}',
      '{"page":0,"pages":1,"nets":{}}',
    ]) {
      expect(() => WifiNetwork.decodePage(utf8.encode(bad)), throwsFormatException, reason: bad);
    }
    // An SSID that is not valid UTF-8 does not hide the page.
    final odd = [
      ...utf8.encode('{"page":0,"pages":1,"nets":[{"ssid":"a'),
      0xFF,
      ...utf8.encode('","rssi":-60,"open":true},{"ssid":"Home","rssi":-61,"open":false}]}'),
    ];
    expect(WifiNetwork.decodePage(odd).nets.last.ssid, 'Home');
  });

  test('collectWifiPages reads every page in order', () async {
    String page(int n, int of, List<String> ssids) => jsonEncode({
      'page': n,
      'pages': of,
      'nets': [for (final s in ssids) {'ssid': s, 'rssi': -50, 'open': false}],
    });
    final pages = [
      page(0, 3, ['a', 'b']),
      page(1, 3, ['c']),
      page(2, 3, ['d', 'e']),
    ];
    final asked = <int>[];
    final nets = await collectWifiPages((n) async {
      asked.add(n);
      return utf8.encode(pages[n]);
    });
    expect(asked, [0, 1, 2]);
    expect(nets.map((n) => n.ssid), ['a', 'b', 'c', 'd', 'e']);

    // Empty list: one page, no networks.
    expect(await collectWifiPages((_) async => utf8.encode(page(0, 1, []))), isEmpty);
    // Wrong page returned, or the count changes midway (a new scan): refused.
    expect(
      collectWifiPages((n) async => utf8.encode(page(0, 2, ['x']))),
      throwsFormatException,
    );
    expect(
      collectWifiPages((n) async => utf8.encode(n == 0 ? page(0, 2, ['x']) : page(1, 3, ['y']))),
      throwsFormatException,
    );
  });

  test('scan commands', () {
    expect(wifiScanStart, [0x01]);
    expect(wifiSelectPage(3), [0x02, 3]);
  });

  test('status decodes with and without a reason', () {
    expect(BoardStatus.decode(utf8.encode('{"state":"wifi_ok"}')).reason, isNull);
    final s = BoardStatus.decode(utf8.encode('{"state":"wifi_failed","reason":"auth"}'));
    expect(s.state, 'wifi_failed');
    expect(describeReason(s.reason), 'Wrong Wi-Fi password.');
  });

  test('Wi-Fi validation uses byte lengths like the board', () {
    expect(validateWifi('', 'whatever1'), isNotNull);
    expect(validateWifi('a' * 33, ''), isNotNull);
    expect(validateWifi('Home', 'short'), isNotNull);
    expect(validateWifi('Home', 'a' * 64), isNotNull);
    expect(validateWifi('Home', ''), isNull); // open network
    expect(validateWifi('Home ', '12345678'), isNull);
  });

  test('credentials encode the SSID exactly', () {
    final json = jsonDecode(utf8.decode(encodeWifiCreds('DeltaForce ', 'pw123456')));
    expect(json, {'ssid': 'DeltaForce ', 'pass': 'pw123456'});
  });

  test('crc32 matches the standard check value (and the firmware)', () {
    expect(crc32(utf8.encode('123456789')), 0xCBF43926);
    expect(crc32([]), 0);
  });

  // A ~1 KB token, like a real Firebase custom token (emulator tokens are short).
  String bigToken() {
    final b = StringBuffer('eyJhbGciOiJSUzI1NiJ9.');
    while (b.length < 1000) {
      b.writeCharCode(65 + (b.length * 7) % 26);
    }
    return b.toString();
  }

  /// Reassembles frames like the board (firmware TokenAssembler), or null.
  String? reassemble(List<List<int>> frames) {
    final buf = <int>[];
    var next = 0;
    for (final f in frames) {
      if (f.length > 512) return null;
      if (f[0] == 0x10) {
        if (f[1] != next || f.length < 3) return null;
        next++;
        buf.addAll(f.sublist(2));
      } else if (f[0] == 0x11 && f.length == 7) {
        final len = f[1] | (f[2] << 8);
        final crc = f[3] | (f[4] << 8) | (f[5] << 16) | (f[6] << 24);
        if (len != buf.length || crc != crc32(buf)) return null;
        return utf8.decode(buf);
      } else {
        return null;
      }
    }
    return null;
  }

  test('token frames: numbered 180-byte chunks, then length and CRC', () {
    final token = bigToken();
    final frames = tokenFrames(token);
    expect(frames.length, 6 + 1); // 1000 bytes = 6 chunks of <= 180, + end
    // Every write fits one plain write at the default iOS MTU (185 - 3).
    expect(frames.every((f) => f.length <= 182), isTrue);
    expect([for (final f in frames.take(6)) f[1]], [0, 1, 2, 3, 4, 5]);
    expect(frames.take(6).every((f) => f[0] == 0x10), isTrue);
    expect(frames.last.length, 7);
    expect(frames.last[0], 0x11);
    expect(reassemble(frames), token);

    expect(tokenFrames('abc'), [
      [0x10, 0, ...utf8.encode('abc')],
      [0x11, 3, 0, ...[0xC2, 0x41, 0x24, 0x35]], // crc32("abc") = 0x352441C2
    ]);
  });

  test('token frames: the board refuses tampering, gaps and oversize', () {
    final frames = tokenFrames(bigToken());
    // Bad checksum.
    final badCrc = [...frames]..last = [...frames.last]..last[3] ^= 0xFF;
    expect(reassemble(badCrc), isNull);
    // Missing chunk.
    expect(reassemble([...frames]..removeAt(2)), isNull);
    // Duplicate chunk.
    expect(reassemble([...frames]..insert(2, frames[1])), isNull);
    // Oversized and empty tokens are refused before anything is sent.
    expect(() => tokenFrames('z' * (tokenMaxBytes + 1)), throwsArgumentError);
    expect(tokenFrames('z' * tokenMaxBytes).length, 9 + 1);
    expect(() => tokenFrames(''), throwsArgumentError);
  });

  test('signal labels and help text', () {
    expect(const WifiNetwork(ssid: 'a', rssi: -50, open: false).signalLabel, 'Excellent');
    expect(const WifiNetwork(ssid: 'a', rssi: -67, open: false).signalLabel, 'Fair');
    expect(const WifiNetwork(ssid: 'a', rssi: -90, open: false).signalLabel, 'Very weak');
    expect(reasonHelp('auth'), contains('case-sensitive'));
    expect(reasonHelp('no_ap'), contains('2.4 GHz'));
    expect(reasonHelp('nonsense'), isNull);
  });

  test('protocol mismatch says which side to update', () {
    expect(protocolMismatch(setupProtocolVersion), isNull);
    expect(protocolMismatch(1), startsWith('Update the board firmware'));
    expect(protocolMismatch(setupProtocolVersion + 1), startsWith('Update the app'));
  });
}
