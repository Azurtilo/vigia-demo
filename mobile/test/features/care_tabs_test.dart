import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:vigia_mobile/app.dart';
import 'package:vigia_mobile/core/config/app_config.dart';
import 'package:vigia_mobile/core/network/api_client.dart';
import 'package:vigia_mobile/features/auth/data/auth_repository.dart';
import 'package:vigia_mobile/features/auth/data/profile_api.dart';
import 'package:vigia_mobile/features/care/data/care_api.dart';
import 'package:vigia_mobile/features/patients/data/patients_api.dart';
import 'package:vigia_mobile/features/today/data/agenda_api.dart';

import '../helpers/fake_agenda_api.dart';
import '../helpers/fake_care_api.dart';
import '../helpers/fake_patients_api.dart';
import '../helpers/fakes.dart';

/// Pestañas Medicamentos y Cuidados de la ficha.
void main() {
  late FakePatientsApi patients;
  late FakeAgendaApi agenda;
  late FakeCareApi care;

  setUp(() {
    patients = FakePatientsApi();
    agenda = FakeAgendaApi();
    care = FakeCareApi();
  });

  Future<String> openTab(WidgetTester tester, String tab, {String relation = 'owner', List<String>? permissions}) async {
    final id = patients.addPatient('Abuela Rosa', relation: relation, permissions: permissions)['id'] as String;
    tester.view.physicalSize = const Size(1170, 2532);
    tester.view.devicePixelRatio = 3;
    addTearDown(tester.view.reset);
    final auth = FakeAuthRepository()..current = const AuthUser(uid: 'me', email: 'marta@example.com');
    final profiles = FakeProfileApi()
      ..currentUid = 'me'
      ..profiles['me'] = profileFor('me');
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
          careApiProvider.overrideWithValue(care),
        ],
        child: const VigiaApp(),
      ),
    );
    await tester.pumpAndSettle();
    await tester.tap(find.text('Pacientes').last);
    await tester.pumpAndSettle();
    await tester.tap(find.text('Abuela Rosa'));
    await tester.pumpAndSettle();
    await tester.tap(find.text(tab));
    await tester.pumpAndSettle();
    return id;
  }

  // Flutter solo construye lo que está cerca de la vista: se desplaza la lista del formulario.
  Future<void> scrollToAndTap(WidgetTester tester, Finder target) async {
    await tester.scrollUntilVisible(
      target,
      300,
      scrollable: find.descendant(of: find.byType(Form), matching: find.byType(Scrollable)).first,
    );
    await tester.pumpAndSettle();
    await tester.tap(target);
    await tester.pumpAndSettle();
  }

  /// Agrega la hora que propone el selector (08:00) aceptándolo tal cual.
  Future<void> addDefaultTime(WidgetTester tester) async {
    await tester.tap(find.byKey(const Key('add-time')));
    await tester.pumpAndSettle();
    // El último botón del diálogo es "confirmar", sin depender de cómo esté traducido.
    await tester.tap(find.descendant(of: find.byType(Dialog), matching: find.byType(TextButton)).last);
    await tester.pumpAndSettle();
  }

  testWidgets('agregar un medicamento con horario lo muestra tal como fue indicado', (tester) async {
    await openTab(tester, 'Medicamentos');
    expect(find.text('No hay medicamentos registrados.'), findsOneWidget);

    await tester.tap(find.byKey(const Key('add-medication')));
    await tester.pumpAndSettle();
    expect(find.textContaining('VIGIA no sugiere ni calcula dosis'), findsOneWidget);
    await tester.enterText(find.byKey(const Key('med-name')), 'Paracetamol');
    await tester.enterText(find.byKey(const Key('med-dose')), '1 comprimido de 500 mg');
    await addDefaultTime(tester);
    await addDefaultTime(tester); // repetida: se ignora
    await scrollToAndTap(tester, find.byKey(const Key('med-save')));

    final sent = care.sent.single;
    expect(sent['op'], 'createMedication');
    expect(sent['dose'], '1 comprimido de 500 mg');
    expect(sent['schedule'], {'times': ['08:00'], 'daysOfWeek': <int>[]});
    expect(find.text('Paracetamol'), findsOneWidget);
    expect(find.text('08:00 · todos los días'), findsOneWidget);
  });

  testWidgets('horario fijo sin horas no se guarda', (tester) async {
    await openTab(tester, 'Medicamentos');
    await tester.tap(find.byKey(const Key('add-medication')));
    await tester.pumpAndSettle();
    await tester.enterText(find.byKey(const Key('med-name')), 'Paracetamol');
    await tester.enterText(find.byKey(const Key('med-dose')), '1 comprimido');

    await scrollToAndTap(tester, find.byKey(const Key('med-save')));

    expect(care.sent, isEmpty);
    expect(find.text('Agrega al menos una hora.'), findsOneWidget);
  });

  testWidgets('medicamento "si es necesario" se registra con confirmación', (tester) async {
    care.meds['p1'] = [
      {'id': 'm9', 'name': 'Ibuprofeno', 'dose': '1 comprimido', 'instructions': null, 'scheduleType': 'as_needed',
       'schedule': null, 'startDate': '2026-10-01', 'endDate': null, 'active': true},
    ];
    await openTab(tester, 'Medicamentos');

    expect(find.text('Si es necesario'), findsOneWidget);
    await tester.tap(find.text('Registrar toma'));
    await tester.pumpAndSettle();
    expect(find.textContaining('¿Registrar que se dio Ibuprofeno'), findsOneWidget);
    await tester.tap(find.widgetWithText(TextButton, 'Registrar'));
    await tester.pumpAndSettle();

    expect(care.sent.single, {'op': 'asNeededDose', 'medicationId': 'm9'});
  });

  testWidgets('desactivar pide confirmación y explica que los registros se conservan', (tester) async {
    care.meds['p1'] = [
      {'id': 'm1', 'name': 'Paracetamol', 'dose': '1 comprimido', 'instructions': null, 'scheduleType': 'fixed',
       'schedule': {'times': ['08:00'], 'daysOfWeek': []}, 'startDate': '2026-10-01', 'endDate': null, 'active': true},
    ];
    await openTab(tester, 'Medicamentos');

    await tester.tap(find.byTooltip('Opciones de Paracetamol'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Desactivar'));
    await tester.pumpAndSettle();
    expect(find.textContaining('Las tomas ya registradas se conservan'), findsOneWidget);
    await tester.tap(find.widgetWithText(TextButton, 'Desactivar'));
    await tester.pumpAndSettle();

    expect(care.sent.single, {'op': 'updateMedication', 'id': 'm1', 'active': false});
    expect(find.text('Inactivo'), findsOneWidget);
  });

  testWidgets('una cuidadora ve los medicamentos pero no puede agregarlos ni editarlos', (tester) async {
    care.meds['p1'] = [
      {'id': 'm1', 'name': 'Paracetamol', 'dose': '1 comprimido', 'instructions': null, 'scheduleType': 'fixed',
       'schedule': {'times': ['08:00'], 'daysOfWeek': [1, 3, 5]}, 'startDate': '2026-10-01', 'endDate': null, 'active': true},
    ];
    await openTab(tester, 'Medicamentos', relation: 'caregiver', permissions: ['patient.view', 'meds.administer', 'care.record']);

    expect(find.text('Paracetamol'), findsOneWidget);
    expect(find.text('08:00 · lun, mié, vie'), findsOneWidget);
    expect(find.byKey(const Key('add-medication')), findsNothing);
    expect(find.byTooltip('Opciones de Paracetamol'), findsNothing);
  });

  testWidgets('crear una tarea sin horario y registrarla desde Cuidados', (tester) async {
    await openTab(tester, 'Cuidados');

    await tester.tap(find.byKey(const Key('add-task')));
    await tester.pumpAndSettle();
    expect(find.text('Cambio de posición'), findsNothing); // plan Gratis: sin tareas de posición
    expect(find.text('Responsable asignado (opcional)'), findsNothing); // plan Gratis: sin asignar responsable
    await tester.enterText(find.byKey(const Key('task-title')), 'Cambio de sábanas');
    await tester.tap(find.text('Sin horario'));
    await tester.pumpAndSettle();
    await scrollToAndTap(tester, find.byKey(const Key('task-save')));

    expect(care.sent.single['scheduleType'], 'unscheduled');
    expect(care.sent.single['schedule'], isNull);
    expect(find.text('Sin horario fijo'), findsOneWidget);

    await tester.tap(find.widgetWithText(OutlinedButton, 'Registrar'));
    await tester.pumpAndSettle();
    expect(find.text('No se realizó'), findsNothing); // sin horario: solo "realizada"
    await tester.ensureVisible(find.byKey(const Key('record-save')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('record-save')));
    await tester.pumpAndSettle();

    expect(agenda.recorded.single, containsPair('status', 'done'));
  });

  testWidgets('con plan Plus se pueden crear tareas de cambio de posición', (tester) async {
    agenda
      ..positionChanges = true
      ..extendedCareTracking = true;
    care.positionChangesAllowed = true;
    await openTab(tester, 'Cuidados');

    await tester.tap(find.byKey(const Key('add-task')));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Cambio de posición'));
    await tester.pumpAndSettle();
    await addDefaultTime(tester);
    await scrollToAndTap(tester, find.byKey(const Key('task-save')));

    expect(care.sent.single['kind'], 'position_change');
    expect(care.sent.single['title'], 'Cambio de posición'); // nombre sugerido editable
  });
}
