import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/patients_api.dart';
import '../domain/patient.dart';

/// Pacientes activos con los que la persona tiene relación (propios o compartidos).
final patientsProvider = FutureProvider.autoDispose<List<Patient>>(
  (ref) => ref.watch(patientsApiProvider).list(),
);

/// Pacientes archivados (solo se consultan al abrir esa vista).
final archivedPatientsProvider = FutureProvider.autoDispose<List<Patient>>(
  (ref) => ref.watch(patientsApiProvider).list(status: 'archived'),
);

final patientProvider = FutureProvider.autoDispose.family<Patient, String>(
  (ref, id) => ref.watch(patientsApiProvider).get(id),
);

final planUsageProvider = FutureProvider.autoDispose<PlanUsage>(
  (ref) => ref.watch(patientsApiProvider).planUsage(),
);

/// Paciente activo en "Hoy". Si la persona no eligió uno, se usa el primero de su lista.
class ActivePatientController extends Notifier<String?> {
  @override
  String? build() => null;

  void select(String patientId) => state = patientId;
}

final activePatientIdProvider = NotifierProvider<ActivePatientController, String?>(ActivePatientController.new);

/// Paciente a mostrar en "Hoy": el elegido si sigue en la lista; si no, el primero; null si no hay.
final activePatientProvider = FutureProvider.autoDispose<Patient?>((ref) async {
  final patients = await ref.watch(patientsProvider.future);
  if (patients.isEmpty) return null;
  final chosen = ref.watch(activePatientIdProvider);
  return patients.firstWhere((p) => p.id == chosen, orElse: () => patients.first);
});

/// Después de crear, editar, archivar o unirse: se vuelven a pedir las listas y el uso del plan.
void refreshPatients(WidgetRef ref, {String? patientId}) {
  ref.invalidate(patientsProvider);
  ref.invalidate(archivedPatientsProvider);
  ref.invalidate(planUsageProvider);
  if (patientId != null) ref.invalidate(patientProvider(patientId));
}
