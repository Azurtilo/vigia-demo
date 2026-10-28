import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_client.dart';
import '../domain/care_models.dart';

/// Medicamentos y tareas del plan de cuidados de un paciente.
class CareApi {
  CareApi(this._client);
  final ApiClient _client;

  // ---- Medicamentos ----

  Future<List<Medication>> medications(String patientId) async {
    final data = await _client.get('/patients/$patientId/medications', query: {'includeInactive': 'true'}) as List;
    return data.map((m) => Medication.fromJson(m as Map<String, dynamic>)).toList();
  }

  Future<Medication> createMedication(String patientId, MedicationDraft draft) async => Medication.fromJson(
        await _client.post('/patients/$patientId/medications', body: draft.toJson()) as Map<String, dynamic>,
      );

  /// Guarda la versión anterior en el backend: los cambios quedan trazables.
  Future<Medication> updateMedication(String patientId, String id, Map<String, dynamic> changes) async =>
      Medication.fromJson(await _client.patch('/patients/$patientId/medications/$id', body: changes) as Map<String, dynamic>);

  /// Toma "si es necesario": se registra como dada, con la hora actual.
  Future<void> recordAsNeededDose(String patientId, String medicationId) =>
      _client.post('/patients/$patientId/medications/$medicationId/doses', body: {'status': 'given'});

  // ---- Tareas ----

  Future<List<CareTask>> tasks(String patientId) async {
    final data = await _client.get('/patients/$patientId/tasks', query: {'includeInactive': 'true'}) as List;
    return data.map((t) => CareTask.fromJson(t as Map<String, dynamic>)).toList();
  }

  Future<CareTask> createTask(String patientId, CareTaskDraft draft) async =>
      CareTask.fromJson(await _client.post('/patients/$patientId/tasks', body: draft.toJson()) as Map<String, dynamic>);

  Future<CareTask> updateTask(String patientId, String id, Map<String, dynamic> changes) async =>
      CareTask.fromJson(await _client.patch('/patients/$patientId/tasks/$id', body: changes) as Map<String, dynamic>);

  /// Tarea sin horario: se registra como realizada, con la hora actual.
  Future<void> recordUnscheduledTask(String patientId, String taskId) =>
      _client.post('/patients/$patientId/tasks/$taskId/logs', body: {'status': 'done'});
}

final careApiProvider = Provider<CareApi>((ref) => CareApi(ref.watch(apiClientProvider)));

final medicationsProvider = FutureProvider.autoDispose.family<List<Medication>, String>(
  (ref, patientId) => ref.watch(careApiProvider).medications(patientId),
);

final tasksProvider = FutureProvider.autoDispose.family<List<CareTask>, String>(
  (ref, patientId) => ref.watch(careApiProvider).tasks(patientId),
);
