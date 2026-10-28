import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Entorno al que apunta la app. Se elige AL COMPILAR, sin tocar el código:
///
///   flutter run                                          -> local (emuladores)
///   flutter run --dart-define=VIGIA_ENV=production \
///               --dart-define=API_URL=https://...        -> servicios reales
enum AppEnvironment { local, production }

class AppConfig {
  const AppConfig({
    required this.environment,
    required this.apiBaseUrl,
    this.authEmulatorHost,
    this.authEmulatorPort = 9099,
    this.firebaseProjectId = 'demo-vigia',
  });

  final AppEnvironment environment;

  /// URL base del backend, sin `/v1`.
  final String apiBaseUrl;

  /// Solo en local: dónde escucha el emulador de Firebase Auth.
  final String? authEmulatorHost;
  final int authEmulatorPort;
  final String firebaseProjectId;

  bool get usesEmulators => environment == AppEnvironment.local;

  /// Lee la configuración entregada con `--dart-define`.
  ///
  /// Por defecto apunta al emulador de Android: `10.0.2.2` es el `localhost` del PC.
  /// En un teléfono físico se usa la IP del PC en la red local.
  factory AppConfig.fromEnvironment() {
    const env = String.fromEnvironment('VIGIA_ENV', defaultValue: 'local');
    const apiUrl = String.fromEnvironment('API_URL', defaultValue: 'http://10.0.2.2:8000');
    const emulatorHost = String.fromEnvironment('AUTH_EMULATOR_HOST', defaultValue: '10.0.2.2');
    return AppConfig.parse(env: env, apiUrl: apiUrl, emulatorHost: emulatorHost);
  }

  /// Separado de [AppConfig.fromEnvironment] para poder probar las reglas.
  factory AppConfig.parse({required String env, required String apiUrl, required String emulatorHost}) {
    switch (env) {
      case 'local':
        return AppConfig(
          environment: AppEnvironment.local,
          apiBaseUrl: apiUrl,
          authEmulatorHost: emulatorHost,
        );
      case 'production':
        // Producción nunca usa emuladores ni HTTP sin cifrar.
        if (!apiUrl.startsWith('https://')) {
          throw const ConfigError('En producción API_URL debe usar https://');
        }
        return AppConfig(environment: AppEnvironment.production, apiBaseUrl: apiUrl);
      default:
        throw ConfigError('VIGIA_ENV desconocido: "$env" (usa local o production)');
    }
  }
}

class ConfigError implements Exception {
  const ConfigError(this.message);
  final String message;

  @override
  String toString() => 'ConfigError: $message';
}

/// Se reemplaza en `main.dart` (y en las pruebas) con la configuración real.
final appConfigProvider = Provider<AppConfig>(
  (ref) => throw UnimplementedError('appConfigProvider debe sobrescribirse en main.dart'),
);
