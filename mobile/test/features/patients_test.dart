import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:vigia_mobile/app.dart';
import 'package:vigia_mobile/core/config/app_config.dart';
import 'package:vigia_mobile/core/network/api_client.dart';
import 'package:vigia_mobile/features/auth/data/auth_repository.dart';
import 'package:vigia_mobile/features/auth/data/profile_api.dart';
import 'package:vigia_mobile/features/patients/data/patients_api.dart';

import '../helpers/fake_patients_api.dart';
import '../helpers/fakes.dart';

/// Pantallas de pacientes con sesión iniciada y backend falso.
void main() {
  late FakeAuthRepository auth;
  late FakeProfileApi profiles;
  late FakePatientsApi patients;

  setUp(() {
    auth = FakeAuthRepository()..current = const AuthUser(uid: 'me', email: 'marta@example.com');
    profiles = FakeProfileApi()
      ..currentUid = 'me'
      ..profiles['me'] = profileFor('me');
    patients = FakePatientsApi();
  });

  Future<void> openPatients(WidgetTester tester) async {
    tester.view.physicalSize = const Size(1170, 2532);
    tester.view.devicePixelRatio = 3;
    addTearDown(tester.view.reset);
    await tester.pumpWidget(
      ProviderScope(
        retry: retryOnlyConnectivity, // la misma regla de reintentos que main.dart
        overrides: [
          appConfigProvider.overrideWithValue(
            const AppConfig(environment: AppEnvironment.local, apiBaseUrl: 'http://test', authEmulatorHost: 'x'),
          ),
          authRepositoryProvider.overrideWithValue(auth),
          profileApiProvider.overrideWithValue(profiles),
          patientsApiProvider.overrideWithValue(patients),
        ],
        child: const VigiaApp(),
      ),
    );
    await tester.pumpAndSettle();
    await tester.tap(find.text('Pacientes').last);
    await tester.pumpAndSettle();
  }

  // Se desplaza la lista del formulario (no las otras pestañas ni los campos de texto,
  // que también son desplazables). Flutter solo construye lo que está cerca de la vista.
  Future<void> scrollTo(WidgetTester tester, Finder target, {double delta = 300}) => tester.scrollUntilVisible(
        target,
        delta,
        scrollable: find.descendant(of: find.byType(Form), matching: find.byType(Scrollable)).first,
      );

  testWidgets('sin pacientes ofrece registrar o unirse con código', (tester) async {
    await openPatients(tester);

    expect(find.text('Aún no tienes pacientes'), findsOneWidget);
    expect(find.text('Registrar paciente'), findsOneWidget);
    expect(find.text('Unirme con código'), findsOneWidget);
  });

  testWidgets('registrar un paciente lo muestra en su ficha y en la lista', (tester) async {
    await openPatients(tester);

    await tester.tap(find.text('Registrar paciente'));
    await tester.pumpAndSettle();
    await tester.enterText(find.byKey(const Key('patient-name')), 'Abuela Rosa');
    await scrollTo(tester, find.byKey(const Key('allergy-input')));
    await tester.enterText(find.byKey(const Key('allergy-input')), 'Penicilina');
    await tester.tap(find.byTooltip('Agregar alergia'));
    await tester.pumpAndSettle();
    await scrollTo(tester, find.byKey(const Key('patient-save')));
    await tester.tap(find.byKey(const Key('patient-save')));
    await tester.pumpAndSettle();

    expect(find.text('Abuela Rosa'), findsWidgets); // título de la ficha
    expect(find.text('Penicilina'), findsOneWidget); // alergias destacadas
    expect(patients.lastDraft!.allergies, ['Penicilina']);
    await tester.tap(find.text('Pacientes').last); // volver a la lista desde la barra inferior
    await tester.pumpAndSettle();
    expect(find.text('Abuela Rosa'), findsOneWidget); // en la lista
    expect(find.textContaining('1 de 1 pacientes activos'), findsOneWidget);
  });

  testWidgets('el nombre es obligatorio', (tester) async {
    await openPatients(tester);
    await tester.tap(find.text('Registrar paciente'));
    await tester.pumpAndSettle();

    await scrollTo(tester, find.byKey(const Key('patient-save')));
    await tester.tap(find.byKey(const Key('patient-save')));
    await tester.pumpAndSettle();
    await scrollTo(tester, find.text('Escribe un nombre o identificador.'), delta: -300);

    expect(find.text('Escribe un nombre o identificador.'), findsOneWidget);
    expect(patients.lastDraft, isNull);
  });

  testWidgets('con el plan lleno, registrar se desactiva y se explica por qué', (tester) async {
    patients.addPatient('Abuela Rosa');
    await openPatients(tester);

    final button = tester.widget<ButtonStyleButton>(find.ancestor(of: find.text('Registrar paciente'), matching: find.byWidgetPredicate((w) => w is ButtonStyleButton)));
    expect(button.onPressed, isNull);
    expect(find.textContaining('Llegaste al límite de tu plan'), findsOneWidget);
    expect(find.textContaining('archiva un paciente o cambia de plan'), findsOneWidget);
  });

  testWidgets('si el backend rechaza por límite, se muestra su mensaje', (tester) async {
    patients.maxPatients = 1;
    await openPatients(tester); // la lista aún muestra cupo
    patients.addPatient('Otro creado en otro teléfono'); // el cupo se llenó después

    await tester.tap(find.text('Registrar paciente'));
    await tester.pumpAndSettle();
    await tester.enterText(find.byKey(const Key('patient-name')), 'Tía');
    await scrollTo(tester, find.byKey(const Key('patient-save')));
    await tester.tap(find.byKey(const Key('patient-save')));
    await tester.pumpAndSettle();

    expect(find.textContaining('Tu plan Gratis permite hasta 1'), findsOneWidget);
  });

  testWidgets('una cuidadora no ve "Editar" ni archivar', (tester) async {
    patients.addPatient('Mamá de Marta', relation: 'caregiver', permissions: ['patient.view', 'meds.administer']);
    await openPatients(tester);

    await tester.tap(find.text('Mamá de Marta'));
    await tester.pumpAndSettle();

    expect(find.text('Eres cuidador/a'), findsOneWidget);
    expect(find.text('Editar'), findsNothing);
    expect(find.byTooltip('Más opciones'), findsNothing);
  });

  testWidgets('la responsable puede archivar con confirmación', (tester) async {
    patients.addPatient('Abuela Rosa');
    await openPatients(tester);
    await tester.tap(find.text('Abuela Rosa'));
    await tester.pumpAndSettle();

    await tester.tap(find.byTooltip('Más opciones'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Archivar paciente'));
    await tester.pumpAndSettle();
    expect(find.textContaining('Su información e historial se conservan'), findsOneWidget);
    await tester.tap(find.widgetWithText(TextButton, 'Archivar'));
    await tester.pumpAndSettle();

    expect(find.textContaining('Paciente archivado'), findsOneWidget);
  });

  testWidgets('unirse con código: valida el formato y muestra el error del backend', (tester) async {
    await openPatients(tester);
    await tester.tap(find.text('Unirme con código'));
    await tester.pumpAndSettle();

    await tester.enterText(find.byKey(const Key('join-code')), 'ABC');
    await tester.tap(find.text('Unirme'));
    await tester.pumpAndSettle();
    expect(find.textContaining('20 letras y números'), findsOneWidget);

    await tester.enterText(find.byKey(const Key('join-code')), 'AAAA-BBBB-CCCC-DDDD-EEEE');
    await tester.tap(find.text('Unirme'));
    await tester.pumpAndSettle();
    expect(find.text('El código de invitación no es válido.'), findsOneWidget);
  });

  testWidgets('unirse con un código válido abre la ficha del paciente compartido', (tester) async {
    patients.invitations['59XBSV6SB7RCV4K4PU6N'] = {
      'id': 'shared', 'ownerUid': 'marta', 'displayName': 'Mamá de Marta', 'timeZone': 'America/Santiago',
      'status': 'active', 'allergies': ['Penicilina'], 'emergencyContacts': [],
      'myRelation': 'caregiver', 'myPermissions': ['patient.view'],
    };
    await openPatients(tester);
    await tester.tap(find.text('Unirme con código'));
    await tester.pumpAndSettle();

    await tester.enterText(find.byKey(const Key('join-code')), '59xb-sv6s-b7rc-v4k4-pu6n');
    await tester.tap(find.text('Unirme'));
    await tester.pumpAndSettle();

    expect(find.text('Mamá de Marta'), findsWidgets);
    expect(find.text('Eres cuidador/a'), findsOneWidget);
  });

  testWidgets('sin conexión la lista ofrece reintentar', (tester) async {
    patients
      ..failure = offline
      ..failuresLeft = 3; // la carga inicial y los 2 reintentos automáticos
    await openPatients(tester);
    await tester.pump(const Duration(seconds: 10)); // deja pasar los reintentos (2 s y 4 s)
    await tester.pumpAndSettle();

    expect(find.textContaining('No pudimos conectar con VIGIA'), findsOneWidget);
    await tester.tap(find.text('Reintentar'));
    await tester.pumpAndSettle();

    expect(find.text('Aún no tienes pacientes'), findsOneWidget);
  });
}
