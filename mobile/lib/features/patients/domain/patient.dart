/// Paciente tal como lo entrega el backend (GET /v1/patients/{id}).
class Patient {
  const Patient({
    required this.id,
    required this.ownerUid,
    required this.displayName,
    required this.timeZone,
    required this.status,
    required this.myRelation,
    required this.myPermissions,
    this.birthDate,
    this.mobility,
    this.careNeeds,
    this.notes,
    this.allergies = const [],
    this.emergencyContacts = const [],
  });

  factory Patient.fromJson(Map<String, dynamic> json) => Patient(
        id: json['id'] as String,
        ownerUid: json['ownerUid'] as String,
        displayName: json['displayName'] as String,
        timeZone: json['timeZone'] as String? ?? 'America/Santiago',
        status: json['status'] as String,
        birthDate: json['birthDate'] == null ? null : DateTime.parse(json['birthDate'] as String),
        mobility: json['mobility'] as String?,
        careNeeds: json['careNeeds'] as String?,
        notes: json['notes'] as String?,
        allergies: (json['allergies'] as List? ?? []).cast<String>(),
        emergencyContacts: (json['emergencyContacts'] as List? ?? [])
            .map((c) => EmergencyContact.fromJson(c as Map<String, dynamic>))
            .toList(),
        myRelation: json['myRelation'] as String,
        myPermissions: (json['myPermissions'] as List).cast<String>().toSet(),
      );

  final String id;
  final String ownerUid;
  final String displayName;
  final String timeZone;
  final String status; // active | archived
  final DateTime? birthDate;
  final String? mobility;
  final String? careNeeds;
  final String? notes;
  final List<String> allergies;
  final List<EmergencyContact> emergencyContacts;
  final String myRelation; // owner | family | caregiver
  final Set<String> myPermissions;

  bool get isOwner => myRelation == 'owner';
  bool get isArchived => status == 'archived';
  bool can(String permission) => myPermissions.contains(permission);

  String get relationLabel => switch (myRelation) {
        'owner' => 'Eres responsable',
        'family' => 'Eres familiar',
        _ => 'Eres cuidador/a',
      };
}

class EmergencyContact {
  const EmergencyContact({required this.name, required this.phone, this.relation});

  factory EmergencyContact.fromJson(Map<String, dynamic> json) => EmergencyContact(
        name: json['name'] as String,
        phone: json['phone'] as String,
        relation: json['relation'] as String?,
      );

  final String name;
  final String phone;
  final String? relation;

  Map<String, dynamic> toJson() => {'name': name, 'phone': phone, if (relation != null) 'relation': relation};
}

/// Datos que se envían al crear o editar (POST/PATCH). Los vacíos se envían como null.
class PatientDraft {
  const PatientDraft({
    required this.displayName,
    this.birthDate,
    this.mobility,
    this.careNeeds,
    this.notes,
    this.allergies = const [],
    this.emergencyContacts = const [],
  });

  final String displayName;
  final DateTime? birthDate;
  final String? mobility;
  final String? careNeeds;
  final String? notes;
  final List<String> allergies;
  final List<EmergencyContact> emergencyContacts;

  static String? _blankToNull(String? v) => (v == null || v.trim().isEmpty) ? null : v.trim();

  Map<String, dynamic> toJson() => {
        'displayName': displayName.trim(),
        'birthDate': birthDate == null
            ? null
            : '${birthDate!.year.toString().padLeft(4, '0')}-${birthDate!.month.toString().padLeft(2, '0')}-${birthDate!.day.toString().padLeft(2, '0')}',
        'mobility': _blankToNull(mobility),
        'careNeeds': _blankToNull(careNeeds),
        'notes': _blankToNull(notes),
        'allergies': allergies.map((a) => a.trim()).where((a) => a.isNotEmpty).toList(),
        'emergencyContacts': emergencyContacts.map((c) => c.toJson()).toList(),
      };
}

/// Uso del plan (GET /v1/me/plan).
class PlanUsage {
  const PlanUsage({
    required this.planId,
    required this.planName,
    required this.maxPatients,
    required this.activePatients,
    required this.canAddPatient,
  });

  factory PlanUsage.fromJson(Map<String, dynamic> json) => PlanUsage(
        planId: json['planId'] as String,
        planName: json['planName'] as String,
        maxPatients: json['maxPatients'] as int?,
        activePatients: json['activePatients'] as int,
        canAddPatient: json['canAddPatient'] as bool,
      );

  final String planId;
  final String planName;
  final int? maxPatients; // null = sin límite
  final int activePatients;
  final bool canAddPatient;

  String get usageLabel => maxPatients == null
      ? '$activePatients pacientes activos · plan $planName sin límite'
      : '$activePatients de $maxPatients pacientes activos · plan $planName';
}
