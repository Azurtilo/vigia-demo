import 'package:vigia_mobile/core/network/api_exception.dart';
import 'package:vigia_mobile/features/alerts/alerts.dart';

/// Alertas falsas: atender cambia el estado como el backend; una alerta ya atendida da 409.
class FakeAlertsApi implements AlertsApi {
  final List<Map<String, dynamic>> store = [];
  final List<String> attended = [];
  int mineCalls = 0;

  Map<String, dynamic> add(String id, String kind, {String patient = 'Abuela Rosa', String? monitorState, String status = 'open'}) {
    final json = <String, dynamic>{
      'id': id,
      'patientId': 'p1',
      'patientName': patient,
      'kind': kind,
      'monitorState': monitorState,
      'occurredAt': DateTime.now().toUtc().toIso8601String(),
      'status': status,
    };
    store.add(json);
    return json;
  }

  @override
  Future<List<AlertItem>> mine() async {
    mineCalls++;
    return store.map(AlertItem.fromJson).toList();
  }

  @override
  Future<AlertItem> attend(String patientId, String alertId) async {
    final alert = store.firstWhere((a) => a['id'] == alertId);
    if (alert['status'] == 'attended') {
      throw const ApiException(
        kind: ApiErrorKind.api,
        statusCode: 409,
        code: 'alert_already_attended',
        message: 'La alerta ya fue atendida.',
      );
    }
    attended.add(alertId);
    alert
      ..['status'] = 'attended'
      ..['attendedAt'] = DateTime.now().toUtc().toIso8601String();
    return AlertItem.fromJson(alert);
  }
}
