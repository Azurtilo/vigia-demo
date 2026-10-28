import 'dart:async';

import 'package:vigia_mobile/core/network/api_exception.dart';
import 'package:vigia_mobile/features/auth/data/auth_repository.dart';
import 'package:vigia_mobile/features/auth/data/profile_api.dart';
import 'package:vigia_mobile/features/auth/domain/user_profile.dart';

/// Firebase Auth falso: la prueba decide qué pasa al iniciar sesión o crear cuenta.
class FakeAuthRepository implements AuthRepository {
  final _controller = StreamController<AuthUser?>.broadcast();
  AuthUser? current;
  AuthFailure? nextFailure;
  int signOutCalls = 0;
  final Map<String, String> accounts = {};

  void emit(AuthUser? user) {
    current = user;
    _controller.add(user);
  }

  /// Como Firebase: al suscribirse entrega el usuario actual y luego cada cambio.
  /// La suscripción interna es inmediata, así no se pierde ningún evento.
  @override
  Stream<AuthUser?> authStateChanges() {
    late final StreamController<AuthUser?> perListener;
    StreamSubscription<AuthUser?>? inner;
    perListener = StreamController<AuthUser?>(
      onListen: () {
        perListener.add(current);
        inner = _controller.stream.listen(perListener.add);
      },
      onCancel: () => inner?.cancel(),
    );
    return perListener.stream;
  }

  @override
  Future<void> signIn({required String email, required String password}) async {
    if (nextFailure != null) throw nextFailure!;
    if (accounts[email] != password) throw const AuthFailure('Correo o contraseña incorrectos.');
    emit(AuthUser(uid: 'uid-$email', email: email));
  }

  @override
  Future<void> createAccount({required String email, required String password}) async {
    if (nextFailure != null) throw nextFailure!;
    accounts[email] = password;
    emit(AuthUser(uid: 'uid-$email', email: email));
  }

  @override
  Future<void> sendPasswordReset(String email) async {
    if (nextFailure != null) throw nextFailure!;
  }

  @override
  Future<void> signOut() async {
    signOutCalls++;
    emit(null);
  }
}

/// Backend falso para el perfil (GET /me y POST /auth/register).
class FakeProfileApi implements ProfileApi {
  final Map<String, UserProfile> profiles = {};
  ApiException? nextError;
  String? currentUid;
  int meCalls = 0;

  @override
  Future<UserProfile> me() async {
    meCalls++;
    if (nextError != null) {
      final e = nextError!;
      nextError = null;
      throw e;
    }
    final profile = profiles[currentUid];
    if (profile == null) {
      throw const ApiException(
        kind: ApiErrorKind.api,
        statusCode: 403,
        code: 'profile_missing',
        message: 'Debes completar tu registro en VIGIA.',
      );
    }
    return profile;
  }

  @override
  Future<UserProfile> register(String displayName) async {
    final profile = UserProfile(uid: currentUid!, displayName: displayName.trim(), role: 'client', status: 'active');
    profiles[currentUid!] = profile;
    return profile;
  }
}

const offline = ApiException.offline;

UserProfile profileFor(String uid, {String name = 'Marta', String status = 'active'}) =>
    UserProfile(uid: uid, displayName: name, role: 'client', status: status, email: 'marta@example.com');
