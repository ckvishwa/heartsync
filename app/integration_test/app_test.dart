// End-to-end regression suite for the Android emulator (AVD).
//
// Runs the real app against the real Firebase emulators (seeded: alice, bob,
// demo-couple). Board setup uses the debug-only simulated board, because an
// AVD has no BLE radio to reach a real one. Screenshots of every screen go to
// app/build/avd_screens/ (see test_driver/integration_test.dart).
//
// Run (emulators up and seeded, AVD running):
//   tool/avd_test.sh            (or the flutter drive line in it)
import 'dart:convert';

import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:heartsync/core/firebase_init.dart';
import 'package:heartsync/data/simulated_board.dart';
import 'package:heartsync/main.dart';
import 'package:integration_test/integration_test.dart';

final binding = IntegrationTestWidgetsFlutterBinding.ensureInitialized();

var _surfaceConverted = false;

Future<void> shot(WidgetTester tester, String name) async {
  if (!_surfaceConverted) {
    await binding.convertFlutterSurfaceToImage();
    _surfaceConverted = true;
  }
  await tester.pump(const Duration(milliseconds: 300));
  await binding.takeScreenshot(name);
}

/// pumpAndSettle never settles while a progress indicator spins, so pump until
/// [finder] shows up (or fail with what was expected).
Future<void> pumpUntil(
  WidgetTester tester,
  Finder finder, {
  Duration timeout = const Duration(seconds: 30),
}) async {
  final end = DateTime.now().add(timeout);
  while (DateTime.now().isBefore(end)) {
    await tester.pump(const Duration(milliseconds: 200));
    if (finder.evaluate().isNotEmpty) return;
  }
  fail('Timed out after $timeout waiting for $finder');
}

Future<void> startApp(WidgetTester tester) async {
  await tester.pumpWidget(const ProviderScope(child: HeartsyncApp()));
  await tester.pump();
}

Future<void> signIn(WidgetTester tester, String email, String password) async {
  await pumpUntil(tester, find.text('Sign in'));
  await tester.enterText(find.byKey(const Key('email')), email);
  await tester.enterText(find.byKey(const Key('password')), password);
  await tester.tap(find.text('Sign in'));
}

Future<void> tapVisible(WidgetTester tester, Finder finder) async {
  await tester.ensureVisible(finder);
  await tester.pump(const Duration(milliseconds: 300));
  await tester.tap(finder);
}

Finder get _list => find.byType(Scrollable).first;

/// Opens "Set up a board" from the home screen and picks the simulated board.
Future<void> openSimulatedSetup(WidgetTester tester) async {
  final again = find.text('Change Wi-Fi or set up again');
  final first = find.text('Set up a board');
  await pumpUntil(tester, find.byWidgetPredicate((w) {
    return w is Text && (w.data == 'Change Wi-Fi or set up again' || w.data == 'Set up a board');
  }));
  await tapVisible(tester, again.evaluate().isNotEmpty ? again : first);
  await pumpUntil(tester, find.text(SimulatedBoardSetupRepository.name));
}

void main() {
  setUpAll(() async {
    expect(simulatedBoardEnabled, isTrue,
        reason: 'run with --dart-define=SIMULATED_BOARD=true (see tool/avd_test.sh)');
    await initFirebase();
    await FirebaseAuth.instance.signOut();
  });

  testWidgets('1 sign-in: wrong password, then Bob; account letter; home', (tester) async {
    await startApp(tester);
    await pumpUntil(tester, find.text('Sign in'));
    await shot(tester, '01_login');

    await signIn(tester, 'bob@example.com', 'not-the-password');
    await pumpUntil(tester, find.text('Wrong email or password.'));
    await shot(tester, '02_login_wrong_password');

    await signIn(tester, 'bob@example.com', 'heartsync');
    await pumpUntil(tester, find.text('Send heart'));
    final badge = find.byKey(const ValueKey('account-badge'));
    expect(badge, findsOneWidget);
    expect(find.descendant(of: badge, matching: find.text('B')), findsOneWidget);
    // Connection check and Bob's board.
    await pumpUntil(tester, find.textContaining('Your board hs-20500dcd63f4'));
    await shot(tester, '03_home_bob');

    await tester.tap(badge);
    await pumpUntil(tester, find.text('Signed in as bob@example.com'));
    await shot(tester, '04_account_badge_tapped');
  });

  testWidgets('2 send a heart from the app', (tester) async {
    await startApp(tester);
    await pumpUntil(tester, find.text('Send heart'));
    await tester.tap(find.text('Send heart'));
    await pumpUntil(tester, find.text('Heart sent'), timeout: const Duration(seconds: 20));
    await shot(tester, '05_heart_sent');
  });

  testWidgets('3 setup: paging and page count, network page, wrong password, success', (
    tester,
  ) async {
    await startApp(tester);
    await openSimulatedSetup(tester);
    await shot(tester, '06_board_list');

    await tester.tap(find.text(SimulatedBoardSetupRepository.name));
    await pumpUntil(tester, find.text('${simulatedNetworks.length} networks'));
    await shot(tester, '07_wifi_list_top');

    // Page count: every page within one attribute value, all of them read in
    // order, and the app shows exactly what the board sent.
    final link = SimulatedBoardSetupRepository.lastLink!;
    final pages = link.pages;
    debugPrint('PAGECOUNT networks=${simulatedNetworks.length} pages=${pages.length} '
        'sizes=${pages.map((p) => utf8.encode(p).length).toList()} reads=${link.pageReads}');
    expect(pages.length, greaterThan(1));
    expect(pages.every((p) => utf8.encode(p).length <= 512), isTrue);
    expect(link.pageReads, List.generate(pages.length, (i) => i));
    final served = [
      for (final p in pages)
        for (final n in (jsonDecode(p) as Map)['nets'] as List) (n as Map)['ssid'],
    ];
    expect(served, simulatedNetworks.map((n) => n.ssid).toList());
    // Awkward names survive exactly.
    expect(find.text('DeltaForce '), findsOneWidget);
    expect(find.text('Café ☕ Guest'), findsOneWidget);

    await tester.scrollUntilVisible(find.text('Other network...'), 400, scrollable: _list);
    await shot(tester, '08_wifi_list_bottom');
    await tester.scrollUntilVisible(find.text('Peace'), -400, scrollable: _list);

    // Network page.
    await tester.tap(find.text('Peace'));
    await pumpUntil(tester, find.byKey(const ValueKey('network-title')));
    expect(find.text('Password protected'), findsOneWidget);
    expect(find.text('2.4 GHz'), findsOneWidget);
    FilledButton connect() =>
        tester.widget<FilledButton>(find.widgetWithText(FilledButton, 'Connect board'));
    expect(connect().onPressed, isNull, reason: 'no password yet');
    await shot(tester, '09_network_page');

    // Wrong password: stays on Peace's page with the reason and help.
    await tester.enterText(find.byKey(const ValueKey('password')), 'wrongpass1');
    await tester.pump();
    await tester.tap(find.text('Connect board'));
    await pumpUntil(tester, find.byKey(const ValueKey('wifi-error')));
    expect(find.text('Wrong Wi-Fi password.'), findsOneWidget);
    expect(tester.widget<Text>(find.byKey(const ValueKey('network-title'))).data, 'Peace');
    await shot(tester, '10_wrong_password');

    await tester.enterText(find.byKey(const ValueKey('password')), 'wrongpass2');
    await tester.pump();
    await tester.tap(find.text('Connect board'));
    await pumpUntil(tester, find.text('Failed attempts: 2'));
    await shot(tester, '11_wrong_password_twice');

    // Show/hide, then the right password: real registerDevice, token frames.
    await tester.enterText(
      find.byKey(const ValueKey('password')),
      SimulatedBoardSetupRepository.password,
    );
    await tester.tap(find.byTooltip('Show password'));
    await tester.pump();
    await shot(tester, '12_password_shown');
    await tester.tap(find.text('Connect board'));
    await pumpUntil(tester, find.textContaining('Board set up'), timeout: const Duration(seconds: 40));
    expect(link.tokenBytes, greaterThan(0));
    await shot(tester, '13_setup_done');
    await tester.tap(find.text('Done'));
    await pumpUntil(tester, find.text('Send heart'));
  });

  testWidgets('4 setup: hidden network not found, then an open network', (tester) async {
    await startApp(tester);
    await openSimulatedSetup(tester);
    await tester.tap(find.text(SimulatedBoardSetupRepository.name));
    await pumpUntil(tester, find.text('${simulatedNetworks.length} networks'));

    await tester.scrollUntilVisible(find.text('Other network...'), 400, scrollable: _list);
    await tester.tap(find.text('Other network...'));
    await pumpUntil(tester, find.byKey(const ValueKey('ssid')));
    await tester.enterText(find.byKey(const ValueKey('ssid')), 'NotHere');
    await tester.enterText(find.byKey(const ValueKey('password')), 'whatever1');
    await tester.pump();
    await shot(tester, '14_other_network');
    await tester.tap(find.text('Connect board'));
    await pumpUntil(tester, find.textContaining('cannot see that network'));
    // The typed name is kept after the failure.
    expect(tester.widget<TextField>(find.byKey(const ValueKey('ssid'))).controller!.text, 'NotHere');
    await shot(tester, '15_not_found');

    await tester.tap(find.text('All networks'));
    await pumpUntil(tester, find.text('DeltaForce '));
    await tester.tap(find.text('DeltaForce '));
    await pumpUntil(tester, find.text('Open (no password)'));
    expect(find.byKey(const ValueKey('password')), findsNothing);
    await shot(tester, '16_open_network');
    await tester.tap(find.text('Connect board'));
    await pumpUntil(tester, find.textContaining('Board set up'), timeout: const Duration(seconds: 40));
    await tester.tap(find.text('Done'));
    await pumpUntil(tester, find.text('Send heart'));
  });

  testWidgets('5 sign out, then Alice gets her own letter', (tester) async {
    await startApp(tester);
    await pumpUntil(tester, find.byTooltip('Sign out'));
    await tester.tap(find.byTooltip('Sign out'));
    await pumpUntil(tester, find.text('Sign in'));
    await signIn(tester, 'alice@example.com', 'heartsync');
    await pumpUntil(tester, find.text('Send heart'));
    final badge = find.byKey(const ValueKey('account-badge'));
    expect(find.descendant(of: badge, matching: find.text('A')), findsOneWidget);
    await pumpUntil(tester, find.textContaining('Your board hs-20500dcdfd18'));
    await shot(tester, '17_home_alice');
    await tester.tap(find.byTooltip('Sign out'));
    await pumpUntil(tester, find.text('Sign in'));
  });
}
