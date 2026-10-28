import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Lo mínimo que la app necesita saber de la cuenta de Firebase.
class AuthUser {
  const AuthUser({required this.uid, this.email});
  final String uid;
  final String? email;
}

/// Error de inicio de sesión o registro, con mensaje en español.
class AuthFailure implements Exception {
  const AuthFailure(this.message, {this.isConnectivity = false});
  final String message;
  final bool isConnectivity;

  @override
  String toString() => 'AuthFailure: $message';
}

/// Cuentas e inicio de sesión (Firebase Authentication).
/// Firebase guarda la sesión con el almacenamiento seguro del sistema: la app no guarda tokens.
abstract class AuthRepository {
  Stream<AuthUser?> authStateChanges();
  Future<void> signIn({required String email, required String password});
  Future<void> createAccount({required String email, required String password});
  Future<void> sendPasswordReset(String email);
  Future<void> signOut();

  /// Vuelve a pedir la contraseña antes de una acción sensible (eliminar la cuenta) y renueva el token,
  /// para que el backend vea un inicio de sesión reciente (`auth_time`).
  Future<void> reauthenticate(String password);
}

class FirebaseAuthRepository implements AuthRepository {
  FirebaseAuthRepository(this._auth);
  final FirebaseAuth _auth;

  @override
  Stream<AuthUser?> authStateChanges() =>
      _auth.authStateChanges().map((u) => u == null ? null : AuthUser(uid: u.uid, email: u.email));

  @override
  Future<void> signIn({required String email, required String password}) =>
      _guard(() => _auth.signInWithEmailAndPassword(email: email.trim(), password: password));

  @override
  Future<void> createAccount({required String email, required String password}) =>
      _guard(() => _auth.createUserWithEmailAndPassword(email: email.trim(), password: password));

  @override
  Future<void> sendPasswordReset(String email) async {
    try {
      await _auth.sendPasswordResetEmail(email: email.trim());
    } on FirebaseAuthException catch (e) {
      // No se revela si el correo tiene cuenta: solo se informan problemas de conexión o formato.
      if (e.code == 'network-request-failed' || e.code == 'invalid-email' || e.code == 'too-many-requests') {
        throw mapFirebaseAuthError(e);
      }
    }
  }

  @override
  Future<void> signOut() => _auth.signOut();

  @override
  Future<void> reauthenticate(String password) => _guard(() async {
        final user = _auth.currentUser;
        if (user == null || user.email == null) throw FirebaseAuthException(code: 'user-not-found');
        await user.reauthenticateWithCredential(EmailAuthProvider.credential(email: user.email!, password: password));
        return user.getIdToken(true);
      });

  Future<void> _guard(Future<Object?> Function() action) async {
    try {
      await action();
    } on FirebaseAuthException catch (e) {
      throw mapFirebaseAuthError(e);
    }
  }
}

/// Mensajes claros y que no revelan si un correo está registrado.
AuthFailure mapFirebaseAuthError(FirebaseAuthException e) {
  switch (e.code) {
    case 'invalid-credential':
    case 'user-not-found':
    case 'wrong-password':
      return const AuthFailure('Correo o contraseña incorrectos.');
    case 'email-already-in-use':
      return const AuthFailure('Ya existe una cuenta con ese correo. Inicia sesión o recupera tu contraseña.');
    case 'invalid-email':
      return const AuthFailure('El correo no tiene un formato válido.');
    case 'weak-password':
      return const AuthFailure('La contraseña es muy débil. Usa al menos 8 caracteres.');
    case 'user-disabled':
      return const AuthFailure('Esta cuenta está deshabilitada. Contacta al soporte de VIGIA.');
    case 'too-many-requests':
      return const AuthFailure('Demasiados intentos. Espera unos minutos e inténtalo de nuevo.');
    case 'network-request-failed':
      return const AuthFailure('Sin conexión. Revisa tu internet e inténtalo de nuevo.', isConnectivity: true);
    default:
      return const AuthFailure('No pudimos completar la operación. Inténtalo de nuevo.');
  }
}

final authRepositoryProvider = Provider<AuthRepository>((ref) => FirebaseAuthRepository(FirebaseAuth.instance));
