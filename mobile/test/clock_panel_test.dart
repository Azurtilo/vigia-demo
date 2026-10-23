import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:vigia_mobile/core/api.dart';
import 'package:vigia_mobile/features/patients/patient_screen.dart';
import 'package:vigia_mobile/features/posture/clock_panel.dart';

void main() {
  testWidgets(
    'Patient without events creates a clock without recording a posture',
    (tester) async {
      FlutterSecureStorage.setMockInitialValues({});
      Map<String, dynamic>? timer;
      final posts = <String, Map<String, dynamic>>{};
      final api = VigiaApi(
        client: MockClient((r) async {
          final path = r.url.path;
          Object response = {'items': [], 'next_page': null};
          if (r.method == 'POST') {
            posts[path] = jsonDecode(r.body);
            timer = {
              'interval': 90,
              'paused': false,
              'next_due_at': DateTime.now()
                  .add(const Duration(minutes: 90))
                  .toIso8601String(),
              'generation': 1,
            };
            response = {'saved': true};
          } else if (path.endsWith('/patients/1')) {
            response = {
              'id': 1,
              'name': 'Paciente ficticio',
              'active': true,
              'tokens': {'timer': 'signed-timer', 'posture': 'signed-posture'},
              'timer': timer,
            };
          } else if (path.endsWith('/capabilities')) {
            response = {};
          }
          return http.Response(
            jsonEncode(response),
            200,
            headers: {'content-type': 'application/json; charset=utf-8'},
          );
        }),
      );
      await tester.pumpWidget(
        MaterialApp(
          home: PatientScreen(api: api, id: 1, initialTab: 4),
        ),
      );
      await tester.pumpAndSettle();
      expect(find.text('Pausar'), findsNothing);
      expect(find.text('Cambiar intervalo'), findsNothing);
      await tester.tap(find.text('Crear recordatorio'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('90 minutos'));
      await tester.pumpAndSettle();
      expect(posts.keys, ['/api/v1/patients/1/timer']);
      expect(posts.values.single, {
        'token': 'signed-timer',
        'action': 'start',
        'interval': 90,
      });
      expect(find.text('Crear recordatorio'), findsNothing);
      expect(find.text('Pausar'), findsOneWidget);
      expect(find.text('Cambiar intervalo'), findsOneWidget);
      await tester.pumpWidget(const SizedBox());
    },
  );

  testWidgets('Archived patient sees the clock but cannot act on it', (
    tester,
  ) async {
    final actions = <String>[];
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: ClockPanel(
            api: VigiaApi(),
            timer: null,
            busy: false,
            enabled: false,
            onAction: actions.add,
          ),
        ),
      ),
    );
    expect(
      find.text('Paciente archivado: reactívalo para usar el reloj.'),
      findsOneWidget,
    );
    await tester.tap(find.text('Crear recordatorio'));
    expect(actions, isEmpty);
    await tester.pumpWidget(const SizedBox());
  });
}
