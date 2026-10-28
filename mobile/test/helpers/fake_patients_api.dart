import 'package:vigia_mobile/core/network/api_exception.dart';
import 'package:vigia_mobile/features/patients/data/patients_api.dart';
import 'package:vigia_mobile/features/patients/domain/patient.dart';

const _ownerPermissions = [
  'patient.view', 'patient.edit', 'meds.manage', 'meds.administer',
  'care.manage', 'care.record', 'history.view', 'alerts.handle',
];

/// Backend falso de pacientes: aplica el límite de plan y los códigos como el real.
class FakePatientsApi implements PatientsApi {
  final Map<String, Map<String, dynamic>> _store = {};
  int maxPatients = 1; // plan Gratis
  String planName = 'Gratis';
  /// Falla las próximas [failuresLeft] lecturas con [failure] (p. ej. sin conexión durante los reintentos).
  ApiException? failure;
  int failuresLeft = 0;
  final Map<String, Map<String, dynamic>> invitations = {}; // código normalizado -> paciente
  int _seq = 0;
  PatientDraft? lastDraft;

  ApiException? _takeError() {
    if (failuresLeft <= 0) return null;
    failuresLeft--;
    return failure;
  }

  int get _active => _store.values.where((p) => p['status'] == 'active' && p['myRelation'] == 'owner').length;

  Map<String, dynamic> addPatient(String name, {String relation = 'owner', String status = 'active', List<String>? permissions, List<String> allergies = const []}) {
    final id = 'p${++_seq}';
    final json = <String, dynamic>{
      'id': id,
      'ownerUid': relation == 'owner' ? 'me' : 'otra',
      'displayName': name,
      'timeZone': 'America/Santiago',
      'status': status,
      'allergies': allergies,
      'emergencyContacts': <Map<String, dynamic>>[],
      'myRelation': relation,
      'myPermissions': permissions ?? _ownerPermissions,
    };
    _store[id] = json;
    return json;
  }

  @override
  Future<List<Patient>> list({String status = 'active'}) async {
    final e = _takeError();
    if (e != null) throw e;
    return _store.values.where((p) => p['status'] == status).map(Patient.fromJson).toList();
  }

  @override
  Future<Patient> get(String id) async {
    final e = _takeError();
    if (e != null) throw e;
    final p = _store[id];
    if (p == null) {
      throw const ApiException(kind: ApiErrorKind.api, statusCode: 404, code: 'patient_not_found', message: 'Paciente no encontrado.');
    }
    return Patient.fromJson(p);
  }

  @override
  Future<Patient> create(PatientDraft draft) async {
    lastDraft = draft;
    if (_active >= maxPatients) {
      throw ApiException(
        kind: ApiErrorKind.api,
        statusCode: 403,
        code: 'plan_limit_reached',
        message: 'Tu plan $planName permite hasta $maxPatients paciente(s) activo(s).',
      );
    }
    final json = addPatient(draft.displayName.trim());
    json.addAll(draft.toJson());
    return Patient.fromJson(json);
  }

  @override
  Future<Patient> update(String id, PatientDraft draft) async {
    lastDraft = draft;
    _store[id]!.addAll(draft.toJson());
    return Patient.fromJson(_store[id]!);
  }

  @override
  Future<Patient> archive(String id) async {
    _store[id]!['status'] = 'archived';
    return Patient.fromJson(_store[id]!);
  }

  @override
  Future<Patient> reactivate(String id) async {
    _store[id]!['status'] = 'active';
    return Patient.fromJson(_store[id]!);
  }

  @override
  Future<Patient> acceptInvitation(String code) async {
    final key = code.toUpperCase().replaceAll(RegExp(r'[^A-Z0-9]'), '');
    final target = invitations.remove(key);
    if (target == null) {
      throw const ApiException(kind: ApiErrorKind.api, statusCode: 404, code: 'invitation_invalid', message: 'El código de invitación no es válido.');
    }
    _store[target['id'] as String] = target;
    return Patient.fromJson(target);
  }

  @override
  Future<PlanUsage> planUsage() async => PlanUsage(
        planId: 'free',
        planName: planName,
        maxPatients: maxPatients,
        activePatients: _active,
        canAddPatient: _active < maxPatients,
      );
}
