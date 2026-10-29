/// Política de privacidad y consentimiento por paciente (spec 014, RF-019-17, D-101).
library;

/// Estado de la política de la cuenta (GET /v1/privacy).
class PolicyStatus {
  const PolicyStatus({required this.policyVersion, required this.accepted, required this.enforced});

  factory PolicyStatus.fromJson(Map<String, dynamic> json) => PolicyStatus(
        policyVersion: json['policyVersion'] as String,
        accepted: json['accepted'] as bool,
        enforced: json['enforced'] as bool? ?? true,
      );

  final String policyVersion;
  final bool accepted;

  /// Falso solo en entornos de prueba del backend: entonces la app no la exige.
  final bool enforced;

  bool get pending => enforced && !accepted;
}

/// Finalidades con consentimiento propio.
const consentScopes = ['cuidado', 'deteccion'];

const consentTitles = {
  'cuidado': 'Datos de cuidado',
  'deteccion': 'Detección con cámara',
};

const consentDescriptions = {
  'cuidado': 'Medicamentos, tareas, tomas y cambios de posición. Sin este consentimiento no se pueden registrar.',
  'deteccion': 'Posturas, inmovilidad y caídas detectadas por el nodo. Solo metadatos: el video nunca sale del domicilio.',
};

const revokeEffects = {
  'cuidado': 'No se podrán registrar nuevos datos de cuidado. Lo ya registrado se conserva según los plazos de la política.',
  'deteccion': 'La cámara deja de enviar datos de inmediato.',
};

/// Consentimiento de un paciente para una finalidad (GET /v1/patients/{id}/consents).
class PatientConsent {
  const PatientConsent({
    required this.scope,
    required this.active,
    this.basis,
    this.representativeName,
    this.representativeRelation,
    this.recordedAt,
    this.revokedAt,
  });

  factory PatientConsent.fromJson(Map<String, dynamic> json) => PatientConsent(
        scope: json['scope'] as String,
        active: json['active'] as bool,
        basis: json['basis'] as String?,
        representativeName: json['representativeName'] as String?,
        representativeRelation: json['representativeRelation'] as String?,
        recordedAt: json['recordedAt'] == null ? null : DateTime.parse(json['recordedAt'] as String),
        revokedAt: json['revokedAt'] == null ? null : DateTime.parse(json['revokedAt'] as String),
      );

  final String scope; // cuidado | deteccion
  final bool active;
  final String? basis; // titular | representante
  final String? representativeName;
  final String? representativeRelation;
  final DateTime? recordedAt;
  final DateTime? revokedAt;

  /// El backend devuelve siempre las dos finalidades: una nunca registrada llega inactiva y sin `revokedAt`.
  String get statusLabel => active ? 'Activo' : (revokedAt != null ? 'Revocado' : 'Sin registrar');

  String get basisLabel => switch (basis) {
        'titular' => 'Lo dio el propio paciente',
        'representante' => 'Lo dio $representativeName ($representativeRelation)',
        _ => '',
      };
}

/// Quién consiente. Con representante, el nombre y la relación son obligatorios.
class ConsentDraft {
  const ConsentDraft.titular() : basis = 'titular', representativeName = null, representativeRelation = null;
  const ConsentDraft.representative(String name, String relation)
      : basis = 'representante',
        representativeName = name,
        representativeRelation = relation;

  final String basis;
  final String? representativeName;
  final String? representativeRelation;

  Map<String, dynamic> toJson(String scope) => {
        'scope': scope,
        'basis': basis,
        if (representativeName != null) 'representativeName': representativeName!.trim(),
        if (representativeRelation != null) 'representativeRelation': representativeRelation!.trim(),
      };
}

/// Misma regla que el backend (`erase.delete_patient`) para confirmar un borrado:
/// sin distinguir mayúsculas ni espacios al inicio o al final.
bool sameName(String typed, String name) {
  String norm(String s) => s.trim().toLowerCase();
  return norm(typed).isNotEmpty && norm(typed) == norm(name);
}
