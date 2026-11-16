import 'package:flutter_test/flutter_test.dart';
import 'package:heartsync/core/firebase_config.dart';

const _emulatorKey = 'AIzaEmulatorOnlyNotARealKey000000000000';
const _realLookingKey = 'AIzaSyA1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q';

FirebaseConfig _config({
  String apiKey = _emulatorKey,
  String appId = '1:000000000000:android:0000000000000000',
  String sender = '000000000000',
  String project = 'demo-heartsync',
}) => FirebaseConfig(apiKey: apiKey, appId: appId, messagingSenderId: sender, projectId: project);

void main() {
  test('the example emulator config is valid in emulator mode', () {
    expect(() => _config().validate(emulator: true), returnsNormally);
  });

  test('empty or badly shaped values fail with every problem named', () {
    final bad = _config(apiKey: 'demo-key', appId: 'nope', sender: '', project: '');
    expect(
      () => bad.validate(emulator: true),
      throwsA(
        isA<StateError>().having(
          (e) => e.message,
          'message',
          allOf(
            contains('FIREBASE_API_KEY'),
            contains('FIREBASE_APP_ID'),
            contains('FIREBASE_MESSAGING_SENDER_ID'),
            contains('FIREBASE_PROJECT_ID'),
          ),
        ),
      ),
    );
  });

  test('emulator mode needs a demo- project', () {
    expect(() => _config(project: 'heartsync-prod').validate(emulator: true), throwsStateError);
  });

  test('the real project refuses the emulator placeholder key', () {
    final c = _config(project: 'heartsync-prod');
    expect(
      () => c.validate(emulator: false),
      throwsA(isA<StateError>().having((e) => e.message, 'message', contains('placeholder'))),
    );
  });

  test('the real project refuses a demo- project id', () {
    final c = _config(apiKey: _realLookingKey);
    expect(() => c.validate(emulator: false), throwsStateError);
  });

  test('a real-looking key and project pass in real mode', () {
    final c = _config(apiKey: _realLookingKey, project: 'heartsync-prod');
    expect(() => c.validate(emulator: false), returnsNormally);
    expect(c.toOptions().storageBucket, 'heartsync-prod.appspot.com');
  });
}
