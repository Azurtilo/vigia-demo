/// Spec 017: what the fixed camera can actually watch (D-073, D-077).
/// The node reports the state; these helpers only choose what is shown.
library;

const _warnings = {'persona_no_visible', 'sin_imagen', 'poca_luz', 'sin_senal'};

/// Text for a monitoring state, or null when unknown (node from before 017).
String? cameraStateLabel(dynamic state) => switch (state) {
  'normal' => 'Monitoreo activo',
  'persona_no_visible' => 'No se ve a la persona',
  'sin_imagen' => 'La cámara no entrega imagen',
  'poca_luz' => 'Poca luz: el monitoreo no es confiable',
  'sin_senal' => 'Sin señal de la cámara',
  _ => null,
};

bool cameraWarning(dynamic state) => _warnings.contains(state);

/// Subtitle of the titular's node card: revoked, plan and signal come first.
String nodeSubtitle(
  Map<String, dynamic> node, {
  required bool detectionEnabled,
  required String lastSeen,
}) {
  if (node['active'] != true) return 'Revocado';
  if (!detectionEnabled) return 'No activo por plan';
  if (node['connected'] != true) {
    return 'Sin señal reciente · No hay monitoreo confirmado';
  }
  final base = 'Conectado · Última señal $lastSeen';
  final label = cameraStateLabel(node['monitor_state']);
  return label == null ? base : '$base\n$label';
}

/// Warning icon only when the node is live and says it cannot watch.
bool nodeWarning(Map<String, dynamic> node, {required bool detectionEnabled}) =>
    node['active'] == true &&
    detectionEnabled &&
    node['connected'] == true &&
    cameraWarning(node['monitor_state']);
