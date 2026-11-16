import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:heartsync/core/routing.dart';
import 'package:heartsync/data/auth_repository.dart';
import 'package:heartsync/data/connection_repository.dart';
import 'package:heartsync/data/event_repository.dart';

class FakeAuthRepository implements AuthRepository {
  final _controller = StreamController<String?>.broadcast();
  String? lastEmail;

  @override
  Stream<String?> uidChanges() async* {
    yield null;
    yield* _controller.stream;
  }

  @override
  Future<void> signIn({required String email, required String password}) async {
    if (password != 'heartsync') throw const AuthFailure('Wrong email or password.');
    lastEmail = email;
    _controller.add('alice');
  }

  @override
  Future<void> signOut() async => _controller.add(null);
}

class FakeEventRepository implements EventRepository {
  int hearts = 0;
  EventFailure? failure;

  @override
  Future<String> sendHeart() async {
    if (failure != null) throw failure!;
    hearts++;
    return 'event-$hearts';
  }
}

class FakeConnectionRepository implements ConnectionRepository {
  ConnectionReport report = const ConnectionReport(checks: [], devices: [], uid: 'alice');

  @override
  Future<ConnectionReport> check() async => report;
}

void main() {
  late FakeAuthRepository auth;
  late FakeEventRepository events;
  late FakeConnectionRepository connection;

  Future<void> pumpApp(WidgetTester tester) async {
    auth = FakeAuthRepository();
    events = FakeEventRepository();
    connection = FakeConnectionRepository();
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          authRepositoryProvider.overrideWithValue(auth),
          eventRepositoryProvider.overrideWithValue(events),
          connectionRepositoryProvider.overrideWithValue(connection),
        ],
        child: const MaterialApp(home: AuthGate()),
      ),
    );
    await tester.pumpAndSettle();
  }

  Future<void> signIn(WidgetTester tester, {String password = 'heartsync'}) async {
    await tester.enterText(find.byKey(const Key('email')), 'alice@example.com');
    await tester.enterText(find.byKey(const Key('password')), password);
    await tester.tap(find.text('Sign in'));
    await tester.pumpAndSettle();
  }

  testWidgets('shows the login screen when signed out', (tester) async {
    await pumpApp(tester);
    expect(find.text('Sign in'), findsOneWidget);
    expect(find.text('Send heart'), findsNothing);
  });

  testWidgets('a wrong password shows an error and stays on login', (tester) async {
    await pumpApp(tester);
    await signIn(tester, password: 'nope');
    expect(find.text('Wrong email or password.'), findsOneWidget);
    expect(find.text('Send heart'), findsNothing);
  });

  testWidgets('signing in shows the Send heart button, which sends a heart', (tester) async {
    await pumpApp(tester);
    await signIn(tester);
    expect(auth.lastEmail, 'alice@example.com');
    expect(find.text('Send heart'), findsOneWidget);

    await tester.tap(find.text('Send heart'));
    await tester.pumpAndSettle();
    expect(events.hearts, 1);
    expect(find.text('Heart sent'), findsOneWidget);
  });

  testWidgets('a failed send shows the reason', (tester) async {
    await pumpApp(tester);
    await signIn(tester);
    events.failure = const EventFailure('You are not paired with a partner yet.');
    await tester.tap(find.text('Send heart'));
    await tester.pumpAndSettle();
    expect(events.hearts, 0);
    expect(find.text('You are not paired with a partner yet.'), findsOneWidget);
  });

  testWidgets('signing out returns to the login screen', (tester) async {
    await pumpApp(tester);
    await signIn(tester);
    await tester.tap(find.byTooltip('Sign out'));
    await tester.pumpAndSettle();
    expect(find.text('Sign in'), findsOneWidget);
  });

  testWidgets('with no board of your own, the home screen offers setup', (tester) async {
    await pumpApp(tester);
    await signIn(tester);
    expect(find.text('Set up a board'), findsOneWidget);
    expect(find.textContaining('is set up'), findsNothing);
  });

  testWidgets('once your board is registered, it shows as set up', (tester) async {
    await pumpApp(tester);
    connection.report = ConnectionReport(
      checks: const [],
      uid: 'alice',
      devices: [
        DeviceStatus(
          deviceId: 'hs-20500dcdfd18',
          ownerUid: 'alice',
          firmwareVersion: '0.1.0',
          lastSeen: DateTime.now(),
        ),
        const DeviceStatus(
          deviceId: 'hs-20500dcd63f4',
          ownerUid: 'bob',
          firmwareVersion: '0.1.0',
          lastSeen: null,
        ),
      ],
    );
    await signIn(tester);
    expect(find.text('Your board hs-20500dcdfd18 is set up'), findsOneWidget);
    expect(find.text('Online.'), findsOneWidget);
    expect(find.text('Set up a board'), findsNothing);
    expect(find.text('Change Wi-Fi or set up again'), findsOneWidget);
  });

  testWidgets('the home screen shows the connection check and both boards', (tester) async {
    await pumpApp(tester);
    final now = DateTime.now();
    connection.report = ConnectionReport(
      uid: 'alice',
      checks: const [
        CheckResult(label: 'Functions', ok: true, detail: '10.0.0.1:5001 reachable'),
        CheckResult(label: 'Paired', ok: true, detail: 'Couple demo-couple'),
      ],
      devices: [
        DeviceStatus(
          deviceId: 'hs-aaaaaaaaaaaa',
          ownerUid: 'alice',
          firmwareVersion: '0.1.0',
          lastSeen: now.subtract(const Duration(seconds: 20)),
        ),
        DeviceStatus(
          deviceId: 'hs-bbbbbbbbbbbb',
          ownerUid: 'bob',
          firmwareVersion: '0.1.0',
          lastSeen: now.subtract(const Duration(minutes: 10)),
        ),
      ],
    );
    await signIn(tester);
    expect(find.text('Connection check'), findsOneWidget);
    expect(find.text('Functions'), findsOneWidget);
    expect(find.text('Your board hs-aaaaaaaaaaaa'), findsOneWidget);
    expect(find.text("Partner's board hs-bbbbbbbbbbbb"), findsOneWidget);
    expect(find.textContaining('online, seen'), findsOneWidget);
    expect(find.textContaining('offline, seen 10m ago'), findsOneWidget);
  });

  test('a board is online only within two missed heartbeats', () {
    final now = DateTime(2026, 11, 16, 12);
    DeviceStatus seen(Duration ago) => DeviceStatus(
      deviceId: 'hs-x',
      ownerUid: 'a',
      firmwareVersion: '0.1.0',
      lastSeen: now.subtract(ago),
    );
    expect(seen(const Duration(seconds: 59)).isOnline(now), isTrue);
    expect(seen(const Duration(seconds: 150)).isOnline(now), isTrue);
    expect(seen(const Duration(seconds: 151)).isOnline(now), isFalse);
    const never = DeviceStatus(
      deviceId: 'hs-y',
      ownerUid: 'a',
      firmwareVersion: '0.1.0',
      lastSeen: null,
    );
    expect(never.isOnline(now), isFalse);
  });
}
