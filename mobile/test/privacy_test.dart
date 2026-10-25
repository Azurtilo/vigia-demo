import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:vigia_mobile/core/api.dart';
import 'package:vigia_mobile/features/home/care_home.dart';
import 'package:vigia_mobile/features/profile/privacy.dart';

/// Spec 014: policy gate in the app and consent when creating a patient.
void main() {
  setUp(() => FlutterSecureStorage.setMockInitialValues({}));

  testWidgets('A pending policy shows the portal notice, not a raw error', (
    tester,
  ) async {
    final api = VigiaApi(
      client: MockClient(
        (r) async => http.Response(
          jsonEncode({
            'error':
                'Acepta la política de privacidad en el portal para continuar.',
            'consent_required': true,
            'portal_path': '/privacidad/aceptar/',
          }),
          403,
          headers: {'content-type': 'application/json; charset=utf-8'},
        ),
      ),
    )..token = 'session';
    await tester.pumpWidget(
      MaterialApp(
        home: CareHome(api: api, onLogout: () {}),
      ),
    );
    await tester.pumpAndSettle();
    expect(find.text('Acepta la política de privacidad'), findsOneWidget);
    expect(find.text('Abrir el portal'), findsOneWidget);
    expect(find.text('Reintentar'), findsNothing);
  });

  testWidgets('The patient consents personally', (tester) async {
    Map<String, dynamic>? result;
    await tester.pumpWidget(
      MaterialApp(
        home: Builder(
          builder: (context) => TextButton(
            onPressed: () async => result = await askPatientConsent(context),
            child: const Text('Agregar'),
          ),
        ),
      ),
    );
    await tester.tap(find.text('Agregar'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('El propio paciente'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Confirmar'));
    await tester.pumpAndSettle();
    expect(result, {'consent_basis': 'titular', 'consent_confirm': true});
  });

  testWidgets('A representative needs name and relation', (tester) async {
    Map<String, dynamic>? result;
    await tester.pumpWidget(
      MaterialApp(
        home: Builder(
          builder: (context) => TextButton(
            onPressed: () async => result = await askPatientConsent(context),
            child: const Text('Agregar'),
          ),
        ),
      ),
    );
    await tester.tap(find.text('Agregar'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Un representante del paciente'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Continuar'));
    await tester.pumpAndSettle();
    expect(find.text('Completa este campo.'), findsNWidgets(2));
    await tester.enterText(find.byType(TextFormField).at(0), 'Hija Demo');
    await tester.enterText(find.byType(TextFormField).at(1), 'Hija');
    await tester.tap(find.text('Continuar'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Confirmar'));
    await tester.pumpAndSettle();
    expect(result, {
      'consent_basis': 'representante',
      'representative_name': 'Hija Demo',
      'representative_relation': 'Hija',
      'consent_confirm': true,
    });
  });

  test('Only a consent_required response triggers the notice', () {
    expect(
      consentRequired(ApiError('x', 403, {'consent_required': true})),
      isTrue,
    );
    expect(consentRequired(ApiError('x', 403)), isFalse);
    expect(consentRequired(Exception('red')), isFalse);
  });
}
