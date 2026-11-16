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
    expect(
      () => BoardInfo.decode(utf8.encode('{"deviceId":"x","fw":"0","proto":1}')),
      throwsFormatException,
    );
    expect(() => BoardInfo.decode(utf8.encode('nope')), throwsFormatException);
  });

  test('Wi-Fi list keeps SSIDs exactly and skips malformed entries', () {
    final list = WifiNetwork.decodeList(
      utf8.encode(
        '[{"ssid":"DeltaForce ","rssi":-50,"open":true},{"ssid":1},{"ssid":"Home","rssi":-80,"open":false}]',
      ),
    );
    expect(list.map((n) => n.ssid), ['DeltaForce ', 'Home']);
    expect(list.first.bars, 4);
    expect(list.last.bars, 1);
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

  test('token chunks carry first/last flags and fit one write', () {
    final token = 'x' * 1000;
    final chunks = tokenChunks(token, 244);
    expect(chunks.every((c) => c.length <= 244), isTrue);
    expect(chunks.first.first, 0x01);
    expect(chunks.last.first, 0x02);
    expect(chunks.skip(1).take(chunks.length - 2).every((c) => c.first == 0), isTrue);
    expect(utf8.decode([for (final c in chunks) ...c.skip(1)]), token);

    final single = tokenChunks('abc', 244);
    expect(single, [
      [0x03, ...utf8.encode('abc')],
    ]);
    // Never more than one attribute value per write, whatever the MTU.
    expect(tokenChunks('y' * 2000, 600).every((c) => c.length <= 512), isTrue);
    expect(() => tokenChunks('', 244), throwsArgumentError);
  });
}
