import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:vigia_mobile/app.dart';
import 'package:vigia_mobile/core/config/app_config.dart';
import 'package:vigia_mobile/core/network/api_client.dart';
import 'package:vigia_mobile/features/auth/data/auth_repository.dart';
import 'package:vigia_mobile/features/auth/data/profile_api.dart';
import 'package:vigia_mobile/features/patients/data/patients_api.dart';
import 'package:vigia_mobile/features/today/data/agenda_api.dart';

import '../helpers/fake_agenda_api.dart';
import '../helpers/fake_patients_api.dart';
import '../helpers/fakes.dart';

/// Pantalla Hoy con sesión iniciada y backend falso.
void main() {
  late FakeAuthRepository auth;
  late FakeProfileApi profiles;
  late FakePatientsApi patients;
  late FakeAgendaApi agenda;

  setUp(() {
    auth = FakeAuthRepository()..current = const AuthUser(uid: 'me', email: 'carla@example.com');
    profiles = FakeProfileApi()
      ..currentUid = 'me'
      ..profiles['me'] = profileFor('me', name: 'Carla');
    patients = FakePatientsApi();
    agenda = FakeAgendaApi();
  });

  Future<void> openToday(WidgetTester tester) async {
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
          agendaApiProvider.overrideWithValue(agenda),
        ],
        child: const VigiaApp(),
      ),
    );
    await tester.pumpAndSettle();
  }

  String pid(Map<String, dynamic> p) => p['id'] as String;

  // La hoja puede ser más alta que la pantalla: se desplaza hasta Guardar, como lo haría una persona.
  Future<void> save(WidgetTester tester) async {
    await tester.ensureVisible(find.byKey(const Key('record-save')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('record-save')));
  }

  testWidgets('sin pacientes invita a ir a Pacientes', (tester) async {
    await openToday(tester);

    expect(find.text('Aún no hay pacientes'), findsOneWidget);
    expect(find.text('Ir a Pacientes'), findsOneWidget);
  });

  testWidgets('muestra la agenda en orden, con estados y quién registró', (tester) async {
    final p = pid(patients.addPatient('Mamá de Marta', relation: 'caregiver', permissions: ['patient.view', 'meds.administer', 'care.record']));
    agenda.members[p] = {'marta': 'Marta'};
    agenda.items[p] = [
      FakeAgendaApi.med('m1', '08:00', '2026-10-26T11:00:00Z', status: 'delayed', log: {
        'id': 'l1', 'recordedBy': 'marta', 'actualAt': '2026-10-26T16:01:00Z', 'reason': 'Estaba durmiendo',
      }),
      FakeAgendaApi.task('t1', '09:00', '2026-10-26T12:00:00Z'),
      FakeAgendaApi.med('m1', '20:00', '2026-10-26T23:00:00Z'),
    ];
    await openToday(tester);

    expect(find.text('Mamá de Marta'), findsOneWidget);
    expect(find.text('1 de 3'), findsOneWidget);
    expect(find.textContaining('lunes 26 de octubre'), findsOneWidget);
    expect(find.textContaining('Retrasada'), findsOneWidget);
    expect(find.textContaining('Marta'), findsWidgets); // quién registró
    expect(find.text('Motivo: Estaba durmiendo'), findsOneWidget);
    expect(find.byTooltip('Registrar Paracetamol de las 20:00'), findsOneWidget);
    expect(find.byTooltip('Registrar Hidratar de las 09:00'), findsOneWidget);
    expect(find.byTooltip('Registrar Paracetamol de las 08:00'), findsNothing); // ya registrada
  });

  testWidgets('registrar "no se dio" exige motivo y queda a nombre de quien registra', (tester) async {
    final p = pid(patients.addPatient('Abuela'));
    agenda.items[p] = [FakeAgendaApi.med('m1', '20:00', '2026-10-26T23:00:00Z')];
    await openToday(tester);

    await tester.tap(find.byTooltip('Registrar Paracetamol de las 20:00'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('No se dio'));
    await tester.pumpAndSettle();
    await save(tester);
    await tester.pumpAndSettle();
    expect(find.text('Indica el motivo.'), findsOneWidget);
    expect(agenda.recorded, isEmpty);

    await tester.enterText(find.byKey(const Key('record-reason')), 'Se negó a tomarlo');
    await save(tester);
    await tester.pumpAndSettle();

    expect(agenda.recorded.single['status'], 'omitted');
    expect(agenda.recorded.single['reason'], 'Se negó a tomarlo');
    expect(agenda.recorded.single['scheduledAt'], DateTime.parse('2026-10-26T23:00:00Z'));
    expect(find.textContaining('No se dio'), findsOneWidget); // la agenda se actualizó
    expect(find.textContaining('ti'), findsWidgets);
    expect(find.text('1 de 1'), findsOneWidget);
  });

  testWidgets('"dada a tiempo" deja que el backend ponga la hora actual', (tester) async {
    final p = pid(patients.addPatient('Abuela'));
    agenda.items[p] = [FakeAgendaApi.med('m1', '20:00', '2026-10-26T23:00:00Z')];
    await openToday(tester);

    await tester.tap(find.byTooltip('Registrar Paracetamol de las 20:00'));
    await tester.pumpAndSettle();
    await save(tester);
    await tester.pumpAndSettle();

    expect(agenda.recorded.single['status'], 'given');
    expect(agenda.recorded.single['actualAt'], isNull);
  });

  testWidgets('sin permiso de administrar no aparece el botón de registrar tomas', (tester) async {
    final p = pid(patients.addPatient('Abuela', relation: 'caregiver', permissions: ['patient.view', 'care.record']));
    agenda.items[p] = [
      FakeAgendaApi.med('m1', '20:00', '2026-10-26T23:00:00Z'),
      FakeAgendaApi.task('t1', '09:00', '2026-10-26T12:00:00Z'),
    ];
    await openToday(tester);

    expect(find.byTooltip('Registrar Paracetamol de las 20:00'), findsNothing);
    expect(find.byTooltip('Registrar Hidratar de las 09:00'), findsOneWidget);
  });

  testWidgets('plan Gratis: tarea sin "no se realizó" ni cambio de posición', (tester) async {
    final p = pid(patients.addPatient('Abuela'));
    agenda.items[p] = [FakeAgendaApi.task('t1', '09:00', '2026-10-26T12:00:00Z')];
    await openToday(tester);

    expect(find.byKey(const Key('position-button')), findsNothing);
    await tester.tap(find.byTooltip('Registrar Hidratar de las 09:00'));
    await tester.pumpAndSettle();
    expect(find.text('No se realizó'), findsNothing);
    await save(tester);
    await tester.pumpAndSettle();

    expect(agenda.recorded.single, containsPair('status', 'done'));
  });

  testWidgets('plan Plus: tarea de posición exige elegir la posición', (tester) async {
    final p = pid(patients.addPatient('Abuela'));
    agenda
      ..positionChanges = true
      ..extendedCareTracking = true
      ..items[p] = [FakeAgendaApi.task('t2', '10:00', '2026-10-26T13:00:00Z', kind: 'position_change')];
    await openToday(tester);

    await tester.tap(find.byTooltip('Registrar Cambio de posición de las 10:00'));
    await tester.pumpAndSettle();
    expect(find.text('No se realizó'), findsOneWidget);
    await save(tester);
    await tester.pumpAndSettle();
    expect(find.text('Indica a qué posición se cambió.'), findsOneWidget);

    await tester.tap(find.text('De lado izquierdo'));
    await tester.pumpAndSettle();
    await save(tester);
    await tester.pumpAndSettle();

    expect(agenda.recorded.single, containsPair('position', 'left_side'));
    expect(find.textContaining('De lado izquierdo'), findsOneWidget); // el estado muestra la posición
  });

  testWidgets('plan Plus: cambio de posición suelto desde Hoy', (tester) async {
    patients.addPatient('Abuela');
    agenda.positionChanges = true;
    await openToday(tester);

    await tester.tap(find.byKey(const Key('position-button')));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Sentado/a'));
    await tester.pumpAndSettle();
    await save(tester);
    await tester.pumpAndSettle();

    expect(agenda.recorded.single, {'type': 'position', 'position': 'sitting', 'positionOther': null});
  });

  testWidgets('con varios pacientes se puede cambiar el paciente activo', (tester) async {
    final a = pid(patients.addPatient('Abuela Rosa'));
    final b = pid(patients.addPatient('Tío Pedro'));
    agenda.items[a] = [FakeAgendaApi.med('m1', '08:00', '2026-10-26T11:00:00Z')];
    agenda.items[b] = [FakeAgendaApi.task('t1', '09:00', '2026-10-26T12:00:00Z')];
    await openToday(tester);
    expect(find.text('Paracetamol'), findsOneWidget);

    await tester.tap(find.text('Abuela Rosa'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Tío Pedro').last);
    await tester.pumpAndSettle();

    expect(find.text('Hidratar'), findsOneWidget);
    expect(find.text('Paracetamol'), findsNothing);
  });

  testWidgets('se puede ver el día siguiente y volver a hoy', (tester) async {
    final p = pid(patients.addPatient('Abuela'));
    agenda.items[p] = [FakeAgendaApi.med('m1', '08:00', '2026-10-26T11:00:00Z')];
    await openToday(tester);

    await tester.tap(find.byTooltip('Día siguiente'));
    await tester.pumpAndSettle();
    expect(agenda.requests.last.day, DateTime(2026, 10, 27));
    expect(find.textContaining('martes 27 de octubre'), findsOneWidget);
    expect(find.text('No hay medicamentos ni tareas programadas para este día.'), findsOneWidget);

    await tester.tap(find.text('Volver a hoy'));
    await tester.pumpAndSettle();
    expect(find.text('Paracetamol'), findsOneWidget);
  });
}
