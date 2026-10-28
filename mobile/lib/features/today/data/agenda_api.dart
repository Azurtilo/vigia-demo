import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_client.dart';
import '../domain/agenda.dart';

/// Agenda y registros del día. Las horas viajan en UTC (ISO 8601 con "Z").
class AgendaApi {
  AgendaApi(this._client);
  final ApiClient _client;

  Future<Agenda> agenda(String patientId, {DateTime? day}) async {
    final query = day == null ? null : {'date': _isoDate(day)};
    return Agenda.fromJson(await _client.get('/patients/$patientId/agenda', query: query) as Map<String, dynamic>);
  }

  /// Nombres de las personas con acceso (para mostrar quién registró cada cosa).
  Future<Map<String, String>> memberNames(String patientId) async {
    final data = await _client.get('/patients/$patientId/members') as List;
    return {for (final m in data.cast<Map<String, dynamic>>()) m['uid'] as String: m['displayName'] as String};
  }

  Future<void> recordDose(
    String patientId,
    String medicationId, {
    required String status,
    DateTime? scheduledAt,
    DateTime? actualAt,
    String? reason,
  }) =>
      _client.post('/patients/$patientId/medications/$medicationId/doses', body: {
        'status': status,
        if (scheduledAt != null) 'scheduledAt': _utc(scheduledAt),
        if (actualAt != null) 'actualAt': _utc(actualAt),
        'reason': ?reason,
      });

  Future<void> recordTask(
    String patientId,
    String taskId, {
    required String status,
    DateTime? scheduledAt,
    String? reason,
    String? note,
    String? position,
    String? positionOther,
  }) =>
      _client.post('/patients/$patientId/tasks/$taskId/logs', body: {
        'status': status,
        if (scheduledAt != null) 'scheduledAt': _utc(scheduledAt),
        'reason': ?reason,
        'note': ?note,
        'position': ?position,
        'positionOther': ?positionOther,
      });

  Future<void> recordPosition(String patientId, {required String position, String? positionOther, String? note}) =>
      _client.post('/patients/$patientId/position-changes', body: {
        'position': position,
        'positionOther': ?positionOther,
        'note': ?note,
      });

  /// Corrige un registro de toma. El backend guarda el valor anterior (trazabilidad).
  Future<void> correctDose(String patientId, String logId, {required String status, DateTime? actualAt, String? reason}) =>
      _client.patch('/patients/$patientId/doses/$logId', body: {
        'status': status,
        if (actualAt != null) 'actualAt': _utc(actualAt),
        'reason': ?reason,
      });

  /// Corrige un registro de tarea. El backend guarda el valor anterior (trazabilidad).
  Future<void> correctTask(String patientId, String logId,
          {required String status, String? reason, String? note, String? position, String? positionOther}) =>
      _client.patch('/patients/$patientId/task-logs/$logId', body: {
        'status': status,
        'reason': ?reason,
        'note': ?note,
        'position': ?position,
        'positionOther': ?positionOther,
      });

  static String _utc(DateTime t) => t.toUtc().toIso8601String();
  static String _isoDate(DateTime d) =>
      '${d.year.toString().padLeft(4, '0')}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';
}

final agendaApiProvider = Provider<AgendaApi>((ref) => AgendaApi(ref.watch(apiClientProvider)));
