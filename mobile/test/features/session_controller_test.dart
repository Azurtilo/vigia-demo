import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:vigia_mobile/core/network/api_exception.dart';
import 'package:vigia_mobile/features/auth/application/session_controller.dart';
import 'package:vigia_mobile/features/auth/data/auth_repository.dart';
import 'package:vigia_mobile/features/auth/data/profile_api.dart';

import '../helpers/fakes.dart';

void main() {
  late FakeAuthRepository auth;
  late FakeProfileApi api;
  late ProviderContainer container;

  setUp(() {
    auth = FakeAuthRepository();
    api = FakeProfileApi();
    container = ProviderContainer(
      overrides: [
        authRepositoryProvider.overrideWithValue(auth),
        profileApiProvider.overrideWithValue(api),
      ],
    );
    addTearDown(container.dispose);
    container.listen(sessionControllerProvider, (_, _) {}); // mantiene vivo el controlador
  });

  Future<SessionState> settle() async {
    await pumpEventQueue();
    return container.read(sessionControllerProvider);
  }

  void signInAs(String uid) {
    api.currentUid = uid;
    auth.emit(AuthUser(uid: uid, email: 'marta@example.com'));
  }

  test('sin cuenta: SignedOut', () async {
    expect(await settle(), isA<SignedOut>());
  });

  test('con cuenta y perfil: SessionReady', () async {
    api.profiles['u1'] = profileFor('u1');
    signInAs('u1');

    final state = await settle();

    expect(state, isA<SessionReady>());
    expect((state as SessionReady).profile.displayName, 'Marta');
  });

  test('con cuenta sin perfil: NeedsProfile, y al completarlo queda lista', () async {
    signInAs('u1');
    expect(await settle(), isA<NeedsProfile>());

    final error = await container.read(sessionControllerProvider.notifier).completeProfile('  Marta  ');

    expect(error, isNull);
    final state = await settle();
    expect(state, isA<SessionReady>());
    expect((state as SessionReady).profile.displayName, 'Marta');
  });

  test('cuenta suspendida: SessionBlocked con el mensaje del backend', () async {
    api.nextError = const ApiException(
      kind: ApiErrorKind.api, statusCode: 403, code: 'account_suspended', message: 'Tu cuenta está suspendida.',
    );
    signInAs('u1');

    final state = await settle();

    expect(state, isA<SessionBlocked>());
    expect((state as SessionBlocked).message, 'Tu cuenta está suspendida.');
  });

  test('sin conexión: SessionUnavailable, y Reintentar recupera la sesión', () async {
    api.profiles['u1'] = profileFor('u1');
    api.nextError = offline;
    signInAs('u1');
    expect(await settle(), isA<SessionUnavailable>());

    await container.read(sessionControllerProvider.notifier).retry();

    expect(await settle(), isA<SessionReady>());
  });

  test('token rechazado por el backend: se cierra la sesión', () async {
    api.nextError = const ApiException(kind: ApiErrorKind.api, statusCode: 401, code: 'auth_revoked', message: 'x');
    signInAs('u1');

    expect(await settle(), isA<SignedOut>());
    expect(auth.signOutCalls, 1);
  });

  test('cerrar sesión vuelve a SignedOut', () async {
    api.profiles['u1'] = profileFor('u1');
    signInAs('u1');
    await settle();

    await container.read(sessionControllerProvider.notifier).signOut();

    expect(await settle(), isA<SignedOut>());
  });

  test('error de red al completar el perfil se muestra, sin cambiar de pantalla', () async {
    signInAs('u1');
    await settle();
    final failingApi = _FailingRegisterApi();
    final c2 = ProviderContainer(overrides: [
      authRepositoryProvider.overrideWithValue(auth),
      profileApiProvider.overrideWithValue(failingApi),
    ]);
    addTearDown(c2.dispose);
    c2.listen(sessionControllerProvider, (_, _) {});
    await pumpEventQueue();

    final error = await c2.read(sessionControllerProvider.notifier).completeProfile('Marta');

    expect(error, contains('conexión'));
    expect(c2.read(sessionControllerProvider), isA<NeedsProfile>());
  });
}

class _FailingRegisterApi extends FakeProfileApi {
  _FailingRegisterApi() {
    currentUid = 'u1';
  }

  @override
  Future<Never> register(String displayName) async => throw offline;
}
