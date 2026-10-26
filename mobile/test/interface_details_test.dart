import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:vigia_mobile/core/api.dart';
import 'package:vigia_mobile/features/home/care_home.dart';
import 'package:vigia_mobile/features/patients/patient_screen.dart';
import 'package:vigia_mobile/features/posture/clock_panel.dart';
import 'package:vigia_mobile/features/subscription/subscription_panel.dart';

/// T-011-12..14 and T-014-12: details found on a ~369 dp Android phone.
http.Response json(Object body, [int status = 200]) => http.Response(
  jsonEncode(body),
  status,
  headers: {'content-type': 'application/json; charset=utf-8'},
);

const plusCaps = {
  'name': 'VIGIA Plus',
  'max_active_patients': 3,
  'portal_path': '/planes/',
  'features': {
    'care_manual': true,
    'medication_schedule': true,
    'posture_manual': true,
    'care_history': true,
    'posture_detection': false,
  },
};

void narrowPhone(WidgetTester tester) {
  tester.view.physicalSize = const Size(360, 780);
  tester.view.devicePixelRatio = 1;
  addTearDown(tester.view.resetPhysicalSize);
  addTearDown(tester.view.resetDevicePixelRatio);
}

void expectOnScreen(WidgetTester tester, String text) {
  final rect = tester.getRect(find.text(text));
  expect(rect.left, greaterThanOrEqualTo(0), reason: text);
  expect(rect.right, lessThanOrEqualTo(360), reason: text);
}

/// CareHome backed by a fake server; `onPost` answers POST /patients.
Future<List<Map<String, dynamic>>> openHome(
  WidgetTester tester, {
  Map<String, dynamic> capacity = const {'count': 1, 'limit': 3},
  List<int> postStatus = const [201],
}) async {
  narrowPhone(tester);
  FlutterSecureStorage.setMockInitialValues({});
  final posts = <Map<String, dynamic>>[];
  final api = VigiaApi(
    client: MockClient((r) async {
      final path = r.url.path;
      if (r.method == 'POST' && path.endsWith('/patients')) {
        posts.add(jsonDecode(r.body));
        final status = postStatus[posts.length - 1];
        return status == 201
            ? json({'id': 9}, 201)
            : json({'error': 'Introduzca una fecha válida.'}, status);
      }
      if (path.endsWith('/me')) {
        return json({
          'name': 'Cuenta demo',
          'username': 'demo',
          'capabilities': plusCaps,
        });
      }
      if (path.endsWith('/patients')) {
        return json({
          'patients': [],
          'capacity': {'pending': false, 'active_ids': [], ...capacity},
        });
      }
      return json({'items': []});
    }),
  )..token = 'session';
  await tester.pumpWidget(
    MaterialApp(
      home: CareHome(api: api, onLogout: () {}),
    ),
  );
  await tester.pumpAndSettle();
  return posts;
}

void main() {
  group('T-011-12 navigation fits a narrow phone', () {
    testWidgets('All six tabs are visible', (tester) async {
      await openHome(tester);
      for (final tab in [
        'Inicio',
        'Pacientes',
        'Medicinas',
        'Posturas',
        'Planes',
        'Perfil',
      ]) {
        expectOnScreen(tester, tab);
      }
      expect(tester.takeException(), isNull);
    });

    testWidgets('Every patient section is visible', (tester) async {
      narrowPhone(tester);
      FlutterSecureStorage.setMockInitialValues({});
      final api = VigiaApi(
        client: MockClient((r) async {
          if (r.url.path.endsWith('/patients/1')) {
            return json({
              'id': 1,
              'name': 'Paciente ficticio',
              'notes': '',
              'contact_name': '',
              'active': true,
              'role': 'titular',
              'allowed_actions': ['history', 'detection', 'manage_nodes'],
              'tokens': {'timer': 't', 'posture': 'p'},
              'timer': null,
            });
          }
          return json({'items': [], 'next_page': null});
        }),
      )..token = 'session';
      await tester.pumpWidget(
        MaterialApp(home: PatientScreen(api: api, id: 1)),
      );
      await tester.pumpAndSettle();
      for (final tab in [
        'Cuidados',
        'Guías',
        'Reloj',
        'Historial',
        'Monitoreo',
      ]) {
        expectOnScreen(tester, tab);
      }
      await tester.tap(find.text('Monitoreo'));
      await tester.pumpAndSettle();
      // T-011-13: without detection in the plan nothing offers the camera.
      expect(find.textContaining('Analiza y guarda'), findsNothing);
      expect(find.text('Cámara fija'), findsNothing);
      expect(tester.takeException(), isNull);
    });
  });

  group('T-011-13 reminders and plan texts', () {
    testWidgets('The clock offers only the action that applies', (
      tester,
    ) async {
      FlutterSecureStorage.setMockInitialValues({});
      final api = VigiaApi(client: MockClient((r) async => json({})));
      Future<void> show() => tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ClockPanel(
              api: api,
              timer: null,
              busy: false,
              onAction: (_) {},
            ),
          ),
        ),
      );
      await show();
      expect(find.text('Activar avisos en este teléfono'), findsOneWidget);
      expect(find.text('Desactivar avisos locales'), findsNothing);
      api.remindersEnabled = true;
      await show();
      await tester.pump(const Duration(seconds: 1));
      expect(find.text('Activar avisos en este teléfono'), findsNothing);
      expect(find.text('Desactivar avisos locales'), findsOneWidget);
    });

    testWidgets('Plus does not promise the camera', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: SingleChildScrollView(
              child: SubscriptionPanel(
                caps: plusCaps,
                baseUrl: 'http://demo',
                enableNotifications: () {},
              ),
            ),
          ),
        ),
      );
      expect(find.textContaining('cámara de este teléfono'), findsNothing);
      expect(
        find.textContaining('Los avisos requieren permiso'),
        findsOneWidget,
      );
    });
  });

  group('T-011-14 adding a patient', () {
    testWidgets('A full plan is announced before the form', (tester) async {
      final posts = await openHome(tester, capacity: {'count': 3, 'limit': 3});
      await tester.tap(find.text('Pacientes'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Agregar paciente'));
      await tester.pumpAndSettle();
      expect(find.text('Nombre del paciente'), findsNothing);
      expect(
        find.textContaining('límite de pacientes activos'),
        findsOneWidget,
      );
      expect(posts, isEmpty);
    });

    testWidgets(
      'A rejected form comes back filled, without asking consent again',
      (tester) async {
        final posts = await openHome(tester, postStatus: [400, 201]);
        await tester.tap(find.text('Pacientes'));
        await tester.pumpAndSettle();
        await tester.tap(find.text('Agregar paciente'));
        await tester.pumpAndSettle();
        await tester.enterText(
          find.byType(TextFormField).at(0),
          'Paciente nuevo',
        );
        await tester.enterText(find.byType(TextFormField).at(1), '1940-13-45');
        await tester.tap(find.text('Continuar'));
        await tester.pumpAndSettle();
        await tester.tap(find.text('El propio paciente'));
        await tester.pumpAndSettle();
        await tester.tap(find.text('Confirmar'));
        await tester.pumpAndSettle();
        expect(find.text('Introduzca una fecha válida.'), findsOneWidget);
        expect(find.text('Paciente nuevo'), findsOneWidget);
        await tester.enterText(find.byType(TextFormField).at(1), '1940-12-24');
        await tester.tap(find.text('Continuar'));
        await tester.pumpAndSettle();
        expect(find.text('¿Quién da el consentimiento?'), findsNothing);
        expect(posts, hasLength(2));
        expect(posts.last['birth_date'], '1940-12-24');
        expect(posts.last['consent_basis'], 'titular');
        expect(find.text('Nombre del paciente'), findsNothing);
      },
    );
  });

  testWidgets('T-014-12 a pending policy shows only the notice', (
    tester,
  ) async {
    narrowPhone(tester);
    FlutterSecureStorage.setMockInitialValues({});
    final api = VigiaApi(
      client: MockClient(
        (r) async => json({
          'error':
              'Acepta la política de privacidad en el portal para continuar.',
          'consent_required': true,
        }, 403),
      ),
    )..token = 'session';
    await tester.pumpWidget(
      MaterialApp(
        home: CareHome(api: api, onLogout: () {}),
      ),
    );
    await tester.pumpAndSettle();
    expect(find.text('Abrir el portal'), findsOneWidget);
    expect(find.text('Cargando plan'), findsNothing);
    expect(find.text('ACCIONES RÁPIDAS'), findsNothing);
    await tester.tap(find.text('Pacientes'));
    await tester.pumpAndSettle();
    expect(find.text('Abrir el portal'), findsOneWidget);
    expect(find.text('Agregar paciente'), findsNothing);
  });
}
