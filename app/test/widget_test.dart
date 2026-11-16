import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:heartsync/core/routing.dart';
import 'package:heartsync/data/auth_repository.dart';
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

void main() {
  late FakeAuthRepository auth;
  late FakeEventRepository events;

  Future<void> pumpApp(WidgetTester tester) async {
    auth = FakeAuthRepository();
    events = FakeEventRepository();
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          authRepositoryProvider.overrideWithValue(auth),
          eventRepositoryProvider.overrideWithValue(events),
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
}
