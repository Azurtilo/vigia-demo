import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:vigia_mobile/app.dart';
import 'package:vigia_mobile/core/config/app_config.dart';
import 'package:vigia_mobile/features/auth/data/auth_repository.dart';
import 'package:vigia_mobile/features/auth/data/profile_api.dart';
import 'package:vigia_mobile/features/patients/data/patients_api.dart';
import 'package:vigia_mobile/features/today/data/agenda_api.dart';

import '../helpers/fake_agenda_api.dart';
import '../helpers/fake_patients_api.dart';
import '../helpers/fakes.dart';

/// Flujos completos de la app con Firebase y backend falsos (sin red ni emuladores).
void main() {
  late FakeAuthRepository auth;
  late FakeProfileApi api;

  setUp(() {
    auth = FakeAuthRepository();
    api = FakeProfileApi();
  });

  Future<void> startApp(WidgetTester tester) async {
    tester.view.physicalSize = const Size(1170, 2532); // teléfono de 390×844
    tester.view.devicePixelRatio = 3;
    addTearDown(tester.view.reset);
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          appConfigProvider.overrideWithValue(
            const AppConfig(environment: AppEnvironment.local, apiBaseUrl: 'http://test', authEmulatorHost: 'x'),
          ),
          authRepositoryProvider.overrideWithValue(auth),
          profileApiProvider.overrideWithValue(api),
          patientsApiProvider.overrideWithValue(FakePatientsApi()),
          agendaApiProvider.overrideWithValue(FakeAgendaApi()),
        ],
        child: const VigiaApp(),
      ),
    );
    await tester.pumpAndSettle();
  }

  testWidgets('sin sesión se muestra el ingreso con el aviso de uso responsable', (tester) async {
    await startApp(tester);

    expect(find.text('Ingresar'), findsOneWidget);
    expect(find.textContaining('No reemplaza a profesionales de salud'), findsOneWidget);
  });

  testWidgets('el formulario de ingreso valida antes de enviar', (tester) async {
    await startApp(tester);

    await tester.tap(find.text('Ingresar'));
    await tester.pumpAndSettle();

    expect(find.text('Escribe tu correo.'), findsOneWidget);
    expect(find.text('Escribe tu contraseña.'), findsOneWidget);
  });

  testWidgets('credenciales incorrectas muestran un mensaje claro', (tester) async {
    await startApp(tester);

    await tester.enterText(find.byKey(const Key('login-email')), 'marta@example.com');
    await tester.enterText(find.byKey(const Key('login-password')), 'equivocada');
    await tester.tap(find.text('Ingresar'));
    await tester.pumpAndSettle();

    expect(find.text('Correo o contraseña incorrectos.'), findsOneWidget);
  });

  testWidgets('ingreso correcto lleva a Hoy con la barra de 5 secciones', (tester) async {
    auth.accounts['marta@example.com'] = 'clave1234';
    api.currentUid = 'uid-marta@example.com';
    api.profiles[api.currentUid!] = profileFor(api.currentUid!);
    await startApp(tester);

    await tester.enterText(find.byKey(const Key('login-email')), 'marta@example.com');
    await tester.enterText(find.byKey(const Key('login-password')), 'clave1234');
    await tester.tap(find.text('Ingresar'));
    await tester.pumpAndSettle();

    for (final label in ['Hoy', 'Pacientes', 'Alertas', 'Posturas', 'Cuenta']) {
      expect(find.text(label), findsWidgets);
    }
    expect(find.text('Aún no hay pacientes'), findsOneWidget); // Hoy sin pacientes: estado vacío honesto
  });

  testWidgets('crear cuenta lleva a completar el perfil y luego a Hoy', (tester) async {
    api.currentUid = 'uid-nueva@example.com';
    await startApp(tester);

    await tester.tap(find.text('Crear cuenta'));
    await tester.pumpAndSettle();
    await tester.enterText(find.byKey(const Key('create-email')), 'nueva@example.com');
    await tester.enterText(find.byKey(const Key('create-password')), 'clave1234');
    await tester.enterText(find.byKey(const Key('create-confirm')), 'clave1234');
    await tester.tap(find.text('Continuar'));
    await tester.pumpAndSettle();

    expect(find.text('Completa tu perfil'), findsOneWidget);
    await tester.enterText(find.byKey(const Key('profile-name')), 'Carla');
    await tester.tap(find.text('Comenzar'));
    await tester.pumpAndSettle();

    expect(find.text('Hoy'), findsWidgets);
    expect(api.profiles['uid-nueva@example.com']!.displayName, 'Carla');
  });

  testWidgets('crear cuenta exige contraseñas iguales y de 8 caracteres', (tester) async {
    await startApp(tester);
    await tester.tap(find.text('Crear cuenta'));
    await tester.pumpAndSettle();

    await tester.enterText(find.byKey(const Key('create-email')), 'nueva@example.com');
    await tester.enterText(find.byKey(const Key('create-password')), 'corta');
    await tester.enterText(find.byKey(const Key('create-confirm')), 'otra');
    await tester.tap(find.text('Continuar'));
    await tester.pumpAndSettle();

    expect(find.text('La contraseña debe tener al menos 8 caracteres.'), findsOneWidget);
    expect(find.text('Las contraseñas no coinciden.'), findsOneWidget);
    expect(auth.accounts, isEmpty);
  });

  testWidgets('recuperar contraseña no revela si el correo existe', (tester) async {
    await startApp(tester);
    await tester.tap(find.text('¿Olvidaste tu contraseña?'));
    await tester.pumpAndSettle();

    await tester.enterText(find.byKey(const Key('reset-email')), 'cualquiera@example.com');
    await tester.tap(find.text('Enviar enlace'));
    await tester.pumpAndSettle();

    expect(find.textContaining('Si existe una cuenta con ese correo'), findsOneWidget);
  });

  testWidgets('sin conexión con VIGIA se ofrece reintentar, y reintentar funciona', (tester) async {
    api.currentUid = 'u1';
    api.profiles['u1'] = profileFor('u1');
    api.nextError = offline;
    auth.current = const AuthUser(uid: 'u1', email: 'marta@example.com');
    await startApp(tester);

    expect(find.text('Sin conexión con VIGIA'), findsOneWidget);
    await tester.tap(find.byKey(const Key('retry')));
    await tester.pumpAndSettle();

    expect(find.text('Hoy'), findsWidgets);
  });

  testWidgets('cerrar sesión pide confirmación y vuelve al ingreso', (tester) async {
    api.currentUid = 'u1';
    api.profiles['u1'] = profileFor('u1');
    auth.current = const AuthUser(uid: 'u1', email: 'marta@example.com');
    await startApp(tester);

    await tester.tap(find.text('Cuenta'));
    await tester.pumpAndSettle();
    expect(find.text('Marta'), findsOneWidget);
    await tester.tap(find.widgetWithText(OutlinedButton, 'Cerrar sesión'));
    await tester.pumpAndSettle();
    await tester.tap(find.widgetWithText(TextButton, 'Cerrar sesión'));
    await tester.pumpAndSettle();

    expect(find.text('Ingresar'), findsOneWidget);
  });
}
