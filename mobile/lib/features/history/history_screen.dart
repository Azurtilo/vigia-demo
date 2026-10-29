import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/network/api_exception.dart';
import '../../core/theme/vigia_colors.dart';
import '../../core/widgets/async_view.dart';
import '../auth/application/session_controller.dart';
import '../care/domain/care_models.dart';
import '../today/presentation/record_sheets.dart';
import 'history.dart';

const _filters = {null: 'Todo', 'medication': 'Tomas', 'task': 'Tareas', 'position': 'Posiciones', 'change': 'Cambios'};

/// Historial del paciente: del más reciente al más antiguo, según el plan del responsable.
class HistoryScreen extends ConsumerStatefulWidget {
  const HistoryScreen({super.key, required this.patientId});
  final String patientId;

  @override
  ConsumerState<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends ConsumerState<HistoryScreen> {
  String? _category;

  @override
  Widget build(BuildContext context) {
    final key = (patientId: widget.patientId, category: _category);
    final history = ref.watch(historyProvider(key));
    final session = ref.watch(sessionControllerProvider);
    final myUid = session is SessionReady ? session.profile.uid : null;

    return Scaffold(
      appBar: AppBar(title: const Text('Historial')),
      body: Column(
        children: [
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.fromLTRB(16, 4, 16, 8),
            child: Row(
              children: [
                for (final f in _filters.entries)
                  Padding(
                    padding: const EdgeInsets.only(right: 8),
                    child: ChoiceChip(
                      label: Text(f.value),
                      selected: _category == f.key,
                      onSelected: (_) => setState(() => _category = f.key),
                      materialTapTargetSize: MaterialTapTargetSize.padded,
                    ),
                  ),
              ],
            ),
          ),
          Expanded(
            child: AsyncView(
              value: history,
              onRetry: () => ref.invalidate(historyProvider(key)),
              builder: (page) => RefreshIndicator(
                onRefresh: () async => ref.invalidate(historyProvider(key)),
                child: ListView(
                  padding: const EdgeInsets.fromLTRB(16, 0, 16, 24),
                  children: [
                    if (page.items.isEmpty)
                      const Padding(
                        padding: EdgeInsets.symmetric(vertical: 40),
                        child: Text('No hay registros para mostrar.', textAlign: TextAlign.center, style: TextStyle(color: VigiaColors.inkMuted)),
                      ),
                    for (final e in page.items) _EntryTile(entry: e, isMe: e.actorUid == myUid),
                    if (page.nextCursor != null)
                      _LoadMore(onLoad: () => ref.read(historyProvider(key).notifier).loadMore()),
                    if (page.hiddenOlderEntries && page.nextCursor == null)
                      Container(
                        margin: const EdgeInsets.only(top: 12),
                        padding: const EdgeInsets.all(14),
                        decoration: BoxDecoration(color: VigiaColors.attentionSoft, borderRadius: BorderRadius.circular(14)),
                        child: Text(
                          'El plan del responsable muestra el historial desde el ${formatDate(page.visibleSince!.toLocal())}. '
                          'Los registros anteriores se conservan y se pueden ver con un plan que los incluya.',
                          style: const TextStyle(color: VigiaColors.attention, fontWeight: FontWeight.w600),
                        ),
                      ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _LoadMore extends StatefulWidget {
  const _LoadMore({required this.onLoad});
  final Future<void> Function() onLoad;

  @override
  State<_LoadMore> createState() => _LoadMoreState();
}

class _LoadMoreState extends State<_LoadMore> {
  bool _busy = false;
  String? _error;

  Future<void> _load() async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await widget.onLoad();
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.message);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.only(top: 8),
        child: Column(
          children: [
            if (_error != null) Text(_error!, style: const TextStyle(color: VigiaColors.risk)),
            OutlinedButton(onPressed: _busy ? null : _load, child: Text(_busy ? 'Cargando…' : 'Ver registros anteriores')),
          ],
        ),
      );
}

class _EntryTile extends StatelessWidget {
  const _EntryTile({required this.entry, required this.isMe});
  final HistoryEntry entry;
  final bool isMe;

  IconData get _icon => switch (entry.category) {
        'medication' => Icons.medication_outlined,
        'task' => Icons.checklist,
        'position' => Icons.airline_seat_flat_outlined,
        _ => Icons.edit_note,
      };

  @override
  Widget build(BuildContext context) {
    final when = entry.occurredAt.toLocal();
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(color: VigiaColors.surface, borderRadius: BorderRadius.circular(16)),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(_icon, color: VigiaColors.primary),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(entry.description, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
                if (entry.reason != null) Text('Motivo: ${entry.reason}'),
                if (entry.note != null) Text('Observación: ${entry.note}'),
                const SizedBox(height: 2),
                Text(
                  '${formatDate(when)} · ${hhmm(when)} · ${isMe ? 'Tú' : entry.actorName}',
                  style: const TextStyle(fontSize: 14, color: VigiaColors.inkMuted),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
