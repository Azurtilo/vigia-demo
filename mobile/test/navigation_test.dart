import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:vigia_mobile/api.dart';
import 'package:vigia_mobile/care.dart';

void main() {
  testWidgets(
    'Medicinas filters care tasks and retains omissions on a narrow screen',
    (tester) async {
      tester.view.physicalSize = const Size(390, 844);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      FlutterSecureStorage.setMockInitialValues({});
      final api = VigiaApi(
        client: MockClient((r) async {
          final Object response;
          if (r.url.path.endsWith('/me')) {
            response = {
              'name': 'Cuenta demo',
              'username': 'demo',
              'capabilities': {'name': 'Free'},
            };
          } else if (r.url.path.endsWith('/patients')) {
            response = {
              'patients': [],
              'capacity': {'count': 0, 'pending': false},
            };
          } else {
            response = {
              'items': [
                {
                  'kind': 'medication',
                  'label': 'Medicina omitida demo',
                  'patient': 'Paciente ficticio',
                  'patient_id': 1,
                  'due': null,
                  'dose': 'Dosis de prueba',
                  'status': 'omitted',
                  'overdue': false,
                },
                {
                  'kind': 'task',
                  'label': 'Higiene demo',
                  'patient': 'Paciente ficticio',
                  'patient_id': 1,
                  'due': null,
                  'dose': '',
                  'status': 'pending',
                  'overdue': false,
                },
              ],
            };
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
          home: CareHome(api: api, onLogout: () {}),
        ),
      );
      await tester.pumpAndSettle();
      expect(tester.takeException(), isNull);
      await tester.tap(find.text('Medicinas'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Omitidos'));
      await tester.pumpAndSettle();
      expect(find.text('Medicina omitida demo'), findsOneWidget);
      expect(find.text('Higiene demo'), findsNothing);
      expect(tester.takeException(), isNull);
    },
  );
}
