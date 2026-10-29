import 'package:vigia_mobile/core/network/api_exception.dart';
import 'package:vigia_mobile/features/care/data/care_api.dart';
import 'package:vigia_mobile/features/care/domain/care_models.dart';

/// Backend falso de medicamentos y tareas: valida como el real y guarda lo que se envía.
class FakeCareApi implements CareApi {
  final Map<String, List<Map<String, dynamic>>> meds = {};
  final Map<String, List<Map<String, dynamic>>> taskStore = {};
  final List<Map<String, dynamic>> sent = [];
  int _seq = 0;

  Map<String, dynamic> _med(Map<String, dynamic> body) => {
        'id': 'm${++_seq}', 'active': true, 'createdBy': 'me', ...body,
      };

  @override
  Future<List<Medication>> medications(String patientId) async =>
      (meds[patientId] ?? []).map(Medication.fromJson).toList();

  @override
  Future<Medication> createMedication(String patientId, MedicationDraft draft) async {
    final body = draft.toJson();
    sent.add({'op': 'createMedication', ...body});
    final json = _med(body);
    (meds[patientId] ??= []).add(json);
    return Medication.fromJson(json);
  }

  @override
  Future<Medication> updateMedication(String patientId, String id, Map<String, dynamic> changes) async {
    sent.add({'op': 'updateMedication', 'id': id, ...changes});
    final json = meds[patientId]!.firstWhere((m) => m['id'] == id)..addAll(changes);
    return Medication.fromJson(json);
  }

  @override
  Future<void> recordAsNeededDose(String patientId, String medicationId) async {
    sent.add({'op': 'asNeededDose', 'medicationId': medicationId});
  }

  @override
  Future<List<CareTask>> tasks(String patientId) async => (taskStore[patientId] ?? []).map(CareTask.fromJson).toList();

  @override
  Future<CareTask> createTask(String patientId, CareTaskDraft draft) async {
    final body = draft.toJson();
    sent.add({'op': 'createTask', ...body});
    if (body['kind'] == 'position_change' && !positionChangesAllowed) {
      throw const ApiException(kind: ApiErrorKind.api, statusCode: 403, code: 'plan_feature_unavailable', message: 'No incluido en el plan.');
    }
    final json = {'id': 't${++_seq}', 'active': true, 'createdBy': 'me', ...body};
    (taskStore[patientId] ??= []).add(json);
    return CareTask.fromJson(json);
  }

  bool positionChangesAllowed = false;

  @override
  Future<CareTask> updateTask(String patientId, String id, Map<String, dynamic> changes) async {
    sent.add({'op': 'updateTask', 'id': id, ...changes});
    final json = taskStore[patientId]!.firstWhere((t) => t['id'] == id)..addAll(changes);
    return CareTask.fromJson(json);
  }

  @override
  Future<void> recordUnscheduledTask(String patientId, String taskId) async {
    sent.add({'op': 'unscheduledTask', 'taskId': taskId});
  }
}
