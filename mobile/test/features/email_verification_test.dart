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

/// Verificación de correo para unirse a un paciente (T-019-18, QA-2026-10-28-01).
/// En producción el backend exige el correo verificado; la app debe permitir verificarlo.
void main() {
  late FakeAuthRepository auth;
  late FakeProfileApi profiles;
  late FakePatientsApi patients;

  setUp(() {
    auth = FakeAuthRepository();
    profiles = FakeProfileApi();
    patients = FakePatientsApi()..tokenEmailVerified = () => auth.tokenEmailVerified;
    patients.invitations['59XBSV6SB7RCV4K4PU6N'] = {
      'id': 'shared', 'ownerUid': 'marta', 'displayName': 'Mamá de Marta', 'timeZone': 'America/Santiago',
      'status': 'active', 'allergies': <String>[], 'emergencyContacts': <Map<String, dynamic>>[],
      'myRelation': 'caregiver', 'myPermissions': ['patient.view'],
    };
  });

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
        ],
        child: const VigiaApp(),
      ),
    );
    await tester.pumpAndSettle();
  }

  Future<void> tryToJoin(WidgetTester tester) async {
    auth.current = const AuthUser(uid: 'me', email: 'carla@example.com');
    profiles
      ..currentUid = 'me'
      ..profiles['me'] = profileFor('me');
    await startApp(tester);
    await tester.tap(find.text('Pacientes').last);
    await tester.pumpAndSettle();
    await tester.tap(find.text('Unirme con código'));
    await tester.pumpAndSettle();
    await tester.enterText(find.byKey(const Key('join-code')), '59xb-sv6s-b7rc-v4k4-pu6n');
    await tester.tap(find.text('Unirme'));
    await tester.pumpAndSettle();
  }

  // La tarjeta queda bajo el campo del código: se hace visible antes de tocar.
  Future<void> tapVisible(WidgetTester tester, String text) async {
    await tester.ensureVisible(find.text(text));
    await tester.pumpAndSettle();
    await tester.tap(find.text(text));
    await tester.pumpAndSettle();
  }

  testWidgets('crear la cuenta envía el correo de verificación', (tester) async {
    profiles.currentUid = 'uid-nueva@example.com';
    await startApp(tester);

    await tester.tap(find.text('Crear cuenta'));
    await tester.pumpAndSettle();
    await tester.enterText(find.byKey(const Key('create-email')), 'nueva@example.com');
    await tester.enterText(find.byKey(const Key('create-password')), 'clave1234');
    await tester.enterText(find.byKey(const Key('create-confirm')), 'clave1234');
    await tester.tap(find.text('Continuar'));
    await tester.pumpAndSettle();

    expect(auth.verificationEmails, 1);
    expect(find.text('Completa tu perfil'), findsOneWidget);
  });

  testWidgets('si el envío falla, crear la cuenta sigue adelante', (tester) async {
    auth = _FailingVerification();
    profiles.currentUid = 'uid-nueva@example.com';
    await startApp(tester);
    await tester.tap(find.text('Crear cuenta'));
    await tester.pumpAndSettle();
    await tester.enterText(find.byKey(const Key('create-email')), 'nueva@example.com');
    await tester.enterText(find.byKey(const Key('create-password')), 'clave1234');
    await tester.enterText(find.byKey(const Key('create-confirm')), 'clave1234');
    await tester.tap(find.text('Continuar'));
    await tester.pumpAndSettle();

    expect(find.text('Completa tu perfil'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('sin correo verificado se pide verificarlo en vez de mostrar un error', (tester) async {
    await tryToJoin(tester);

    expect(find.text('Verifica tu correo'), findsOneWidget);
    expect(find.text('Ya lo verifiqué'), findsOneWidget);
    expect(find.text('Reenviar correo'), findsOneWidget);
    expect(find.text('Unirme'), findsNothing);
  });

  testWidgets('reenviar manda otro correo', (tester) async {
    await tryToJoin(tester);

    await tapVisible(tester, 'Reenviar correo');

    expect(auth.verificationEmails, 1);
    expect(find.text('Te enviamos otro correo de verificación.'), findsOneWidget);
  });

  testWidgets('«Ya lo verifiqué» sin haber abierto el enlace no une al paciente', (tester) async {
    await tryToJoin(tester);

    await tapVisible(tester, 'Ya lo verifiqué');

    expect(auth.refreshCalls, 1);
    expect(find.textContaining('aún no aparece verificado'), findsOneWidget);
    expect(find.text('Mamá de Marta'), findsNothing);
  });

  testWidgets('tras abrir el enlace, «Ya lo verifiqué» renueva el token y une al paciente', (tester) async {
    await tryToJoin(tester);
    auth.emailVerified = true; // la persona abrió el enlace; su token sigue siendo el antiguo

    await tapVisible(tester, 'Ya lo verifiqué');

    expect(auth.tokenEmailVerified, isTrue);
    expect(find.text('Mamá de Marta'), findsWidgets);
    expect(find.text('Eres cuidador/a'), findsOneWidget);
  });
}

/// Repositorio falso cuyo envío del correo de verificación falla (p. ej. sin conexión).
class _FailingVerification extends FakeAuthRepository {
  @override
  Future<void> sendEmailVerification() async =>
      throw const AuthFailure('Sin conexión. Revisa tu internet e inténtalo de nuevo.', isConnectivity: true);
}
