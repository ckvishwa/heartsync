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
    expect(find.textContaining('Only 2.4 GHz networks are shown'), findsOneWidget);
    expect(find.text('2 networks'), findsOneWidget);
    await tester.tap(find.text('Home'));
    await tester.pumpAndSettle();
    // The network page: details, password, Connect.
    expect(find.text('Excellent (-50 dBm)'), findsOneWidget);
    expect(find.text('Password protected'), findsOneWidget);
    expect(find.text('2.4 GHz'), findsOneWidget);
    await tester.enterText(find.byKey(const ValueKey('password')), 'correct horse');
    await tester.pump();
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
    await tester.pump();
    await tester.tap(find.text('Connect board'));
    await tester.pumpAndSettle();
    // Back on the same network's page (not the list), the reason and help on top.
    expect(find.byKey(const ValueKey('wifi-error')), findsOneWidget);
    expect(find.text('Wrong Wi-Fi password.'), findsOneWidget);
    expect(find.textContaining('case-sensitive'), findsWidgets);
    final title = tester.widget<Text>(find.byKey(const ValueKey('network-title')));
    expect(title.data, 'Home');
    expect(find.byKey(const ValueKey('password')), findsOneWidget);
    expect(find.textContaining('wrong-pass'), findsNothing); // field cleared

    // A second wrong try shows the count; the right one then works.
    boards.link.wifiAnswers = ['auth', null];
    await tester.enterText(find.byKey(const ValueKey('password')), 'wrong-again');
    await tester.pump();
    await tester.tap(find.text('Connect board'));
    await tester.pumpAndSettle();
    expect(find.text('Failed attempts: 2'), findsOneWidget);
    await tester.enterText(find.byKey(const ValueKey('password')), 'correct horse');
    await tester.pump();
    await tester.tap(find.text('Connect board'));
    await tester.pumpAndSettle();
    expect(find.textContaining('Board set up'), findsOneWidget);
  });

  testWidgets('Connect stays disabled until the password is a valid length', (tester) async {
    await pump(tester);
    await tester.tap(find.text('heartsync-63f4'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Home'));
    await tester.pumpAndSettle();
    FilledButton connect() =>
        tester.widget<FilledButton>(find.widgetWithText(FilledButton, 'Connect board'));
    expect(connect().onPressed, isNull);
    await tester.enterText(find.byKey(const ValueKey('password')), 'short');
    await tester.pump();
    expect(connect().onPressed, isNull);
    expect(find.text('Wi-Fi passwords are 8 to 63 characters.'), findsOneWidget);
    await tester.enterText(find.byKey(const ValueKey('password')), 'long enough');
    await tester.pump();
    expect(connect().onPressed, isNotNull);
    // Show/hide toggle.
    await tester.tap(find.byTooltip('Show password'));
    await tester.pump();
    expect(find.byTooltip('Hide password'), findsOneWidget);
    // Back to the list.
    await tester.tap(find.text('All networks'));
    await tester.pumpAndSettle();
    expect(find.text('Other network...'), findsOneWidget);
  });

  testWidgets('an open network needs no password; manual entry is offered', (tester) async {
    await pump(tester);
    await tester.tap(find.text('heartsync-63f4'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('DeltaForce '));
    await tester.pumpAndSettle();
    expect(find.byKey(const ValueKey('password')), findsNothing);
    expect(find.text('Open (no password)'), findsOneWidget);
    await tester.tap(find.text('All networks'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Other network...'));
    await tester.pumpAndSettle();
    expect(find.byKey(const ValueKey('ssid')), findsOneWidget);
    expect(find.byKey(const ValueKey('password')), findsOneWidget);
  });
}
