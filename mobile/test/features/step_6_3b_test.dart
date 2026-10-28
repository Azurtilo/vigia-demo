import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:vigia_mobile/app.dart';
import 'package:vigia_mobile/core/config/app_config.dart';
import 'package:vigia_mobile/core/network/api_client.dart';
import 'package:vigia_mobile/features/account/subscription.dart';
import 'package:vigia_mobile/features/auth/data/auth_repository.dart';
import 'package:vigia_mobile/features/auth/data/profile_api.dart';
import 'package:vigia_mobile/features/care/data/care_api.dart';
import 'package:vigia_mobile/features/history/history.dart';
import 'package:vigia_mobile/features/members/members.dart';
import 'package:vigia_mobile/features/patients/data/patients_api.dart';
import 'package:vigia_mobile/features/today/data/agenda_api.dart';

import '../helpers/fake_account_apis.dart';
import '../helpers/fake_agenda_api.dart';
import '../helpers/fake_care_api.dart';
import '../helpers/fake_patients_api.dart';
import '../helpers/fakes.dart';

/// Historial, personas, plan y correcciones.
void main() {
  late FakePatientsApi patients;
  late FakeAgendaApi agenda;
  late FakeHistoryApi history;
  late FakeMembersApi members;
  late FakeSubscriptionApi subscription;

  setUp(() {
    patients = FakePatientsApi();
    agenda = FakeAgendaApi();
    history = FakeHistoryApi();
    members = FakeMembersApi();
    subscription = FakeSubscriptionApi();
  });

  Future<void> start(WidgetTester tester) async {
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
          careApiProvider.overrideWithValue(FakeCareApi()),
          historyApiProvider.overrideWithValue(history),
          membersApiProvider.overrideWithValue(members),
          subscriptionApiProvider.overrideWithValue(subscription),
        ],
        child: const VigiaApp(),
      ),
    );
    await tester.pumpAndSettle();
  }

  Future<void> openPatient(WidgetTester tester, String name) async {
    await tester.tap(find.text('Pacientes').last);
    await tester.pumpAndSettle();
    await tester.tap(find.text(name));
    await tester.pumpAndSettle();
  }

  Future<void> tapInSheet(WidgetTester tester, Finder target) async {
    await tester.ensureVisible(target);
    await tester.pumpAndSettle();
    await tester.tap(target);
    await tester.pumpAndSettle();
  }

  // ---------- Historial ----------

  testWidgets('historial: textos legibles, filtros y paginación', (tester) async {
    patients.addPatient('Abuela Rosa');
    history.entries = [
      FakeHistoryApi.entry('1', 'medication.delayed', 'medication', {'name': 'Paracetamol', 'dose': '1 comprimido', 'reason': 'Dormía'}),
      FakeHistoryApi.entry('2', 'task.done', 'task', {'title': 'Hidratar'}, actor: 'me', name: 'Marta'),
      FakeHistoryApi.entry('3', 'position.changed', 'position', {'position': 'left_side'}),
    ];
    await start(tester);
    await openPatient(tester, 'Abuela Rosa');

    await tester.tap(find.text('Historial'));
    await tester.pumpAndSettle();
    expect(find.text('Dio con retraso Paracetamol (1 comprimido)'), findsOneWidget);
    expect(find.text('Motivo: Dormía'), findsOneWidget);
    expect(find.textContaining('· Tú'), findsOneWidget); // registro propio
    expect(find.text('Cambio de posición: De lado izquierdo'), findsNothing); // 3.ª entrada: página siguiente

    await tester.tap(find.text('Ver registros anteriores'));
    await tester.pumpAndSettle();
    expect(find.text('Cambio de posición: De lado izquierdo'), findsOneWidget);

    await tester.tap(find.text('Tareas'));
    await tester.pumpAndSettle();
    expect(history.categoriesRequested.last, 'task');
    expect(find.text('Realizó «Hidratar»'), findsOneWidget);
    expect(find.textContaining('Paracetamol'), findsNothing);
  });

  testWidgets('historial: avisa cuando el plan oculta registros antiguos', (tester) async {
    patients.addPatient('Abuela Rosa');
    history
      ..hiddenOlder = true
      ..entries = [FakeHistoryApi.entry('1', 'task.done', 'task', {'title': 'Hidratar'})];
    await start(tester);
    await openPatient(tester, 'Abuela Rosa');
    await tester.tap(find.text('Historial'));
    await tester.pumpAndSettle();

    expect(find.textContaining('Los registros anteriores se conservan'), findsOneWidget);
  });

  testWidgets('sin permiso de historial, el acceso aparece desactivado con el motivo', (tester) async {
    patients.addPatient('Abuela Rosa', relation: 'caregiver', permissions: ['patient.view']);
    await start(tester);
    await openPatient(tester, 'Abuela Rosa');

    expect(find.text('No tienes permiso para ver el historial'), findsOneWidget);
  });

  // ---------- Personas ----------

  testWidgets('la responsable invita y ve el código una sola vez, con opción de copiar', (tester) async {
    final id = patients.addPatient('Abuela Rosa')['id'] as String;
    members.memberStore[id] = [
      {'uid': 'me', 'displayName': 'Marta', 'relation': 'owner', 'permissions': ['patient.view']},
    ];
    await start(tester);
    await openPatient(tester, 'Abuela Rosa');
    await tester.tap(find.text('Personas con acceso'));
    await tester.pumpAndSettle();
    expect(find.text('Marta (tú)'), findsOneWidget);

    await tester.tap(find.byKey(const Key('invite')));
    await tester.pumpAndSettle();
    await tester.enterText(find.byKey(const Key('invite-email')), 'carla@example.com');
    await tapInSheet(tester, find.text('Crear invitación'));

    expect(members.calls.single, {'op': 'invite', 'email': 'carla@example.com', 'relation': 'caregiver'});
    expect(find.text('59XB-SV6S-B7RC-V4K4-PU6N'), findsOneWidget);
    expect(find.text('Copiar'), findsOneWidget);
    await tester.tap(find.text('Listo'));
    await tester.pumpAndSettle();
    expect(find.text('carla@example.com'), findsOneWidget); // en la lista de invitaciones
    expect(find.textContaining('Pendiente'), findsOneWidget);
  });

  testWidgets('cambiar permisos: "Ver la ficha" no se puede quitar', (tester) async {
    final id = patients.addPatient('Abuela Rosa')['id'] as String;
    members.memberStore[id] = [
      {'uid': 'me', 'displayName': 'Marta', 'relation': 'owner', 'permissions': ['patient.view']},
      {'uid': 'carla', 'displayName': 'Carla', 'relation': 'caregiver', 'permissions': ['patient.view', 'meds.administer']},
    ];
    await start(tester);
    await openPatient(tester, 'Abuela Rosa');
    await tester.tap(find.text('Personas con acceso'));
    await tester.pumpAndSettle();

    await tester.tap(find.byTooltip('Opciones de Carla'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Cambiar permisos'));
    await tester.pumpAndSettle();
    final viewTile = tester.widget<CheckboxListTile>(find.widgetWithText(CheckboxListTile, 'Ver la ficha'));
    expect(viewTile.onChanged, isNull);
    await tester.tap(find.text('Editar la ficha'));
    await tester.pumpAndSettle();
    await tapInSheet(tester, find.text('Guardar permisos'));

    expect(members.calls.single['permissions'], ['meds.administer', 'patient.edit', 'patient.view']);
  });

  testWidgets('una cuidadora puede retirarse, pero no ve opciones sobre otras personas', (tester) async {
    final id = patients.addPatient('Mamá de Marta', relation: 'caregiver', permissions: ['patient.view'])['id'] as String;
    members.memberStore[id] = [
      {'uid': 'marta', 'displayName': 'Marta', 'relation': 'owner', 'permissions': ['patient.view']},
      {'uid': 'me', 'displayName': 'Carla', 'relation': 'caregiver', 'permissions': ['patient.view']},
    ];
    await start(tester);
    await openPatient(tester, 'Mamá de Marta');
    await tester.tap(find.text('Personas con acceso'));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('invite')), findsNothing);
    expect(find.byTooltip('Opciones de Marta'), findsNothing);
    await tester.tap(find.byTooltip('Opciones de Carla'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Dejar de cuidar a este paciente'));
    await tester.pumpAndSettle();
    await tester.tap(find.widgetWithText(TextButton, 'Dejar de cuidar'));
    await tester.pumpAndSettle();

    expect(members.calls.single, {'op': 'remove', 'uid': 'me'});
    expect(find.text('Pacientes'), findsWidgets); // vuelve a la lista
  });

  // ---------- Plan ----------

  testWidgets('plan: muestra uso, simula y cambia (simulado)', (tester) async {
    await start(tester);
    await tester.tap(find.text('Cuenta').last);
    await tester.pumpAndSettle();
    await tester.tap(find.text('Plan y límites'));
    await tester.pumpAndSettle();

    expect(find.textContaining('no se realiza ningún cobro'), findsOneWidget);
    expect(find.text('Pacientes activos: 1 de 1'), findsOneWidget);
    await tapInSheet(tester, find.byKey(const Key('simulate-premium')));
    expect(find.text('Puedes cambiarte a este plan sin restricciones.'), findsOneWidget);
    await tapInSheet(tester, find.byKey(const Key('confirm-change')));

    expect(subscription.planId, 'premium');
    expect(find.text('Premium'), findsOneWidget); // tarjeta del plan actual
  });

  testWidgets('plan: bajar quedando sobre el límite exige marcar la confirmación', (tester) async {
    subscription
      ..planId = 'plus'
      ..activePatients = 3;
    await start(tester);
    await tester.tap(find.text('Cuenta').last);
    await tester.pumpAndSettle();
    await tester.tap(find.text('Plan y límites'));
    await tester.pumpAndSettle();

    await tapInSheet(tester, find.byKey(const Key('simulate-free')));
    final button = find.byKey(const Key('confirm-change'));
    await tester.ensureVisible(button);
    expect(tester.widget<FilledButton>(button).onPressed, isNull); // falta confirmar
    await tapInSheet(tester, find.byKey(const Key('understood')));
    await tapInSheet(tester, button);

    expect(subscription.planId, 'free');
    expect(subscription.changes.first['confirm'], isTrue);
  });

  // ---------- Correcciones ----------

  testWidgets('la responsable corrige un registro y queda marcado como corregido', (tester) async {
    final p = patients.addPatient('Abuela Rosa')['id'] as String;
    agenda.items[p] = [
      FakeAgendaApi.med('m1', '08:00', '2026-10-26T11:00:00Z', status: 'given', log: {
        'id': 'log1', 'recordedBy': 'carla', 'actualAt': '2026-10-26T11:05:00Z', 'reason': null,
      }),
    ];
    await start(tester);

    await tester.tap(find.text('Corregir'));
    await tester.pumpAndSettle();
    expect(find.text('Corregir: Paracetamol · 08:00'), findsOneWidget);
    await tester.tap(find.text('No se dio'));
    await tester.pumpAndSettle();
    await tester.enterText(find.byKey(const Key('record-reason')), 'Me equivoqué de toma');
    await tapInSheet(tester, find.byKey(const Key('record-save')));

    expect(agenda.recorded.single, containsPair('type', 'correctDose'));
    expect(agenda.recorded.single, containsPair('logId', 'log1'));
    expect(find.text('Corregido'), findsOneWidget);
  });

  testWidgets('una cuidadora no puede corregir registros de otra persona', (tester) async {
    final p = patients.addPatient('Abuela Rosa', relation: 'caregiver', permissions: ['patient.view', 'meds.administer'])['id'] as String;
    agenda.items[p] = [
      FakeAgendaApi.med('m1', '08:00', '2026-10-26T11:00:00Z', status: 'given', log: {
        'id': 'log1', 'recordedBy': 'otra', 'actualAt': '2026-10-26T11:05:00Z', 'reason': null,
      }),
      FakeAgendaApi.med('m1', '20:00', '2026-10-26T23:00:00Z', status: 'given', log: {
        'id': 'log2', 'recordedBy': 'me', 'actualAt': '2026-10-26T23:05:00Z', 'reason': null,
      }),
    ];
    await start(tester);

    expect(find.text('Corregir'), findsOneWidget); // solo su propio registro (20:00)
  });
}
