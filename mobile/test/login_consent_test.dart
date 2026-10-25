import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:vigia_mobile/core/api.dart';
import 'package:vigia_mobile/features/auth/session_gate.dart';

/// T-014-11: a valid session with a pending policy reaches the portal notice.
class FakeServer {
  bool accepted = false;
  final calls = <String>[];

  http.Response _json(Object body, int status) => http.Response(
    jsonEncode(body),
    status,
    headers: {'content-type': 'application/json; charset=utf-8'},
  );

  Future<http.Response> handle(http.Request r) async {
    final token = r.headers['X-Session-Token'];
    calls.add('${r.method} ${r.url.path}${token == null ? '' : ' [$token]'}');
    final path = r.url.path;
    if (path == '/_allauth/app/v1/auth/session' && r.method == 'DELETE') {
      return _json({'status': 401, 'data': {}}, 401);
    }
    if (path == '/_allauth/app/v1/auth/login') {
      // allauth refuses a second login while the sent session is still open.
      if (token != null) return _json({'status': 409}, 409);
      return _json({
        'status': 200,
        'data': {},
        'meta': {'session_token': 'fresh', 'is_authenticated': true},
      }, 200);
    }
    if (!accepted) {
      return _json({
        'error': 'Acepta la política de privacidad en el portal para continuar.',
        'consent_required': true,
        'portal_path': '/privacidad/aceptar/',
      }, 403);
    }
    if (path.endsWith('/me')) {
      return _json({
        'name': 'Cuenta demo',
        'username': 'demo',
        'capabilities': {'name': 'Free'},
      }, 200);
    }
    if (path.endsWith('/patients')) {
      return _json({
        'patients': [],
        'capacity': {'count': 0, 'pending': false},
      }, 200);
    }
    return _json({'items': []}, 200);
  }
}

void main() {
  Future<void> login(WidgetTester tester) async {
    await tester.enterText(find.byType(TextField).at(0), 'demo');
    await tester.enterText(find.byType(TextField).at(1), 'clave-demo');
    await tester.tap(find.text('Ingresar'));
    await tester.pumpAndSettle();
  }

  testWidgets('Login with a pending policy opens the portal notice', (
    tester,
  ) async {
    FlutterSecureStorage.setMockInitialValues({});
    final server = FakeServer();
    await tester.pumpWidget(
      MaterialApp(
        home: SessionGate(api: VigiaApi(client: MockClient(server.handle))),
      ),
    );
    await tester.pumpAndSettle();
    await login(tester);
    expect(find.text('Acepta la política de privacidad'), findsOneWidget);
    expect(find.text('Abrir el portal'), findsOneWidget);

    // Still pending: the notice stays.
    await tester.tap(find.text('Ya la acepté'));
    await tester.pumpAndSettle();
    expect(find.text('Acepta la política de privacidad'), findsOneWidget);

    server.accepted = true;
    await tester.tap(find.text('Ya la acepté'));
    await tester.pumpAndSettle();
    expect(find.text('Acepta la política de privacidad'), findsNothing);
    expect(find.text('Ingresar'), findsNothing);
    expect(
      server.calls.where((c) => c.contains('auth/login')),
      hasLength(1),
      reason: 'the password is not sent again',
    );
    expect(tester.takeException(), isNull);
  });

  testWidgets('Reopening the app with a pending policy shows the notice', (
    tester,
  ) async {
    FlutterSecureStorage.setMockInitialValues({'vigia_session': 'saved'});
    final server = FakeServer();
    await tester.pumpWidget(
      MaterialApp(
        home: SessionGate(api: VigiaApi(client: MockClient(server.handle))),
      ),
    );
    await tester.pumpAndSettle();
    expect(find.text('Abrir el portal'), findsOneWidget);
    expect(find.text('Ingresar'), findsNothing);
  });

  testWidgets('A stale saved session does not block a new login', (
    tester,
  ) async {
    FlutterSecureStorage.setMockInitialValues({'vigia_session': 'stale'});
    final server = FakeServer()..accepted = true;
    final api = VigiaApi(
      client: MockClient((r) async {
        // The saved session cannot be checked (no network at start).
        if (r.url.path.endsWith('/me') && r.headers['X-Session-Token'] == 'stale') {
          throw http.ClientException('sin red');
        }
        return server.handle(r);
      }),
    );
    await tester.pumpWidget(MaterialApp(home: SessionGate(api: api)));
    await tester.pumpAndSettle();
    expect(find.text('Ingresar'), findsOneWidget);
    await login(tester);
    expect(find.text('Ingresar'), findsNothing);
    expect(server.calls, contains('POST /_allauth/app/v1/auth/login'));
    expect(api.token, 'fresh');
  });
}
