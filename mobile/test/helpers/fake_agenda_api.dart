import 'package:vigia_mobile/core/network/api_exception.dart';
import 'package:vigia_mobile/features/today/data/agenda_api.dart';
import 'package:vigia_mobile/features/today/domain/agenda.dart';

/// Backend falso de agenda: guarda los ítems por paciente y aplica los registros como el real.
class FakeAgendaApi implements AgendaApi {
  final Map<String, List<Map<String, dynamic>>> items = {};
  final Map<String, Map<String, String>> members = {};
  bool positionChanges = false;
  bool extendedCareTracking = false;
  final List<Map<String, dynamic>> recorded = [];
  final List<({String patientId, DateTime? day})> requests = [];
  DateTime today = DateTime(2026, 10, 26);

  static Map<String, dynamic> med(String id, String time, String scheduledAt, {String status = 'pending', Map<String, dynamic>? log}) => {
        'kind': 'medication', 'medicationId': id, 'name': 'Paracetamol', 'dose': '1 comprimido de 500 mg',
        'instructions': 'Con comida', 'scheduledAt': scheduledAt, 'localTime': time, 'status': status, 'log': log,
      };

  static Map<String, dynamic> task(String id, String time, String scheduledAt, {String kind = 'general', String status = 'pending', Map<String, dynamic>? log}) => {
        'kind': 'task', 'taskId': id, 'title': kind == 'general' ? 'Hidratar' : 'Cambio de posición',
        'description': null, 'taskKind': kind, 'assignedTo': null, 'scheduledAt': scheduledAt, 'localTime': time,
        'status': status, 'log': log,
      };

  @override
  Future<Agenda> agenda(String patientId, {DateTime? day}) async {
    requests.add((patientId: patientId, day: day));
    final d = day ?? today;
    return Agenda.fromJson({
      'patientId': patientId,
      'date': '${d.year}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}',
      'timeZone': 'America/Santiago',
      'features': {'positionChanges': positionChanges, 'extendedCareTracking': extendedCareTracking},
      'items': day == null || day == today ? items[patientId] ?? [] : <Map<String, dynamic>>[],
    });
  }

  @override
  Future<Map<String, String>> memberNames(String patientId) async => members[patientId] ?? {};

  Map<String, dynamic> _find(String patientId, String key, String id, DateTime? scheduledAt) =>
      items[patientId]!.firstWhere((i) => i[key] == id && (scheduledAt == null || DateTime.parse(i['scheduledAt'] as String) == scheduledAt.toUtc()));

  @override
  Future<void> recordDose(String patientId, String medicationId, {required String status, DateTime? scheduledAt, DateTime? actualAt, String? reason}) async {
    final item = _find(patientId, 'medicationId', medicationId, scheduledAt);
    if (item['status'] != 'pending') {
      throw const ApiException(kind: ApiErrorKind.api, statusCode: 409, code: 'dose_already_recorded', message: 'Esta toma ya fue registrada.');
    }
    recorded.add({'type': 'dose', 'status': status, 'scheduledAt': scheduledAt, 'actualAt': actualAt, 'reason': reason});
    item['status'] = status;
    item['log'] = {'id': 'l${recorded.length}', 'recordedBy': 'me', 'actualAt': (actualAt ?? DateTime.now()).toUtc().toIso8601String(), 'reason': reason};
  }

  @override
  Future<void> recordTask(String patientId, String taskId, {required String status, DateTime? scheduledAt, String? reason, String? note, String? position, String? positionOther}) async {
    recorded.add({'type': 'task', 'status': status, 'reason': reason, 'note': note, 'position': position});
    if (scheduledAt == null) return; // tarea sin horario: no está en la agenda programada
    final item = _find(patientId, 'taskId', taskId, scheduledAt);
    item['status'] = status;
    item['log'] = {'id': 't${recorded.length}', 'recordedBy': 'me', 'doneAt': DateTime.now().toUtc().toIso8601String(), 'reason': reason, 'position': position};
  }

  @override
  Future<void> correctDose(String patientId, String logId, {required String status, DateTime? actualAt, String? reason}) async {
    recorded.add({'type': 'correctDose', 'logId': logId, 'status': status, 'reason': reason});
    _correct(patientId, logId, status, reason);
  }

  @override
  Future<void> correctTask(String patientId, String logId,
      {required String status, String? reason, String? note, String? position, String? positionOther}) async {
    recorded.add({'type': 'correctTask', 'logId': logId, 'status': status, 'reason': reason});
    _correct(patientId, logId, status, reason);
  }

  void _correct(String patientId, String logId, String status, String? reason) {
    final item = items[patientId]!.firstWhere((i) => (i['log'] as Map?)?['id'] == logId);
    item['status'] = status;
    final log = item['log'] as Map<String, dynamic>;
    log['reason'] = reason;
    log['corrections'] = ((log['corrections'] as int?) ?? 0) + 1;
  }

  @override
  Future<void> recordPosition(String patientId, {required String position, String? positionOther, String? note}) async {
    recorded.add({'type': 'position', 'position': position, 'positionOther': positionOther});
  }
}
