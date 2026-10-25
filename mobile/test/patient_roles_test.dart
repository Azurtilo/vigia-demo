import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:vigia_mobile/core/api.dart';
import 'package:vigia_mobile/features/patients/access.dart';
import 'package:vigia_mobile/features/patients/patient_screen.dart';

/// Spec 013: the app adapts to `role`/`allowed_actions`; the server enforces them.
const caregiverActions = ['correct', 'leave', 'record', 'view'];
const titularActions = [
  'archive',
  'configure',
  'correct',
  'detection',
  'edit_patient',
  'history',
  'manage_access',
  'manage_nodes',
  'record',
  'view',
];

class RoleServer {
  final String role;
  final List<String> actions;
  final requested = <String>[];
  RoleServer(this.role, this.actions);

  MockClient client() => MockClient((r) async {
    final path = r.url.path;
    requested.add('${r.method} $path');
    Object body = {'items': [], 'next_page': null};
    if (path.endsWith('/patients/1')) {
      body = {
        'id': 1,
        'name': 'Paciente ficticio',
        'notes': '',
        'contact_name': '',
        'active': true,
        'role': role,
        'allowed_actions': actions,
        'tokens': {'timer': 't', 'posture': 'p'},
        'timer': null,
      };
    } else if (path.endsWith('/patients/1/observations')) {
      body = {
        'items': [
          {
            'id': 7,
            'posture': 'indeterminada',
            'risk': 'fall',
            'observed_at': '2026-10-25T10:00:00Z',
            'source': 'Cámara',
          },
        ],
        'next_page': null,
      };
    } else if (path.endsWith('/patients/1/access')) {
      body = {'accesses': [], 'invitations': []};
    } else if (path.endsWith('/capabilities')) {
      body = {};
    }
    return http.Response(
      jsonEncode(body),
      200,
      headers: {'content-type': 'application/json; charset=utf-8'},
    );
  });
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  setUp(() => FlutterSecureStorage.setMockInitialValues({}));

  Future<RoleServer> open(
    WidgetTester tester,
    String role,
    List<String> actions,
  ) async {
    final server = RoleServer(role, actions);
    final api = VigiaApi(client: server.client())..token = 'session';
    await tester.pumpWidget(MaterialApp(home: PatientScreen(api: api, id: 1)));
    await tester.pumpAndSettle();
    return server;
  }

  testWidgets('Caregiver sees no history, monitoring, edit or archive', (
    tester,
  ) async {
    final server = await open(tester, 'cuidador', caregiverActions);
    expect(find.textContaining('Accedes como cuidador'), findsOneWidget);
    expect(find.text('Historial'), findsNothing);
    expect(find.text('Monitoreo'), findsNothing);
    expect(find.byTooltip('Editar ficha'), findsNothing);
    expect(find.byTooltip('Agregar Medicamentos'), findsNothing);
    expect(find.text('Archivar paciente'), findsNothing);
    expect(find.text('Personas con acceso'), findsNothing);
    await tester.scrollUntilVisible(
      find.text('Dejar de acompañar'),
      200,
      scrollable: find.byType(Scrollable).first,
    );
    expect(find.text('Dejar de acompañar'), findsOneWidget);
    // D-062: the app never asks for what the caregiver may not see.
    expect(server.requested.where((p) => p.contains('/history')), isEmpty);
    expect(server.requested.where((p) => p.contains('/observations')), isEmpty);
    expect(server.requested.where((p) => p.contains('/nodes')), isEmpty);
  });

  testWidgets('Titular manages access and keeps every section', (tester) async {
    final server = await open(tester, 'titular', titularActions);
    expect(find.text('Historial'), findsOneWidget);
    expect(find.text('Monitoreo'), findsOneWidget);
    expect(find.byTooltip('Editar ficha'), findsOneWidget);
    expect(find.text('Dejar de acompañar'), findsNothing);
    await tester.scrollUntilVisible(
      find.text('Personas con acceso'),
      200,
      scrollable: find.byType(Scrollable).first,
    );
    expect(find.text('Nadie más tiene acceso a esta ficha.'), findsOneWidget);
    expect(server.requested, contains('GET /api/v1/patients/1/access'));
  });

  testWidgets('A fall is titled as a possible fall, not as a posture', (
    tester,
  ) async {
    await open(tester, 'titular', titularActions);
    await tester.tap(find.text('Monitoreo'));
    await tester.pumpAndSettle();
    await tester.scrollUntilVisible(
      find.text('Posible caída'),
      200,
      scrollable: find.byType(Scrollable).first,
    );
    expect(find.text('Posible caída'), findsOneWidget);
    expect(find.text('No se puede determinar'), findsNothing);
  });

  test('Older servers without roles keep full access', () {
    expect(allows({'id': 1}, 'history'), isTrue);
    expect(allows({'id': 1}, 'leave'), isFalse);
    expect(allows({'allowed_actions': caregiverActions}, 'history'), isFalse);
    expect(roleLabel('cuidador'), 'Cuidador');
  });
}
