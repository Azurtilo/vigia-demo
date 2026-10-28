import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:vigia_mobile/app.dart';
import 'package:vigia_mobile/core/config/app_config.dart';
import 'package:vigia_mobile/core/network/api_client.dart';
import 'package:vigia_mobile/features/alerts/alerts.dart';
import 'package:vigia_mobile/features/alerts/alerts_screen.dart';
import 'package:vigia_mobile/features/auth/data/auth_repository.dart';
import 'package:vigia_mobile/features/auth/data/profile_api.dart';
import 'package:vigia_mobile/features/patients/data/patients_api.dart';

import '../helpers/fake_alerts_api.dart';
import '../helpers/fake_patients_api.dart';
import '../helpers/fakes.dart';

/// Barra de 5 secciones y bandeja de alertas (T-019-09, RF-019-13 y RF-019-14).
void main() {
  late FakeAuthRepository auth;
  late FakeProfileApi profiles;
  late FakeAlertsApi alerts;

  setUp(() {
    auth = FakeAuthRepository()..current = const AuthUser(uid: 'me', email: 'marta@example.com');
    profiles = FakeProfileApi()
      ..currentUid = 'me'
      ..profiles['me'] = profileFor('me');
    alerts = FakeAlertsApi();
  });

  Future<void> startApp(WidgetTester tester, {Size dp = const Size(390, 844)}) async {
    tester.view.physicalSize = dp * 3;
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
          patientsApiProvider.overrideWithValue(FakePatientsApi()),
          alertsApiProvider.overrideWithValue(alerts),
        ],
        child: const VigiaApp(),
      ),
    );
    await tester.pumpAndSettle();
  }

  Future<void> openAlerts(WidgetTester tester) async {
    await startApp(tester);
    await tester.tap(find.text('Alertas').last);
    await tester.pumpAndSettle();
  }

  testWidgets('las 5 etiquetas de la barra caben completas en un teléfono de 360 dp', (tester) async {
    await startApp(tester, dp: const Size(360, 740));

    const labels = ['Hoy', 'Pacientes', 'Alertas', 'Posturas', 'Cuenta'];
    for (final label in labels) {
      final text = find.descendant(of: find.byType(NavigationBar), matching: find.text(label));
      expect(text, findsOneWidget);
      expect(tester.getSize(text).width, lessThanOrEqualTo(360 / labels.length), reason: label);
    }
    expect(tester.takeException(), isNull); // sin desbordes
  });

  testWidgets('Posturas abre su sección y conserva la barra', (tester) async {
    await startApp(tester);

    await tester.tap(find.text('Posturas'));
    await tester.pumpAndSettle();

    expect(find.textContaining('Esta sección se construye'), findsOneWidget);
    expect(find.byType(NavigationBar), findsOneWidget);
  });

  testWidgets('sin alertas se explica qué aparecerá', (tester) async {
    await openAlerts(tester);

    expect(find.text('Sin alertas'), findsOneWidget);
  });

  testWidgets('una caída abierta se muestra con el paciente y se marca como atendida', (tester) async {
    alerts.add('a1', 'fall');
    await openAlerts(tester);

    expect(find.text('Posible caída'), findsOneWidget);
    expect(find.text('Abuela Rosa'), findsOneWidget);
    expect(find.text('Revisa al paciente ahora.'), findsOneWidget);

    await tester.tap(find.text('Marcar como atendida'));
    await tester.pumpAndSettle();

    expect(alerts.attended, ['a1']);
    expect(find.text('Marcar como atendida'), findsNothing);
    expect(find.textContaining('Atendida'), findsOneWidget);
  });

  testWidgets('los avisos de cámara se distinguen de los riesgos', (tester) async {
    alerts
      ..add('a1', 'camera_blind', monitorState: 'sin_imagen')
      ..add('a2', 'node_offline')
      ..add('a3', 'immobility', status: 'attended');
    await openAlerts(tester);

    expect(find.text('La cámara no recibe imagen'), findsOneWidget);
    expect(find.text('El nodo de detección no responde'), findsOneWidget);
    expect(find.text('Inmovilidad prolongada'), findsOneWidget);
    expect(find.text('Marcar como atendida'), findsNWidgets(2)); // la atendida no tiene botón
  });

  testWidgets('si otra persona ya la atendió se informa y la lista se actualiza', (tester) async {
    final alert = alerts.add('a1', 'fall');
    await openAlerts(tester);
    alert['status'] = 'attended'; // la atendió otra persona mientras tanto
    final before = alerts.mineCalls;

    await tester.tap(find.text('Marcar como atendida'));
    await tester.pumpAndSettle();

    expect(find.text('La alerta ya fue atendida.'), findsOneWidget);
    expect(alerts.mineCalls, greaterThan(before));
    expect(find.text('Marcar como atendida'), findsNothing);
  });

  testWidgets('volver la app al primer plano recarga las alertas', (tester) async {
    await openAlerts(tester);
    final before = alerts.mineCalls;
    alerts.add('a1', 'fall');

    // La secuencia real de Android al ir y volver: resumed → inactive → hidden → paused y de vuelta.
    for (final state in [
      AppLifecycleState.inactive,
      AppLifecycleState.hidden,
      AppLifecycleState.paused,
      AppLifecycleState.hidden,
      AppLifecycleState.inactive,
      AppLifecycleState.resumed,
    ]) {
      tester.binding.handleAppLifecycleStateChanged(state);
    }
    await tester.pumpAndSettle();

    expect(alerts.mineCalls, greaterThan(before));
    expect(find.text('Posible caída'), findsOneWidget);
  });

  test('la hora de la alerta se muestra como hoy, ayer o la fecha', () {
    final now = DateTime(2026, 10, 28, 20, 0);
    expect(alertTime(DateTime(2026, 10, 28, 19, 58), now: now), 'hoy 19:58');
    expect(alertTime(DateTime(2026, 10, 27, 8, 5), now: now), 'ayer 08:05');
    expect(alertTime(DateTime(2026, 10, 20, 8, 5), now: now), '20-10-2026 08:05');
  });

  test('cada tipo de alerta tiene su texto', () {
    AlertItem item(String kind, [String? state]) => AlertItem.fromJson({
          'id': 'x', 'patientId': 'p', 'kind': kind, 'monitorState': state,
          'occurredAt': '2026-10-28T22:00:00Z', 'status': 'open',
        });
    expect(item('fall').isRisk, isTrue);
    expect(item('camera_blind', 'persona_no_visible').title, 'La cámara no ve a la persona');
    expect(item('camera_blind').isRisk, isFalse);
  });
}
