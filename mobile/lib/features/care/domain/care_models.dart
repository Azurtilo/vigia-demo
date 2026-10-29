/// Horario en la hora local del paciente: horas fijas y días (1 = lunes … 7 = domingo; vacío = todos).
class ScheduleSpec {
  const ScheduleSpec({required this.times, this.daysOfWeek = const []});

  factory ScheduleSpec.fromJson(Map<String, dynamic> json) => ScheduleSpec(
        times: (json['times'] as List).cast<String>(),
        daysOfWeek: (json['daysOfWeek'] as List? ?? []).cast<int>(),
      );

  final List<String> times; // "HH:MM"
  final List<int> daysOfWeek;

  Map<String, dynamic> toJson() => {'times': times, 'daysOfWeek': daysOfWeek};

  static const _dayNames = ['lun', 'mar', 'mié', 'jue', 'vie', 'sáb', 'dom'];

  /// "08:00 y 20:00 · todos los días" / "09:00 · lun, mié, vie".
  String get label {
    final t = times.length <= 1 ? times.join() : '${times.sublist(0, times.length - 1).join(', ')} y ${times.last}';
    final d = daysOfWeek.isEmpty || daysOfWeek.length == 7 ? 'todos los días' : (daysOfWeek.map((n) => _dayNames[n - 1]).join(', '));
    return '$t · $d';
  }
}

String _isoDate(DateTime d) =>
    '${d.year.toString().padLeft(4, '0')}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';

String formatDate(DateTime d) => '${d.day.toString().padLeft(2, '0')}-${d.month.toString().padLeft(2, '0')}-${d.year}';

/// Medicamento tal como lo indicó el responsable del tratamiento (la app no interpreta la dosis).
class Medication {
  const Medication({
    required this.id,
    required this.name,
    required this.dose,
    required this.scheduleType,
    required this.startDate,
    required this.active,
    this.instructions,
    this.schedule,
    this.endDate,
  });

  factory Medication.fromJson(Map<String, dynamic> json) => Medication(
        id: json['id'] as String,
        name: json['name'] as String,
        dose: json['dose'] as String,
        instructions: json['instructions'] as String?,
        scheduleType: json['scheduleType'] as String,
        schedule: json['schedule'] == null ? null : ScheduleSpec.fromJson(json['schedule'] as Map<String, dynamic>),
        startDate: DateTime.parse(json['startDate'] as String),
        endDate: json['endDate'] == null ? null : DateTime.parse(json['endDate'] as String),
        active: json['active'] as bool,
      );

  final String id;
  final String name;
  final String dose;
  final String? instructions;
  final String scheduleType; // fixed | as_needed
  final ScheduleSpec? schedule;
  final DateTime startDate;
  final DateTime? endDate;
  final bool active;

  bool get asNeeded => scheduleType == 'as_needed';
  String get scheduleLabel => asNeeded ? 'Si es necesario' : schedule!.label;
}

class MedicationDraft {
  const MedicationDraft({
    required this.name,
    required this.dose,
    required this.scheduleType,
    required this.startDate,
    this.instructions,
    this.schedule,
    this.endDate,
  });

  final String name;
  final String dose;
  final String? instructions;
  final String scheduleType;
  final ScheduleSpec? schedule;
  final DateTime startDate;
  final DateTime? endDate;

  Map<String, dynamic> toJson() => {
        'name': name.trim(),
        'dose': dose.trim(),
        'instructions': (instructions?.trim().isEmpty ?? true) ? null : instructions!.trim(),
        'scheduleType': scheduleType,
        'schedule': scheduleType == 'fixed' ? schedule!.toJson() : null,
        'startDate': _isoDate(startDate),
        'endDate': endDate == null ? null : _isoDate(endDate!),
      };
}

/// Tarea del plan de cuidados. La frecuencia la define el responsable (no hay pautas clínicas predefinidas).
class CareTask {
  const CareTask({
    required this.id,
    required this.title,
    required this.kind,
    required this.scheduleType,
    required this.startDate,
    required this.active,
    this.description,
    this.schedule,
    this.endDate,
    this.assignedTo,
  });

  factory CareTask.fromJson(Map<String, dynamic> json) => CareTask(
        id: json['id'] as String,
        title: json['title'] as String,
        description: json['description'] as String?,
        kind: json['kind'] as String,
        scheduleType: json['scheduleType'] as String,
        schedule: json['schedule'] == null ? null : ScheduleSpec.fromJson(json['schedule'] as Map<String, dynamic>),
        startDate: DateTime.parse(json['startDate'] as String),
        endDate: json['endDate'] == null ? null : DateTime.parse(json['endDate'] as String),
        assignedTo: json['assignedTo'] as String?,
        active: json['active'] as bool,
      );

  final String id;
  final String title;
  final String? description;
  final String kind; // general | position_change
  final String scheduleType; // fixed | unscheduled
  final ScheduleSpec? schedule;
  final DateTime startDate;
  final DateTime? endDate;
  final String? assignedTo;
  final bool active;

  bool get unscheduled => scheduleType == 'unscheduled';
  bool get isPositionChange => kind == 'position_change';
  String get scheduleLabel => unscheduled ? 'Sin horario fijo' : schedule!.label;
}

class CareTaskDraft {
  const CareTaskDraft({
    required this.title,
    required this.kind,
    required this.scheduleType,
    required this.startDate,
    this.description,
    this.schedule,
    this.endDate,
    this.assignedTo,
  });

  final String title;
  final String? description;
  final String kind;
  final String scheduleType;
  final ScheduleSpec? schedule;
  final DateTime startDate;
  final DateTime? endDate;
  final String? assignedTo;

  /// [forUpdate]: al editar no se envía `kind` (no se puede cambiar el tipo de una tarea).
  Map<String, dynamic> toJson({bool forUpdate = false}) => {
        'title': title.trim(),
        'description': (description?.trim().isEmpty ?? true) ? null : description!.trim(),
        if (!forUpdate) 'kind': kind,
        'scheduleType': scheduleType,
        'schedule': scheduleType == 'fixed' ? schedule!.toJson() : null,
        'startDate': _isoDate(startDate),
        'endDate': endDate == null ? null : _isoDate(endDate!),
        'assignedTo': assignedTo,
      };
}
