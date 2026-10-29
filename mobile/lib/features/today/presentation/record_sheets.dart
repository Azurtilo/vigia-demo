import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_exception.dart';
import '../../../core/theme/vigia_colors.dart';
import '../../../core/widgets/form_page.dart';
import '../data/agenda_api.dart';
import '../domain/agenda.dart';

/// Abre una hoja inferior de registro. Devuelve true si se guardó algo.
Future<bool> showRecordSheet(BuildContext context, Widget sheet) async {
  final saved = await showModalBottomSheet<bool>(
    context: context,
    isScrollControlled: true,
    showDragHandle: true,
    backgroundColor: VigiaColors.surface,
    builder: (_) => Padding(
      padding: EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom),
      child: sheet,
    ),
  );
  return saved ?? false;
}

/// Hora local "HH:mm" de un instante.
String hhmm(DateTime t) {
  final l = t.toLocal();
  return '${l.hour.toString().padLeft(2, '0')}:${l.minute.toString().padLeft(2, '0')}';
}

/// Base común: título, contenido, error y botón Guardar con estado "Guardando…".
abstract class _RecordSheetState<T extends ConsumerStatefulWidget> extends ConsumerState<T> {
  bool busy = false;
  String? error;

  /// Valida y guarda. Devuelve un mensaje de error para mostrar, o null si salió bien.
  Future<String?> save();

  Future<void> submit() async {
    if (busy) return;
    setState(() {
      busy = true;
      error = null;
    });
    String? message;
    try {
      message = await save();
    } on ApiException catch (e) {
      message = e.message;
    }
    if (!mounted) return;
    if (message == null) {
      Navigator.pop(context, true);
    } else {
      setState(() {
        busy = false;
        error = message;
      });
    }
  }

  Widget frame({required String title, String? subtitle, required List<Widget> children}) {
    return SafeArea(
      child: SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(20, 0, 20, 20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(title, style: Theme.of(context).textTheme.headlineMedium?.copyWith(fontSize: 24)),
            if (subtitle != null) Text(subtitle, style: const TextStyle(fontSize: 16, color: VigiaColors.inkMuted)),
            const SizedBox(height: 16),
            ...children,
            const SizedBox(height: 16),
            if (error != null) ...[ErrorBanner(error!), const SizedBox(height: 12)],
            FilledButton(
              key: const Key('record-save'),
              onPressed: busy ? null : submit,
              child: Text(busy ? 'Guardando…' : 'Guardar registro'),
            ),
            const SizedBox(height: 8),
            const Text(
              'Quedará registrado a tu nombre.',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 14, color: VigiaColors.inkMuted),
            ),
          ],
        ),
      ),
    );
  }
}

/// Opción grande seleccionable (área táctil ≥ 56 px, ícono + texto: no solo color).
class ChoiceTile extends StatelessWidget {
  const ChoiceTile({
    super.key,
    required this.label,
    required this.icon,
    required this.selected,
    required this.onTap,
    this.color = VigiaColors.primary,
    this.background = VigiaColors.primarySoft,
  });

  final String label;
  final IconData icon;
  final bool selected;
  final VoidCallback onTap;
  final Color color;
  final Color background;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Semantics(
        selected: selected,
        button: true,
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(16),
          child: Container(
            constraints: const BoxConstraints(minHeight: 56),
            padding: const EdgeInsets.symmetric(horizontal: 16),
            decoration: BoxDecoration(
              color: selected ? background : VigiaColors.surface,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: selected ? color : VigiaColors.outline, width: 2),
            ),
            child: Row(
              children: [
                Icon(selected ? Icons.radio_button_checked : Icons.radio_button_off, color: selected ? color : VigiaColors.inkMuted),
                const SizedBox(width: 12),
                Icon(icon, color: color),
                const SizedBox(width: 10),
                Expanded(child: Text(label, style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w700))),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

// ---------------------------------------------------------------------------------------------

/// Registrar una toma programada: dada, dada con retraso (hora y motivo) o no dada (motivo).
class DoseSheet extends ConsumerStatefulWidget {
  const DoseSheet({super.key, required this.patientId, required this.item, required this.day, this.correctLogId});
  final String patientId;
  final MedicationItem item;
  final DateTime day; // día local de la agenda

  /// Si se indica, la hoja CORRIGE ese registro en vez de crear uno nuevo.
  final String? correctLogId;

  @override
  ConsumerState<DoseSheet> createState() => _DoseSheetState();
}

class _DoseSheetState extends _RecordSheetState<DoseSheet> {
  String status = 'given';
  final reason = TextEditingController();
  TimeOfDay time = TimeOfDay.now();

  @override
  void dispose() {
    reason.dispose();
    super.dispose();
  }

  @override
  Future<String?> save() async {
    final needsReason = status != 'given';
    if (needsReason && reason.text.trim().isEmpty) return 'Indica el motivo.';
    DateTime? actual;
    if (status == 'delayed') {
      actual = DateTime(widget.day.year, widget.day.month, widget.day.day, time.hour, time.minute);
      if (actual.isAfter(DateTime.now().add(const Duration(minutes: 2)))) {
        return 'La hora en que se dio no puede estar en el futuro.';
      }
    }
    final api = ref.read(agendaApiProvider);
    final why = needsReason ? reason.text.trim() : null;
    if (widget.correctLogId != null) {
      // "Dada" sin hora nueva: el backend conserva la hora ya registrada.
      await api.correctDose(widget.patientId, widget.correctLogId!, status: status, actualAt: actual, reason: why);
    } else {
      await api.recordDose(
        widget.patientId,
        widget.item.medicationId,
        status: status,
        scheduledAt: widget.item.scheduledAt,
        actualAt: actual, // "dada": el backend usa la hora actual
        reason: why,
      );
    }
    return null;
  }

  @override
  Widget build(BuildContext context) {
    final item = widget.item;
    return frame(
      title: '${widget.correctLogId == null ? '' : 'Corregir: '}${item.name}${item.localTime == null ? '' : ' · ${item.localTime}'}',
      subtitle: [item.dose, ?item.instructions].join(' · '),
      children: [
        const Text('¿Qué pasó con esta toma?', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
        const SizedBox(height: 10),
        ChoiceTile(
          label: 'Dada a tiempo',
          icon: Icons.check,
          selected: status == 'given',
          color: VigiaColors.mintInk,
          background: VigiaColors.mint,
          onTap: () => setState(() => status = 'given'),
        ),
        ChoiceTile(
          label: 'Dada con retraso',
          icon: Icons.schedule,
          selected: status == 'delayed',
          color: VigiaColors.attention,
          background: VigiaColors.attentionSoft,
          onTap: () => setState(() => status = 'delayed'),
        ),
        ChoiceTile(
          label: 'No se dio',
          icon: Icons.block,
          selected: status == 'omitted',
          color: VigiaColors.inkMuted,
          background: const Color(0xFFECEAF2),
          onTap: () => setState(() => status = 'omitted'),
        ),
        if (status == 'delayed')
          OutlinedButton.icon(
            onPressed: () async {
              final picked = await showTimePicker(context: context, initialTime: time, helpText: 'Hora en que se dio');
              if (picked != null) setState(() => time = picked);
            },
            icon: const Icon(Icons.access_time),
            label: Text('Se dio a las ${time.hour.toString().padLeft(2, '0')}:${time.minute.toString().padLeft(2, '0')}'),
          ),
        if (status != 'given') ...[
          const SizedBox(height: 12),
          TextField(
            key: const Key('record-reason'),
            controller: reason,
            decoration: const InputDecoration(labelText: 'Motivo (obligatorio)'),
            maxLength: 500,
            maxLines: 2,
          ),
        ],
      ],
    );
  }
}

// ---------------------------------------------------------------------------------------------

/// Registrar una tarea. "No se realizó" y las observaciones dependen del plan del responsable.
class TaskSheet extends ConsumerStatefulWidget {
  const TaskSheet({
    super.key,
    required this.patientId,
    required this.item,
    required this.extendedTracking,
    bool? allowSkip,
    this.correctLogId,
  }) : allowSkip = allowSkip ?? extendedTracking;
  final String patientId;
  final TaskItem item;
  final bool extendedTracking;

  /// Si se indica, la hoja CORRIGE ese registro en vez de crear uno nuevo.
  final String? correctLogId;

  /// "No se realizó" solo existe para tareas con horario y con seguimiento ampliado.
  final bool allowSkip;

  @override
  ConsumerState<TaskSheet> createState() => _TaskSheetState();
}

class _TaskSheetState extends _RecordSheetState<TaskSheet> {
  String status = 'done';
  String? position;
  final positionOther = TextEditingController();
  final reason = TextEditingController();
  final note = TextEditingController();

  @override
  void dispose() {
    positionOther.dispose();
    reason.dispose();
    note.dispose();
    super.dispose();
  }

  @override
  Future<String?> save() async {
    final item = widget.item;
    if (status == 'skipped' && reason.text.trim().isEmpty) return 'Indica por qué no se realizó.';
    if (item.isPositionChange && status == 'done') {
      if (position == null) return 'Indica a qué posición se cambió.';
      if (position == 'other' && positionOther.text.trim().isEmpty) return 'Describe la posición.';
    }
    final api = ref.read(agendaApiProvider);
    final why = status == 'skipped' ? reason.text.trim() : null;
    final observation = note.text.trim().isEmpty ? null : note.text.trim();
    final pos = status == 'done' ? position : null;
    final posOther = status == 'done' && position == 'other' ? positionOther.text.trim() : null;
    if (widget.correctLogId != null) {
      await api.correctTask(widget.patientId, widget.correctLogId!,
          status: status, reason: why, note: observation, position: pos, positionOther: posOther);
    } else {
      await api.recordTask(widget.patientId, item.taskId!,
          status: status, scheduledAt: item.scheduledAt, reason: why, note: observation, position: pos, positionOther: posOther);
    }
    return null;
  }

  @override
  Widget build(BuildContext context) {
    final item = widget.item;
    return frame(
      title: '${widget.correctLogId == null ? '' : 'Corregir: '}${item.title}${item.localTime == null ? '' : ' · ${item.localTime}'}',
      subtitle: item.description,
      children: [
        ChoiceTile(
          label: 'Realizada',
          icon: Icons.check,
          selected: status == 'done',
          color: VigiaColors.mintInk,
          background: VigiaColors.mint,
          onTap: () => setState(() => status = 'done'),
        ),
        if (widget.allowSkip)
          ChoiceTile(
            label: 'No se realizó',
            icon: Icons.block,
            selected: status == 'skipped',
            color: VigiaColors.inkMuted,
            background: const Color(0xFFECEAF2),
            onTap: () => setState(() => status = 'skipped'),
          ),
        if (item.isPositionChange && status == 'done') ...[
          const SizedBox(height: 6),
          PositionPicker(value: position, onChanged: (p) => setState(() => position = p), otherController: positionOther),
        ],
        if (status == 'skipped')
          TextField(
            key: const Key('record-reason'),
            controller: reason,
            decoration: const InputDecoration(labelText: 'Motivo (obligatorio)'),
            maxLength: 500,
          ),
        if (widget.extendedTracking)
          TextField(controller: note, decoration: const InputDecoration(labelText: 'Observación (opcional)'), maxLength: 1000, maxLines: 2),
      ],
    );
  }
}

// ---------------------------------------------------------------------------------------------

/// Cambio de posición sin tarea programada (solo si el plan del responsable lo incluye).
class PositionSheet extends ConsumerStatefulWidget {
  const PositionSheet({super.key, required this.patientId, required this.extendedTracking});
  final String patientId;
  final bool extendedTracking;

  @override
  ConsumerState<PositionSheet> createState() => _PositionSheetState();
}

class _PositionSheetState extends _RecordSheetState<PositionSheet> {
  String? position;
  final positionOther = TextEditingController();
  final note = TextEditingController();

  @override
  void dispose() {
    positionOther.dispose();
    note.dispose();
    super.dispose();
  }

  @override
  Future<String?> save() async {
    if (position == null) return 'Indica a qué posición se cambió.';
    if (position == 'other' && positionOther.text.trim().isEmpty) return 'Describe la posición.';
    await ref.read(agendaApiProvider).recordPosition(
          widget.patientId,
          position: position!,
          positionOther: position == 'other' ? positionOther.text.trim() : null,
          note: note.text.trim().isEmpty ? null : note.text.trim(),
        );
    return null;
  }

  @override
  Widget build(BuildContext context) {
    return frame(
      title: 'Cambio de posición',
      subtitle: 'Se registra con la hora actual.',
      children: [
        PositionPicker(value: position, onChanged: (p) => setState(() => position = p), otherController: positionOther),
        if (widget.extendedTracking)
          TextField(controller: note, decoration: const InputDecoration(labelText: 'Observación (opcional)'), maxLength: 1000),
      ],
    );
  }
}

class PositionPicker extends StatelessWidget {
  const PositionPicker({super.key, required this.value, required this.onChanged, required this.otherController});
  final String? value;
  final ValueChanged<String> onChanged;
  final TextEditingController otherController;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        const Text('¿A qué posición se cambió?', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
        const SizedBox(height: 10),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
            for (final entry in positionLabels.entries)
              ChoiceChip(
                label: Text(entry.value),
                selected: value == entry.key,
                onSelected: (_) => onChanged(entry.key),
                labelStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700),
                materialTapTargetSize: MaterialTapTargetSize.padded,
              ),
          ],
        ),
        if (value == 'other') ...[
          const SizedBox(height: 12),
          TextField(
            controller: otherController,
            decoration: const InputDecoration(labelText: 'Describe la posición'),
            maxLength: 100,
          ),
        ],
        const SizedBox(height: 8),
      ],
    );
  }
}
