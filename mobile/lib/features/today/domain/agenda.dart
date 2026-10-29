/// Agenda del día (GET /v1/patients/{id}/agenda), en la hora local del paciente.
class Agenda {
  const Agenda({
    required this.patientId,
    required this.date,
    required this.timeZone,
    required this.positionChanges,
    required this.extendedCareTracking,
    required this.items,
  });

  factory Agenda.fromJson(Map<String, dynamic> json) {
    final features = json['features'] as Map<String, dynamic>? ?? const {};
    return Agenda(
      patientId: json['patientId'] as String,
      date: DateTime.parse(json['date'] as String),
      timeZone: json['timeZone'] as String,
      positionChanges: features['positionChanges'] as bool? ?? false,
      extendedCareTracking: features['extendedCareTracking'] as bool? ?? false,
      items: (json['items'] as List).map((i) => AgendaItem.fromJson(i as Map<String, dynamic>)).toList(),
    );
  }

  final String patientId;
  final DateTime date; // día local del paciente (sin hora)
  final String timeZone;

  /// Funciones del plan del responsable del paciente.
  final bool positionChanges;
  final bool extendedCareTracking;
  final List<AgendaItem> items;

  int get recordedCount => items.where((i) => i.isRecorded).length;
}

/// Ítem de la agenda: una toma de medicamento o una tarea (incluye cambios de posición).
sealed class AgendaItem {
  const AgendaItem({required this.status, this.scheduledAt, this.localTime, this.log});

  factory AgendaItem.fromJson(Map<String, dynamic> json) => switch (json['kind']) {
        'medication' => MedicationItem.fromJson(json),
        _ => TaskItem.fromJson(json),
      };

  /// Instante programado (UTC). Null en "si es necesario" y en tareas sin horario.
  final DateTime? scheduledAt;

  /// Hora configurada en la hora local del paciente, p. ej. "08:00".
  final String? localTime;

  /// pending | given | delayed | omitted (tomas) · pending | done | skipped (tareas).
  final String status;
  final LogEntry? log;

  bool get isRecorded => status != 'pending';
  String get title;
}

class MedicationItem extends AgendaItem {
  const MedicationItem({
    required this.medicationId,
    required this.name,
    required this.dose,
    required super.status,
    this.instructions,
    super.scheduledAt,
    super.localTime,
    super.log,
  });

  factory MedicationItem.fromJson(Map<String, dynamic> json) => MedicationItem(
        medicationId: json['medicationId'] as String,
        name: json['name'] as String,
        dose: json['dose'] as String,
        instructions: json['instructions'] as String?,
        scheduledAt: _date(json['scheduledAt']),
        localTime: json['localTime'] as String?,
        status: json['status'] as String,
        log: json['log'] == null ? null : LogEntry.fromDoseJson(json['log'] as Map<String, dynamic>),
      );

  final String medicationId;
  final String name;
  final String dose;
  final String? instructions;

  @override
  String get title => name;
}

class TaskItem extends AgendaItem {
  const TaskItem({
    required this.title,
    required this.taskKind,
    required super.status,
    this.taskId,
    this.description,
    this.assignedTo,
    super.scheduledAt,
    super.localTime,
    super.log,
  });

  factory TaskItem.fromJson(Map<String, dynamic> json) => TaskItem(
        taskId: json['taskId'] as String?,
        title: json['title'] as String,
        description: json['description'] as String?,
        taskKind: json['taskKind'] as String,
        assignedTo: json['assignedTo'] as String?,
        scheduledAt: _date(json['scheduledAt']),
        localTime: json['localTime'] as String?,
        status: json['status'] as String,
        log: json['log'] == null ? null : LogEntry.fromTaskJson(json['log'] as Map<String, dynamic>),
      );

  final String? taskId; // null: cambio de posición registrado sin tarea
  @override
  final String title;
  final String? description;
  final String taskKind; // general | position_change
  final String? assignedTo;

  bool get isPositionChange => taskKind == 'position_change';
}

/// Lo que se registró: quién, cuándo y por qué.
class LogEntry {
  const LogEntry({
    required this.id,
    required this.recordedBy,
    this.at,
    this.reason,
    this.note,
    this.position,
    this.positionOther,
    this.corrections = 0,
  });

  factory LogEntry.fromDoseJson(Map<String, dynamic> json) => LogEntry(
        id: json['id'] as String,
        recordedBy: json['recordedBy'] as String,
        at: _date(json['actualAt']),
        reason: json['reason'] as String?,
        corrections: json['corrections'] as int? ?? 0,
      );

  factory LogEntry.fromTaskJson(Map<String, dynamic> json) => LogEntry(
        id: json['id'] as String,
        recordedBy: json['recordedBy'] as String,
        at: _date(json['doneAt']),
        reason: json['reason'] as String?,
        note: json['note'] as String?,
        position: json['position'] as String?,
        positionOther: json['positionOther'] as String?,
        corrections: json['corrections'] as int? ?? 0,
      );

  final String id;
  final String recordedBy; // uid
  final DateTime? at; // hora real (UTC)
  final String? reason;
  final String? note;
  final String? position;
  final String? positionOther;
  final int corrections;
}

DateTime? _date(Object? value) => value == null ? null : DateTime.parse(value as String);

/// Posiciones descriptivas (no clínicas), con su texto para mostrar.
const positionLabels = {
  'supine': 'Boca arriba',
  'left_side': 'De lado izquierdo',
  'right_side': 'De lado derecho',
  'prone': 'Boca abajo',
  'sitting': 'Sentado/a',
  'other': 'Otra',
};
