import 'package:flutter_test/flutter_test.dart';
import 'package:vigia_mobile/core/config/app_config.dart';

void main() {
  test('local apunta a los emuladores', () {
    final config = AppConfig.parse(env: 'local', apiUrl: 'http://10.0.2.2:8000', emulatorHost: '10.0.2.2');

    expect(config.usesEmulators, isTrue);
    expect(config.authEmulatorHost, '10.0.2.2');
    expect(config.firebaseProjectId, 'demo-vigia');
  });

  test('producción exige HTTPS y no usa emuladores', () {
    final config = AppConfig.parse(env: 'production', apiUrl: 'https://api.vigia.cl', emulatorHost: 'x');

    expect(config.usesEmulators, isFalse);
    expect(config.authEmulatorHost, isNull);
    expect(
      () => AppConfig.parse(env: 'production', apiUrl: 'http://api.vigia.cl', emulatorHost: 'x'),
      throwsA(isA<ConfigError>()),
    );
  });

  test('un entorno desconocido se rechaza en vez de suponer uno', () {
    expect(() => AppConfig.parse(env: 'staging', apiUrl: 'https://x', emulatorHost: 'x'), throwsA(isA<ConfigError>()));
  });
}
