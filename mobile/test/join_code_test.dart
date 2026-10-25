import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:vigia_mobile/core/api.dart';
import 'package:vigia_mobile/features/patients/access.dart';

/// T-013-13: the code dialog must close cleanly before the preview and accept calls.
void main() {
  setUp(() => FlutterSecureStorage.setMockInitialValues({}));

  Future<bool?> openAndSubmit(
    WidgetTester tester,
    VigiaApi api,
    String code,
  ) async {
    bool? joined;
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: Builder(
            builder: (context) => TextButton(
              onPressed: () async => joined = await joinWithCode(context, api),
              child: const Text('Unirme'),
            ),
          ),
        ),
      ),
    );
    await tester.tap(find.text('Unirme'));
    await tester.pumpAndSettle();
    await tester.enterText(find.byType(TextField), code);
    await tester.tap(find.text('Revisar código'));
    await tester.pumpAndSettle();
    return joined;
  }

  http.Response json(Map<String, dynamic> body, int status) => http.Response(
    jsonEncode(body),
    status,
    headers: {'content-type': 'application/json; charset=utf-8'},
  );

  testWidgets('A valid code shows the preview and joins', (tester) async {
    final calls = <String>[];
    final api = VigiaApi(
      client: MockClient((r) async {
        calls.add('${r.url.path} ${jsonDecode(r.body)['code']}');
        return r.url.path.endsWith('preview')
            ? json({'patient_name': 'Rosa Demo', 'role': 'cuidador'}, 200)
            : json({'ok': true}, 200);
      }),
    )..token = 'session';
    await openAndSubmit(tester, api, ' ABCDE-12345 ');
    expect(find.text('Unirte a Rosa Demo'), findsOneWidget);
    await tester.tap(find.text('Confirmar'));
    await tester.pumpAndSettle();
    expect(
      find.text('Listo. Ya puedes acompañar a este paciente.'),
      findsOneWidget,
    );
    expect(calls, [
      '/api/v1/access/preview ABCDE-12345',
      '/api/v1/access/accept ABCDE-12345',
    ]);
  });

  testWidgets('A rejected code shows the server message', (tester) async {
    final api = VigiaApi(
      client: MockClient(
        (r) async => json({'error': 'El código no es válido.'}, 400),
      ),
    )..token = 'session';
    final joined = await openAndSubmit(tester, api, 'ZZZZZ-ZZZZZ');
    expect(joined, isFalse);
    expect(find.text('El código no es válido.'), findsOneWidget);
  });
}
