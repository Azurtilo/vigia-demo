import 'package:flutter_test/flutter_test.dart';
import 'package:vigia_mobile/features/patients/camera_state.dart';

/// Spec 017: the node card says what the camera can actually watch.
void main() {
  Map<String, dynamic> node(
    String? state, {
    bool connected = true,
    bool active = true,
  }) => {'active': active, 'connected': connected, 'monitor_state': ?state};

  String subtitle(Map<String, dynamic> n, {bool plan = true}) =>
      nodeSubtitle(n, detectionEnabled: plan, lastSeen: 'hace 5 s');

  test('Each monitoring state has its own text and only blind ones warn', () {
    const expected = {
      'normal': ('Monitoreo activo', false),
      'persona_no_visible': ('No se ve a la persona', true),
      'sin_imagen': ('La cámara no entrega imagen', true),
      'poca_luz': ('Poca luz: el monitoreo no es confiable', true),
    };
    expected.forEach((state, value) {
      final (label, warns) = value;
      expect(
        subtitle(node(state)),
        'Conectado · Última señal hace 5 s\n$label',
      );
      expect(
        nodeWarning(node(state), detectionEnabled: true),
        warns,
        reason: state,
      );
    });
  });

  test('A node that never reported keeps the previous text', () {
    for (final state in [null, 'desconocido', 'otro']) {
      expect(subtitle(node(state)), 'Conectado · Última señal hace 5 s');
      expect(nodeWarning(node(state), detectionEnabled: true), isFalse);
    }
  });

  test('Revoked, plan and missing signal win over the reported state', () {
    expect(subtitle(node('sin_imagen', active: false)), 'Revocado');
    expect(subtitle(node('sin_imagen'), plan: false), 'No activo por plan');
    expect(
      subtitle(node('sin_imagen', connected: false)),
      'Sin señal reciente · No hay monitoreo confirmado',
    );
    for (final n in [
      node('sin_imagen', active: false),
      node('sin_imagen', connected: false),
    ]) {
      expect(nodeWarning(n, detectionEnabled: true), isFalse);
    }
    expect(nodeWarning(node('sin_imagen'), detectionEnabled: false), isFalse);
  });

  test('The aggregated camera state for the patient file has a text', () {
    expect(cameraStateLabel('sin_senal'), 'Sin señal de la cámara');
    expect(cameraWarning('sin_senal'), isTrue);
    expect(cameraStateLabel(null), isNull);
  });
}
