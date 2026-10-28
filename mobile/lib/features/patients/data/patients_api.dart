import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_client.dart';
import '../domain/patient.dart';

class PatientsApi {
  PatientsApi(this._client);
  final ApiClient _client;

  Future<List<Patient>> list({String status = 'active'}) async {
    final data = await _client.get('/patients', query: {'status': status}) as List;
    return data.map((p) => Patient.fromJson(p as Map<String, dynamic>)).toList();
  }

  Future<Patient> get(String id) async => Patient.fromJson(await _client.get('/patients/$id') as Map<String, dynamic>);

  Future<Patient> create(PatientDraft draft) async =>
      Patient.fromJson(await _client.post('/patients', body: draft.toJson()) as Map<String, dynamic>);

  Future<Patient> update(String id, PatientDraft draft) async =>
      Patient.fromJson(await _client.patch('/patients/$id', body: draft.toJson()) as Map<String, dynamic>);

  Future<Patient> archive(String id) async =>
      Patient.fromJson(await _client.post('/patients/$id/archive') as Map<String, dynamic>);

  Future<Patient> reactivate(String id) async =>
      Patient.fromJson(await _client.post('/patients/$id/reactivate') as Map<String, dynamic>);

  /// Acepta una invitación con su código y devuelve el paciente al que se obtuvo acceso.
  Future<Patient> acceptInvitation(String code) async =>
      Patient.fromJson(await _client.post('/invitations/accept', body: {'code': code.trim()}) as Map<String, dynamic>);

  Future<PlanUsage> planUsage() async => PlanUsage.fromJson(await _client.get('/me/plan') as Map<String, dynamic>);
}

final patientsApiProvider = Provider<PatientsApi>((ref) => PatientsApi(ref.watch(apiClientProvider)));
