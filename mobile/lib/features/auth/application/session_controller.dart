import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_exception.dart';
import '../data/auth_repository.dart';
import '../data/profile_api.dart';
import '../domain/user_profile.dart';

/// Estado de la sesión. La navegación (router) decide la pantalla según este estado.
sealed class SessionState {
  const SessionState();
}

/// Arrancando o verificando la cuenta.
class SessionLoading extends SessionState {
  const SessionLoading();
}

class SignedOut extends SessionState {
  const SignedOut();
}

/// Tiene cuenta en Firebase pero aún no completó su perfil en VIGIA.
class NeedsProfile extends SessionState {
  const NeedsProfile(this.email);
  final String? email;
}

/// Tiene perfil, pero debe aceptar la versión vigente de la política antes de usar VIGIA (D-101).
class NeedsPolicy extends SessionState {
  const NeedsPolicy(this.profile, this.policyVersion);
  final UserProfile profile;
  final String policyVersion;
}

class SessionReady extends SessionState {
  const SessionReady(this.profile);
  final UserProfile profile;
}

/// Cuenta suspendida o deshabilitada: no puede usar la app.
class SessionBlocked extends SessionState {
  const SessionBlocked(this.message);
  final String message;
}

/// No se pudo verificar la cuenta (p. ej. sin conexión). Se puede reintentar.
class SessionUnavailable extends SessionState {
  const SessionUnavailable(this.error);
  final ApiException error;
}

class SessionController extends Notifier<SessionState> {
  AuthUser? _user;
  int _generation = 0; // descarta respuestas viejas si la sesión cambió mientras se esperaban

  @override
  SessionState build() {
    final sub = ref.read(authRepositoryProvider).authStateChanges().listen(_onAuthUser);
    ref.onDispose(sub.cancel);
    return const SessionLoading();
  }

  void _onAuthUser(AuthUser? user) {
    _user = user;
    if (user == null) {
      _generation++;
      state = const SignedOut();
    } else {
      unawaited(_loadProfile());
    }
  }

  Future<void> _loadProfile() async {
    final generation = ++_generation;
    state = const SessionLoading();
    try {
      final api = ref.read(profileApiProvider);
      final profile = await api.me();
      final policy = await api.policy();
      if (!ref.mounted || generation != _generation) return;
      state = policy.pending ? NeedsPolicy(profile, policy.policyVersion) : SessionReady(profile);
    } on ApiException catch (e) {
      if (!ref.mounted || generation != _generation) return;
      state = _stateForError(e);
    }
  }

  SessionState _stateForError(ApiException e) {
    switch (e.code) {
      case 'profile_missing':
        return NeedsProfile(_user?.email);
      case 'account_suspended':
      case 'account_disabled':
        return SessionBlocked(e.message);
      case 'auth_invalid':
      case 'auth_expired':
      case 'auth_revoked':
        // La sesión guardada ya no es válida: se cierra para volver a iniciarla.
        unawaited(ref.read(authRepositoryProvider).signOut());
        return const SignedOut();
      default:
        return SessionUnavailable(e);
    }
  }

  /// Vuelve a intentar verificar la cuenta (botón "Reintentar").
  Future<void> retry() async {
    if (_user == null) {
      state = const SignedOut();
      return;
    }
    await _loadProfile();
  }

  /// Completa el registro en VIGIA. Devuelve un mensaje de error para mostrar, o null si salió bien.
  Future<String?> completeProfile(String displayName) async {
    try {
      await ref.read(profileApiProvider).register(displayName);
      await _loadProfile(); // una cuenta nueva aún no aceptó la política
      return null;
    } on ApiException catch (e) {
      if (e.code == 'already_registered') {
        await _loadProfile();
        return null;
      }
      return e.message;
    }
  }

  /// Acepta la política vigente. Devuelve un mensaje de error para mostrar, o null si salió bien.
  Future<String?> acceptPolicy() async {
    final current = state;
    if (current is! NeedsPolicy) return null;
    try {
      await ref.read(profileApiProvider).acceptPolicy();
      if (ref.mounted) state = SessionReady(current.profile);
      return null;
    } on ApiException catch (e) {
      return e.message;
    }
  }

  /// Elimina la cuenta tras confirmar la contraseña (RF-019-27). Devuelve un mensaje de error, o null.
  Future<String?> deleteAccount(String password) async {
    final auth = ref.read(authRepositoryProvider);
    try {
      await auth.reauthenticate(password);
      await ref.read(profileApiProvider).deleteAccount();
    } on AuthFailure catch (e) {
      return e.message;
    } on ApiException catch (e) {
      return e.message;
    }
    await auth.signOut(); // la cuenta ya no existe en Firebase: se limpia la sesión local
    return null;
  }

  Future<void> signOut() => ref.read(authRepositoryProvider).signOut();
}

final sessionControllerProvider = NotifierProvider<SessionController, SessionState>(SessionController.new);
