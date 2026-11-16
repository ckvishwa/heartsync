import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:heartsync/data/board_setup_protocol.dart';
import 'package:heartsync/data/board_setup_repository.dart';
import 'package:heartsync/data/device_repository.dart';
import 'package:heartsync/features/pairing/setup_controller.dart';

import 'fakes/board_fakes.dart';

void main() {
  late FakeBoardSetupRepository boards;
  late FakeDeviceRepository devices;
  late ProviderContainer container;

  SetupController controller() => container.read(setupControllerProvider.notifier);
  SetupState state() => container.read(setupControllerProvider);

  setUp(() {
    boards = FakeBoardSetupRepository();
    devices = FakeDeviceRepository();
    container = ProviderContainer(
      overrides: [
        boardSetupRepositoryProvider.overrideWithValue(boards),
        deviceRepositoryProvider.overrideWithValue(devices),
      ],
    );
    container.listen(setupControllerProvider, (_, _) {}); // keep it alive
  });

  tearDown(() => container.dispose());

  Future<void> toWifiStep() async {
    await controller().startScan();
    expect(state().boards.single.name, 'heartsync-63f4');
    await controller().choose(state().boards.single);
    expect(state().step, SetupStep.pickWifi);
    expect(state().info!.deviceId, 'hs-20500dcd63f4');
    expect(state().networks.map((n) => n.ssid), ['Home', 'DeltaForce ']);
  }

  test('happy path: pair, Wi-Fi, register, key, signed in', () async {
    await toWifiStep();
    await controller().joinWifi('Home', 'correct horse');
    expect(state().step, SetupStep.done);
    expect(boards.link.creds, [('Home', 'correct horse')]);
    expect(devices.registered, ['hs-20500dcd63f4']);
    expect(boards.link.tokens, ['custom-token-for-hs-20500dcd63f4']);
    expect(boards.link.disconnected, isTrue);
  });

  test('wrong Wi-Fi password stays on the Wi-Fi step, then a retry works', () async {
    await toWifiStep();
    boards.link.wifiAnswers = ['auth', null];
    await controller().joinWifi('Home', 'wrong-pass');
    expect(state().step, SetupStep.pickWifi);
    expect(state().wifiError, 'Wrong Wi-Fi password.');
    expect(devices.registered, isEmpty);

    await controller().joinWifi('Home', 'correct horse');
    expect(state().step, SetupStep.done);
  });

  test('invalid input is refused before anything is sent', () async {
    await toWifiStep();
    await controller().joinWifi('Home', 'short');
    expect(state().step, SetupStep.pickWifi);
    expect(state().wifiError, isNotNull);
    expect(boards.link.creds, isEmpty);
  });

  test('a registration failure is shown and nothing is sent to the board', () async {
    await toWifiStep();
    devices.failure = const DeviceFailure('This board is registered to someone else.');
    await controller().joinWifi('Home', 'correct horse');
    expect(state().step, SetupStep.failed);
    expect(state().message, 'This board is registered to someone else.');
    expect(boards.link.tokens, isEmpty);
  });

  test('a refused token is reported', () async {
    await toWifiStep();
    boards.link.signInReason = 'token_rejected';
    await controller().joinWifi('Home', 'correct horse');
    expect(state().step, SetupStep.failed);
    expect(state().message, describeReason('token_rejected'));
  });

  test('losing the board mid-flow fails cleanly', () async {
    await toWifiStep();
    boards.link.dropOnCreds = true;
    await controller().joinWifi('Home', 'correct horse');
    expect(state().step, SetupStep.failed);
    expect(state().message, contains('Lost the board'));
  });

  test('reads every Wi-Fi page', () async {
    await toWifiStep();
    expect(boards.link.pageReads, [0, 1]);
  });

  test('a ~1 KB token goes over in frames the board accepts', () async {
    await toWifiStep();
    devices.token = 'h.${'p' * 1000}';
    await controller().joinWifi('Home', 'correct horse');
    expect(state().step, SetupStep.done);
    expect(boards.link.tokenWrites.every((f) => f.length <= 182), isTrue);
    expect(boards.link.tokenWrites.length, 7);
  });

  test('a board on an older setup protocol is refused clearly', () async {
    boards.link.protocol = 1;
    await controller().startScan();
    await controller().choose(state().boards.single);
    expect(state().step, SetupStep.failed);
    expect(state().message, startsWith('Update the board firmware'));
    expect(boards.link.disconnected, isTrue);
    expect(boards.link.creds, isEmpty);
  });

  test('a board on a newer setup protocol asks for an app update', () async {
    boards.link.protocol = setupProtocolVersion + 1;
    await controller().startScan();
    await controller().choose(state().boards.single);
    expect(state().message, startsWith('Update the app'));
    expect(boards.link.disconnected, isTrue);
  });

  test('pairing failure (codes not confirmed, lockout) is shown', () async {
    boards.connectFailure = const BoardSetupFailure('Could not pair with the board.');
    await controller().startScan();
    await controller().choose(state().boards.single);
    expect(state().step, SetupStep.failed);
    expect(state().message, 'Could not pair with the board.');
  });

  test('state never contains the password or the token', () async {
    final seen = <String>[];
    container.listen(setupControllerProvider, (_, s) => seen.add('$s ${s.wifiError} ${s.message}'));
    await toWifiStep();
    await controller().joinWifi('Home', 'correct horse');
    expect(seen.any((s) => s.contains('correct horse')), isFalse);
    expect(seen.any((s) => s.contains('custom-token')), isFalse);
  });
}
