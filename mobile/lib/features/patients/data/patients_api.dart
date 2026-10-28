import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_client.dart';
import '../../privacy/privacy.dart';
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

  Future<List<PatientConsent>> consents(String id) async {
    final json = await _client.get('/patients/$id/consents') as Map<String, dynamic>;
    return (json['items'] as List).map((c) => PatientConsent.fromJson(c as Map<String, dynamic>)).toList();
  }

  /// Registra el consentimiento de una finalidad. Solo el responsable.
  Future<PatientConsent> registerConsent(String id, String scope, ConsentDraft draft) async => PatientConsent.fromJson(
        await _client.post('/patients/$id/consents', body: draft.toJson(scope)) as Map<String, dynamic>,
      );

  Future<PatientConsent> revokeConsent(String id, String scope) async => PatientConsent.fromJson(
        await _client.post('/patients/$id/consents/$scope/revoke') as Map<String, dynamic>,
      );

  /// Todos los datos del paciente en JSON, sin tokens ni códigos (RF-019-25). Solo el responsable.
  Future<Map<String, dynamic>> exportPatient(String id) async =>
      await _client.get('/patients/$id/export') as Map<String, dynamic>;

  /// Borra el paciente y todos sus datos (RF-019-26). Se confirma con su nombre.
  Future<void> deletePatient(String id, String confirmName) =>
      _client.post('/patients/$id/delete', body: {'confirmName': confirmName});
}

final patientsApiProvider = Provider<PatientsApi>((ref) => PatientsApi(ref.watch(apiClientProvider)));
