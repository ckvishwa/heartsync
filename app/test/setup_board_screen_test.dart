import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:heartsync/data/board_setup_repository.dart';
import 'package:heartsync/data/device_repository.dart';
import 'package:heartsync/features/pairing/setup_board_screen.dart';

import 'fakes/board_fakes.dart';

void main() {
  late FakeBoardSetupRepository boards;
  late FakeDeviceRepository devices;

  Future<void> pump(WidgetTester tester) async {
    boards = FakeBoardSetupRepository();
    devices = FakeDeviceRepository();
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          boardSetupRepositoryProvider.overrideWithValue(boards),
          deviceRepositoryProvider.overrideWithValue(devices),
        ],
        child: const MaterialApp(home: SetupBoardScreen()),
      ),
    );
    await tester.pumpAndSettle();
  }

  testWidgets('sets up a board from scan to done', (tester) async {
    await pump(tester);
    await tester.tap(find.text('heartsync-63f4'));
    await tester.pumpAndSettle();

    expect(find.textContaining('hs-20500dcd63f4'), findsOneWidget);
    expect(find.text('DeltaForce '), findsOneWidget); // SSID shown exactly
    await tester.tap(find.text('Home'));
    await tester.pumpAndSettle();
    await tester.enterText(find.byKey(const ValueKey('password')), 'correct horse');
    await tester.tap(find.text('Connect board'));
    await tester.pumpAndSettle();

    expect(find.textContaining('Board set up'), findsOneWidget);
    expect(boards.link.creds.single, ('Home', 'correct horse'));
    // The password field is gone and nothing on screen shows the secret.
    expect(find.textContaining('correct horse'), findsNothing);
  });

  testWidgets('a wrong password shows the error on the Wi-Fi step', (tester) async {
    await pump(tester);
    boards.link.wifiAnswers = ['auth'];
    await tester.tap(find.text('heartsync-63f4'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Home'));
    await tester.pumpAndSettle();
    await tester.enterText(find.byKey(const ValueKey('password')), 'wrong-pass');
    await tester.tap(find.text('Connect board'));
    await tester.pumpAndSettle();
    expect(find.text('Wrong Wi-Fi password.'), findsOneWidget);
    expect(find.text('Connect board'), findsOneWidget);
  });

  testWidgets('an open network needs no password; manual entry is offered', (tester) async {
    await pump(tester);
    await tester.tap(find.text('heartsync-63f4'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('DeltaForce '));
    await tester.pumpAndSettle();
    expect(find.byKey(const ValueKey('password')), findsNothing);
    await tester.tap(find.text('Other network...'));
    await tester.pumpAndSettle();
    expect(find.byKey(const ValueKey('ssid')), findsOneWidget);
    expect(find.byKey(const ValueKey('password')), findsOneWidget);
  });
}
