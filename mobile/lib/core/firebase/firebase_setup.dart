import 'package:firebase_auth/firebase_auth.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:flutter/foundation.dart';

import '../config/app_config.dart';

/// Inicializa Firebase según el entorno.
///
/// Local: proyecto `demo-vigia`, que SOLO existe en los emuladores. Estos valores no son
/// secretos ni dan acceso a nada real: el emulador no los valida.
Future<void> initFirebase(AppConfig config) async {
  if (!config.usesEmulators) {
    // Los datos del proyecto real se generan con `flutterfire configure` en la Fase 11.
    throw const ConfigError('Configuración de Firebase para producción pendiente (Fase 11).');
  }
  final platform = defaultTargetPlatform == TargetPlatform.iOS ? 'ios' : 'android';
  await Firebase.initializeApp(
    options: FirebaseOptions(
      apiKey: 'demo-api-key',
      appId: '1:000000000000:$platform:0000000000000000',
      messagingSenderId: '000000000000',
      projectId: config.firebaseProjectId,
    ),
  );
  await FirebaseAuth.instance.useAuthEmulator(config.authEmulatorHost!, config.authEmulatorPort);
}
