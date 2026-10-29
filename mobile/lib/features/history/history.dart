import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/network/api_client.dart';
import '../today/domain/agenda.dart';

/// Una entrada del historial (GET /v1/patients/{id}/history).
class HistoryEntry {
  const HistoryEntry({
    required this.id,
    required this.type,
    required this.category,
    required this.occurredAt,
    required this.actorUid,
    required this.actorName,
    required this.data,
  });

  factory HistoryEntry.fromJson(Map<String, dynamic> json) => HistoryEntry(
        id: json['id'] as String,
        type: json['type'] as String,
        category: json['category'] as String,
        occurredAt: DateTime.parse(json['occurredAt'] as String),
        actorUid: json['actorUid'] as String,
        actorName: json['actorName'] as String,
        data: (json['data'] as Map?)?.cast<String, dynamic>() ?? const {},
      );

  final String id;
  final String type; // p. ej. medication.given, position.changed
  final String category; // medication | task | position | change
  final DateTime occurredAt;
  final String actorUid;
  final String actorName;
  final Map<String, dynamic> data;

  String? get reason => data['reason'] as String?;
  String? get note => data['note'] as String?;

  /// Texto en español a partir del tipo y los datos (el backend los guarda estructurados).
  String get description {
    final name = data['name'] ?? data['title'] ?? '';
    final dose = data['dose'] == null ? '' : ' (${data['dose']})';
    return switch (type) {
      'medication.given' => 'Dio $name$dose',
      'medication.delayed' => 'Dio con retraso $name$dose',
      'medication.omitted' => 'No se dio $name$dose',
      'medication.dose_corrected' => 'Corrigió un registro de $name: ${_status(data['from'])} → ${_status(data['to'])}',
      'medication.created' => 'Agregó el medicamento $name',
      'medication.updated' => 'Modificó el medicamento $name',
      'task.done' => 'Realizó «$name»',
      'task.skipped' => 'No se realizó «$name»',
      'task.corrected' => 'Corrigió un registro de «$name»: ${_status(data['from'])} → ${_status(data['to'])}',
      'task.created' => 'Agregó la tarea «$name»',
      'task.updated' => 'Modificó la tarea «$name»',
      'position.changed' => 'Cambio de posición: ${positionLabels[data['position']] ?? 'registrado'}',
      _ => 'Actividad registrada',
    };
  }

  static String _status(Object? s) => switch (s) {
        'given' => 'dada',
        'delayed' => 'con retraso',
        'omitted' => 'no se dio',
        'done' => 'realizada',
        'skipped' => 'no realizada',
        _ => '$s',
      };
}

class HistoryPage {
  const HistoryPage({required this.items, this.nextCursor, this.visibleSince, this.hiddenOlderEntries = false});

  factory HistoryPage.fromJson(Map<String, dynamic> json) => HistoryPage(
        items: (json['items'] as List).map((e) => HistoryEntry.fromJson(e as Map<String, dynamic>)).toList(),
        nextCursor: json['nextCursor'] as String?,
        visibleSince: json['visibleSince'] == null ? null : DateTime.parse(json['visibleSince'] as String),
        hiddenOlderEntries: json['hiddenOlderEntries'] as bool? ?? false,
      );

  final List<HistoryEntry> items;
  final String? nextCursor;

  /// Límite del plan del responsable (null = sin límite).
  final DateTime? visibleSince;

  /// Hay registros más antiguos que el plan no muestra (se conservan).
  final bool hiddenOlderEntries;
}

class HistoryApi {
  HistoryApi(this._client);
  final ApiClient _client;

  Future<HistoryPage> page(String patientId, {String? category, String? cursor, int limit = 20}) async =>
      HistoryPage.fromJson(
        await _client.get('/patients/$patientId/history', query: {
          'limit': '$limit',
          'category': ?category,
          'cursor': ?cursor,
        }) as Map<String, dynamic>,
      );
}

final historyApiProvider = Provider<HistoryApi>((ref) => HistoryApi(ref.watch(apiClientProvider)));

typedef HistoryKey = ({String patientId, String? category});

/// Historial paginado: guarda las páginas cargadas y pide la siguiente con [loadMore].
class HistoryController extends AsyncNotifier<HistoryPage> {
  HistoryController(this.key);
  final HistoryKey key;
  bool _loadingMore = false;

  @override
  Future<HistoryPage> build() => ref.read(historyApiProvider).page(key.patientId, category: key.category);

  Future<void> loadMore() async {
    final current = state.value;
    if (current?.nextCursor == null || _loadingMore) return;
    _loadingMore = true;
    try {
      final next = await ref.read(historyApiProvider).page(key.patientId, category: key.category, cursor: current!.nextCursor);
      state = AsyncData(HistoryPage(
        items: [...current.items, ...next.items],
        nextCursor: next.nextCursor,
        visibleSince: next.visibleSince,
        hiddenOlderEntries: next.hiddenOlderEntries,
      ));
    } finally {
      _loadingMore = false;
    }
  }
}

final historyProvider = AsyncNotifierProvider.autoDispose.family<HistoryController, HistoryPage, HistoryKey>(
  HistoryController.new,
);
