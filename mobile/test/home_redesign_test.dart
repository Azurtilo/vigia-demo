import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:vigia_mobile/core/api.dart';
import 'package:vigia_mobile/features/home/care_home.dart';

/// T-015-04: the redesigned home keeps the 013 roles and the 014 gate.
http.Response json(Object body, [int status = 200]) => http.Response(
  jsonEncode(body),
  status,
  headers: {'content-type': 'application/json; charset=utf-8'},
);

void narrowPhone(WidgetTester tester) {
  tester.view.physicalSize = const Size(360, 780);
  tester.view.devicePixelRatio = 1;
  addTearDown(tester.view.resetPhysicalSize);
  addTearDown(tester.view.resetDevicePixelRatio);
}

Future<void> openHome(WidgetTester tester, MockClient client) async {
  narrowPhone(tester);
  FlutterSecureStorage.setMockInitialValues({});
  final api = VigiaApi(client: client)..token = 'session';
  await tester.pumpWidget(
    MaterialApp(
      home: CareHome(api: api, onLogout: () {}),
    ),
  );
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('Each role sees its access and the agenda actions', (
    tester,
  ) async {
    await openHome(
      tester,
      MockClient((r) async {
        final path = r.url.path;
        if (path.endsWith('/me')) {
          return json({
            'name': 'Cuenta demo',
            'username': 'demo',
            'capabilities': {
              'plan': 'plus',
              'name': 'VIGIA Plus',
              'features': {'posture_detection': false},
            },
          });
        }
        if (path.endsWith('/patients')) {
          return json({
            'patients': [
              {
                'id': 1,
                'name': 'Rosa Propia',
                'active': true,
                'role': 'titular',
              },
              {
                'id': 2,
                'name': 'Luis Familia',
                'active': true,
                'role': 'familiar',
              },
              {
                'id': 3,
                'name': 'Ana Cuidada',
                'active': true,
                'role': 'cuidador',
              },
            ],
            'capacity': {'pending': false, 'count': 1, 'limit': 3},
          });
        }
        return json({
          'items': [
            {
              'id': 'm1',
              'patient_id': 3,
              'patient': 'Ana Cuidada',
              'kind': 'medication',
              'label': 'Paracetamol',
              'dose': '500 mg',
              'status': 'pending',
              'overdue': false,
              'due': DateTime.now().toIso8601String(),
            },
          ],
        });
      }),
    );
    expect(find.text('Unirme con\nun código'), findsOneWidget);
    expect(find.text('ACCIONES RÁPIDAS'), findsOneWidget);
    await tester.scrollUntilVisible(
      find.text('Marcar administrado'),
      200,
      scrollable: find.byType(Scrollable).first,
    );
    expect(find.text('Marcar administrado'), findsOneWidget);
    await tester.tap(find.text('Pacientes'));
    await tester.pumpAndSettle();
    expect(find.text('Paciente activo'), findsOneWidget);
    await tester.scrollUntilVisible(
      find.text('Paciente activo · Cuidador'),
      200,
      scrollable: find.byType(Scrollable).first,
    );
    expect(find.text('Paciente activo · Familiar'), findsOneWidget);
    expect(find.text('Paciente activo · Cuidador'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('Without the policy only the notice and logout are shown', (
    tester,
  ) async {
    await openHome(
      tester,
      MockClient(
        (r) async => json({
          'error':
              'Acepta la política de privacidad en el portal para continuar.',
          'consent_required': true,
        }, 403),
      ),
    );
    expect(find.text('Abrir el portal'), findsOneWidget);
    expect(find.text('Cerrar sesión'), findsOneWidget);
    expect(find.text('ACCIONES RÁPIDAS'), findsNothing);
    expect(tester.takeException(), isNull);
  });
}
