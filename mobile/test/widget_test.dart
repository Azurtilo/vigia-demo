import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:vigia_mobile/main.dart';
import 'package:vigia_mobile/api.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  setUp(() {
    AndroidFlutterLocalNotificationsPlugin.registerWith();
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(
          const MethodChannel('dexterous.com/flutter/local_notifications'),
          (call) async => call.method == 'initialize' ? true : null,
        );
  });
  test(
    'Signing out clears device association before another account enters',
    () async {
      FlutterSecureStorage.setMockInitialValues({
        'vigia_session': 'old-session',
        'vigia_installation': 'old-account-device',
      });
      final api = VigiaApi();
      await api.restore();
      await api.forget();
      expect(api.token, isNull);
      expect(await api.storage.read(key: 'vigia_session'), isNull);
      expect(await api.storage.read(key: 'vigia_installation'), isNull);
    },
  );
  testWidgets(
    'Login failure stays visible and does not enter the patient area',
    (tester) async {
      FlutterSecureStorage.setMockInitialValues({});
      final api = VigiaApi(
        client: MockClient(
          (request) async => http.Response(
            jsonEncode({
              'errors': [
                {'message': 'Acceso inválido'},
              ],
            }),
            400,
          ),
        ),
      );
      await tester.pumpWidget(VigiaApp(api: api));
      await tester.pumpAndSettle();
      expect(find.text('Cuidar, un día a la vez.'), findsOneWidget);
      expect(find.text('Crear cuenta en la web'), findsOneWidget);
      expect(find.text('Crear una cuenta Free'), findsNothing);
      await tester.enterText(find.byType(TextField).at(0), 'demo');
      await tester.enterText(find.byType(TextField).at(1), 'incorrecta');
      await tester.ensureVisible(find.text('Ingresar'));
      await tester.tap(find.text('Ingresar'));
      await tester.pumpAndSettle();
      expect(find.text('Acceso inválido'), findsOneWidget);
      expect(find.text('Tu día de cuidado'), findsNothing);
    },
  );
  test('A failed write reports uncertainty rather than success', () async {
    FlutterSecureStorage.setMockInitialValues({});
    final api = VigiaApi(
      client: MockClient(
        (request) async => throw http.ClientException('offline'),
      ),
    );
    await expectLater(
      api.post('patients/1/events', {'token': 'signed'}),
      throwsA(
        isA<ApiError>().having(
          (e) => e.message,
          'message',
          contains('No se confirmó'),
        ),
      ),
    );
  });
  test('Session header is sent and replacement token persisted', () async {
    FlutterSecureStorage.setMockInitialValues({});
    final api = VigiaApi(
      client: MockClient((r) async {
        expect(r.headers['X-Session-Token'], 'old');
        return http.Response(
          jsonEncode({
            'meta': {'session_token': 'new'},
          }),
          200,
        );
      }),
    );
    api.token = 'old';
    await api.get('me');
    expect(api.token, 'new');
  });
}
