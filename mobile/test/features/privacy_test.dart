import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:vigia_mobile/app.dart';
import 'package:vigia_mobile/core/config/app_config.dart';
import 'package:vigia_mobile/core/network/api_client.dart';
import 'package:vigia_mobile/features/auth/data/auth_repository.dart';
import 'package:vigia_mobile/features/auth/data/profile_api.dart';
import 'package:vigia_mobile/features/patients/data/patients_api.dart';
import 'package:vigia_mobile/features/privacy/privacy.dart';
import 'package:vigia_mobile/features/today/data/agenda_api.dart';

import '../helpers/fake_agenda_api.dart';
import '../helpers/fake_patients_api.dart';
import '../helpers/fakes.dart';

/// Política, consentimiento por paciente, descarga y eliminación en la app (T-019-12, RF-019-17, 25..27).
/// Portadas de `privacy_test` y `login_consent_test` de `develop`, con la política aceptada en la app (D-101).
void main() {
  late FakeAuthRepository auth;
  late FakeProfileApi profiles;
  late FakePatientsApi patients;

  setUp(() {
    auth = FakeAuthRepository();
    profiles = FakeProfileApi();
    patients = FakePatientsApi();
  });

  void signedIn() {
    auth
      ..accounts['marta@example.com'] = 'clave1234'
      ..current = const AuthUser(uid: 'me', email: 'marta@example.com');
    profiles
      ..currentUid = 'me'
      ..profiles['me'] = profileFor('me');
  }

  Future<void> startApp(WidgetTester tester) async {
    tester.view.physicalSize = const Size(1170, 2532);
    tester.view.devicePixelRatio = 3;
    addTearDown(tester.view.reset);
    await tester.pumpWidget(
      ProviderScope(
        retry: retryOnlyConnectivity,
        overrides: [
          appConfigProvider.overrideWithValue(
            const AppConfig(environment: AppEnvironment.local, apiBaseUrl: 'http://test', authEmulatorHost: 'x'),
          ),
          authRepositoryProvider.overrideWithValue(auth),
          profileApiProvider.overrideWithValue(profiles),
          patientsApiProvider.overrideWithValue(patients),
          agendaApiProvider.overrideWithValue(FakeAgendaApi()),
        ],
        child: const VigiaApp(),
      ),
    );
    await tester.pumpAndSettle();
  }

  Future<void> openPatient(WidgetTester tester) async {
    await tester.tap(find.text('Pacientes').last);
    await tester.pumpAndSettle();
    await tester.tap(find.text('Abuela Rosa'));
    await tester.pumpAndSettle();
  }

  // Flutter solo construye y toca lo que está en pantalla: se desplaza la lista visible antes de tocar.
  Future<void> tapInList(WidgetTester tester, Finder target) async {
    await tester.scrollUntilVisible(target, 200, scrollable: find.byType(Scrollable).last);
    await tester.pumpAndSettle();
    await tester.tap(target);
    await tester.pumpAndSettle();
  }

  Future<void> openPatientPrivacy(WidgetTester tester) async {
    await openPatient(tester);
    await tapInList(tester, find.text('Privacidad'));
  }

  // ---------- Política (D-101) ----------

  testWidgets('al ingresar con la política pendiente se muestra la política, no Hoy', (tester) async {
    auth.accounts['marta@example.com'] = 'clave1234';
    profiles
      ..currentUid = 'uid-marta@example.com'
      ..profiles['uid-marta@example.com'] = profileFor('uid-marta@example.com')
      ..policyAccepted = false;
    await startApp(tester);

    await tester.enterText(find.byKey(const Key('login-email')), 'marta@example.com');
    await tester.enterText(find.byKey(const Key('login-password')), 'clave1234');
    await tester.tap(find.text('Ingresar'));
    await tester.pumpAndSettle();

    expect(find.text('Política de privacidad'), findsOneWidget);
    expect(find.text('Versión 2026-10-25'), findsOneWidget);
    expect(find.byType(NavigationBar), findsNothing);
  });

  testWidgets('aceptar exige marcar la lectura y luego lleva a Hoy', (tester) async {
    signedIn();
    profiles.policyAccepted = false;
    await startApp(tester);

    final accept = find.widgetWithText(FilledButton, 'Aceptar y continuar');
    expect(tester.widget<FilledButton>(accept).onPressed, isNull);

    await tester.tap(find.byKey(const Key('policy-read')));
    await tester.pumpAndSettle();
    await tester.tap(accept);
    await tester.pumpAndSettle();

    expect(profiles.acceptCalls, 1);
    expect(find.byType(NavigationBar), findsOneWidget);
  });

  testWidgets('al reabrir la app con la política pendiente vuelve a pedirla', (tester) async {
    signedIn();
    profiles.policyAccepted = false;
    await startApp(tester);

    expect(find.text('Leí y acepto la política de privacidad'), findsOneWidget);
  });

  testWidgets('desde la política se puede cambiar de cuenta', (tester) async {
    signedIn();
    profiles.policyAccepted = false;
    await startApp(tester);

    await tester.tap(find.text('Usar otra cuenta'));
    await tester.pumpAndSettle();

    expect(auth.signOutCalls, 1);
    expect(find.text('Ingresar'), findsOneWidget);
  });

  testWidgets('la política se puede releer desde Cuenta › Privacidad', (tester) async {
    signedIn();
    await startApp(tester);

    await tester.tap(find.text('Cuenta'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Privacidad'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Política de privacidad'));
    await tester.pumpAndSettle();

    expect(find.text('Video y cámaras'), findsOneWidget);
  });

  // ---------- Consentimiento por paciente ----------

  testWidgets('sin consentimiento de cuidado la ficha avisa y la responsable lo registra como titular', (tester) async {
    signedIn();
    final id = patients.addPatient('Abuela Rosa')['id'] as String;
    patients.consentStore[id] = {};
    await startApp(tester);
    await openPatient(tester);

    expect(find.text('Falta el consentimiento de datos de cuidado'), findsOneWidget);
    await tester.tap(find.text('Registrar consentimiento').first);
    await tester.pumpAndSettle();
    await tester.tap(find.text('Registrar consentimiento').first); // tarjeta de datos de cuidado
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('consent-confirm')));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Registrar'));
    await tester.pumpAndSettle();

    expect(patients.consentStore[id]!['cuidado'], containsPair('basis', 'titular'));
    expect(find.text('Activo'), findsOneWidget);
    await tester.tap(find.byTooltip('Atrás'));
    await tester.pumpAndSettle();
    expect(find.text('Falta el consentimiento de datos de cuidado'), findsNothing);
  });

  testWidgets('con representante se exigen nombre y relación', (tester) async {
    signedIn();
    final id = patients.addPatient('Abuela Rosa')['id'] as String;
    await startApp(tester);
    await openPatientPrivacy(tester);

    await tapInList(tester, find.text('Registrar consentimiento')); // detección (cuidado ya está activo)
    await tester.tap(find.text('Un representante del paciente'));
    await tester.tap(find.byKey(const Key('consent-confirm')));
    await tester.pumpAndSettle();
    final register = find.widgetWithText(TextButton, 'Registrar');
    expect(tester.widget<TextButton>(register).onPressed, isNull);

    await tester.enterText(find.byKey(const Key('consent-name')), 'Rosa Duena');
    await tester.pumpAndSettle();
    expect(tester.widget<TextButton>(register).onPressed, isNull); // falta la relación
    await tester.enterText(find.byKey(const Key('consent-relation')), 'hija');
    await tester.pumpAndSettle();
    await tester.tap(register);
    await tester.pumpAndSettle();

    expect(patients.consentStore[id]!['deteccion'], {
      'scope': 'deteccion', 'basis': 'representante', 'representativeName': 'Rosa Duena',
      'representativeRelation': 'hija', 'active': true,
    });
    expect(find.text('Lo dio Rosa Duena (hija)'), findsOneWidget);
  });

  testWidgets('revocar pide confirmación y explica el efecto', (tester) async {
    signedIn();
    final id = patients.addPatient('Abuela Rosa')['id'] as String;
    await startApp(tester);
    await openPatientPrivacy(tester);

    await tester.tap(find.text('Revocar'));
    await tester.pumpAndSettle();
    expect(find.textContaining('No se podrán registrar nuevos datos de cuidado'), findsOneWidget);
    await tester.tap(find.widgetWithText(TextButton, 'Revocar').last);
    await tester.pumpAndSettle();

    expect(patients.consentStore[id]!['cuidado']!['active'], isFalse);
    expect(find.text('Revocado'), findsOneWidget);
  });

  testWidgets('una cuidadora ve los consentimientos pero no puede cambiarlos ni borrar al paciente', (tester) async {
    signedIn();
    final id = patients.addPatient('Abuela Rosa', relation: 'caregiver', permissions: ['patient.view'])['id'] as String;
    patients.consentStore[id] = {};
    await startApp(tester);
    await openPatient(tester);

    expect(find.textContaining('La persona responsable debe registrarlo'), findsOneWidget);
    expect(find.text('Registrar consentimiento'), findsNothing);
    await tapInList(tester, find.text('Privacidad'));

    expect(find.text('Sin registrar'), findsNWidgets(2));
    expect(find.text('Registrar consentimiento'), findsNothing);
    expect(find.text('Eliminar paciente y todos sus datos'), findsNothing);
    expect(find.text('Descargar datos del paciente'), findsNothing);
  });

  // ---------- Descarga y eliminación ----------

  testWidgets('la responsable descarga los datos del paciente en JSON', (tester) async {
    signedIn();
    patients.addPatient('Abuela Rosa');
    await startApp(tester);
    await openPatientPrivacy(tester);

    await tapInList(tester, find.text('Descargar datos del paciente'));

    expect(find.text('Datos del paciente'), findsOneWidget);
    expect(find.textContaining('"displayName": "Abuela Rosa"'), findsOneWidget);
    expect(find.text('Copiar'), findsOneWidget);
  });

  testWidgets('eliminar al paciente exige escribir su nombre', (tester) async {
    signedIn();
    final id = patients.addPatient('Abuela Rosa')['id'] as String;
    await startApp(tester);
    await openPatientPrivacy(tester);

    await tapInList(tester, find.text('Eliminar paciente y todos sus datos'));
    final delete = find.widgetWithText(TextButton, 'Eliminar');
    await tester.enterText(find.byKey(const Key('delete-patient-name')), 'Abuela');
    await tester.pumpAndSettle();
    expect(tester.widget<TextButton>(delete).onPressed, isNull);

    await tester.enterText(find.byKey(const Key('delete-patient-name')), '  abuela rosa ');
    await tester.pumpAndSettle();
    await tester.tap(delete);
    await tester.pumpAndSettle();

    expect(patients.deleted, [id]);
    expect(find.text('Aún no tienes pacientes'), findsOneWidget);
  });

  testWidgets('descargar mis datos muestra mi cuenta en JSON', (tester) async {
    signedIn();
    await startApp(tester);

    await tester.tap(find.text('Cuenta'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Privacidad'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Descargar mis datos'));
    await tester.pumpAndSettle();

    expect(find.textContaining('"kind": "account"'), findsOneWidget);
  });

  testWidgets('eliminar la cuenta con una contraseña equivocada no borra nada', (tester) async {
    signedIn();
    await startApp(tester);
    await tester.tap(find.text('Cuenta'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Privacidad'));
    await tester.pumpAndSettle();

    await tester.tap(find.text('Eliminar mi cuenta'));
    await tester.pumpAndSettle();
    await tester.enterText(find.byKey(const Key('delete-account-password')), 'equivocada');
    await tester.pumpAndSettle();
    await tester.tap(find.text('Eliminar cuenta'));
    await tester.pumpAndSettle();

    expect(find.text('Correo o contraseña incorrectos.'), findsOneWidget);
    expect(profiles.deleteCalls, 0);
    expect(auth.signOutCalls, 0);
  });

  testWidgets('eliminar la cuenta reautentica, borra y cierra la sesión', (tester) async {
    signedIn();
    await startApp(tester);
    await tester.tap(find.text('Cuenta'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Privacidad'));
    await tester.pumpAndSettle();

    await tester.tap(find.text('Eliminar mi cuenta'));
    await tester.pumpAndSettle();
    await tester.enterText(find.byKey(const Key('delete-account-password')), 'clave1234');
    await tester.pumpAndSettle();
    await tester.tap(find.text('Eliminar cuenta'));
    await tester.pumpAndSettle();

    expect(auth.reauthCalls, 1);
    expect(profiles.deleteCalls, 1);
    expect(auth.signOutCalls, 1);
    expect(find.text('Ingresar'), findsOneWidget);
  });

  test('la confirmación por nombre sigue la regla del backend', () {
    expect(sameName('  ABUELA rosa ', 'Abuela Rosa'), isTrue);
    expect(sameName('Abuela', 'Abuela Rosa'), isFalse);
    expect(sameName('', ''), isFalse);
  });

  test('el consentimiento con representante envía nombre y relación sin espacios', () {
    expect(const ConsentDraft.representative(' Rosa ', ' hija ').toJson('cuidado'), {
      'scope': 'cuidado', 'basis': 'representante', 'representativeName': 'Rosa', 'representativeRelation': 'hija',
    });
    expect(const ConsentDraft.titular().toJson('deteccion'), {'scope': 'deteccion', 'basis': 'titular'});
  });
}
