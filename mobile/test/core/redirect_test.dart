import 'package:flutter_test/flutter_test.dart';
import 'package:vigia_mobile/core/network/api_exception.dart';
import 'package:vigia_mobile/core/router/app_router.dart';
import 'package:vigia_mobile/features/auth/application/session_controller.dart';

import '../helpers/fakes.dart';

void main() {
  final ready = SessionReady(profileFor('u1'));

  test('sin sesión solo se permiten las pantallas públicas', () {
    expect(redirectFor(const SignedOut(), Routes.today), Routes.login);
    expect(redirectFor(const SignedOut(), Routes.account), Routes.login);
    expect(redirectFor(const SignedOut(), Routes.login), isNull);
    expect(redirectFor(const SignedOut(), Routes.createAccount), isNull);
    expect(redirectFor(const SignedOut(), Routes.forgotPassword), isNull);
  });

  test('con sesión lista no se vuelve a las pantallas de ingreso', () {
    expect(redirectFor(ready, Routes.login), Routes.today);
    expect(redirectFor(ready, Routes.loading), Routes.today);
    expect(redirectFor(ready, Routes.completeProfile), Routes.today);
    expect(redirectFor(ready, Routes.account), isNull);
  });

  test('sin perfil VIGIA se completa el perfil antes de entrar', () {
    expect(redirectFor(const NeedsProfile('a@b.cl'), Routes.today), Routes.completeProfile);
    expect(redirectFor(const NeedsProfile('a@b.cl'), Routes.completeProfile), isNull);
  });

  test('cargando, sin conexión o bloqueada tienen su propia pantalla', () {
    expect(redirectFor(const SessionLoading(), Routes.today), Routes.loading);
    expect(redirectFor(const SessionUnavailable(ApiException.offline), Routes.today), Routes.problem);
    expect(redirectFor(const SessionBlocked('Suspendida'), Routes.account), Routes.problem);
  });
}
