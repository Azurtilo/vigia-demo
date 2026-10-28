import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/network/api_client.dart';

/// Una alerta de riesgo o de cámara (GET /v1/me/alerts y /v1/patients/{id}/alerts).
class AlertItem {
  const AlertItem({
    required this.id,
    required this.patientId,
    required this.kind,
    required this.occurredAt,
    required this.status,
    this.patientName,
    this.monitorState,
    this.attendedAt,
  });

  factory AlertItem.fromJson(Map<String, dynamic> json) => AlertItem(
        id: json['id'] as String,
        patientId: json['patientId'] as String,
        patientName: json['patientName'] as String?,
        kind: json['kind'] as String,
        monitorState: json['monitorState'] as String?,
        occurredAt: DateTime.parse(json['occurredAt'] as String),
        status: json['status'] as String,
        attendedAt: json['attendedAt'] == null ? null : DateTime.parse(json['attendedAt'] as String),
      );

  final String id;
  final String patientId;
  final String? patientName;
  final String kind; // fall | immobility | camera_blind | node_offline
  final String? monitorState; // solo en camera_blind: persona_no_visible | sin_imagen
  final DateTime occurredAt;
  final String status; // open | attended
  final DateTime? attendedAt;

  bool get isOpen => status == 'open';

  /// Las caídas y la inmovilidad son riesgos; lo demás, avisos de que la cámara no está vigilando.
  bool get isRisk => kind == 'fall' || kind == 'immobility';

  String get title => switch (kind) {
        'fall' => 'Posible caída',
        'immobility' => 'Inmovilidad prolongada',
        'camera_blind' => monitorState == 'sin_imagen' ? 'La cámara no recibe imagen' : 'La cámara no ve a la persona',
        'node_offline' => 'El nodo de detección no responde',
        _ => 'Aviso',
      };

  String get advice => switch (kind) {
        'fall' => 'Revisa al paciente ahora.',
        'immobility' => 'Revisa si necesita un cambio de posición.',
        'node_offline' => 'Revisa que el nodo tenga energía e internet.',
        _ => 'Mientras tanto, la detección no está vigilando.',
      };
}

class AlertsApi {
  AlertsApi(this._client);
  final ApiClient _client;

  /// Últimas alertas de todos los pacientes en que la persona puede atenderlas.
  Future<List<AlertItem>> mine() async {
    final json = await _client.get('/me/alerts') as Map<String, dynamic>;
    return (json['items'] as List).map((e) => AlertItem.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<AlertItem> attend(String patientId, String alertId) async => AlertItem.fromJson(
        await _client.post('/patients/$patientId/alerts/$alertId/attend') as Map<String, dynamic>,
      );
}

final alertsApiProvider = Provider<AlertsApi>((ref) => AlertsApi(ref.watch(apiClientProvider)));

final myAlertsProvider = FutureProvider.autoDispose<List<AlertItem>>((ref) => ref.watch(alertsApiProvider).mine());
