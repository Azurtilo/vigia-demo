import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/network/api_exception.dart';
import '../../../core/theme/vigia_colors.dart';
import '../../../core/widgets/async_view.dart';
import '../../../core/widgets/form_page.dart';
import '../../today/application/today_providers.dart';
import '../data/care_api.dart';
import '../domain/care_models.dart';
import 'schedule_editor.dart';

/// Crear o editar una tarea del plan de cuidados.
/// Cambios de posición y responsable asignado dependen del plan del responsable del paciente.
class TaskFormScreen extends ConsumerWidget {
  const TaskFormScreen({super.key, required this.patientId, this.taskId});
  final String patientId;
  final String? taskId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final title = taskId == null ? 'Nueva tarea' : 'Editar tarea';
    final agenda = ref.watch(agendaProvider((patientId: patientId, day: null)));
    final tasks = taskId == null ? null : ref.watch(tasksProvider(patientId));
    return Scaffold(
      appBar: AppBar(title: Text(title)),
      body: AsyncView(
        value: agenda,
        onRetry: () => ref.invalidate(agendaProvider((patientId: patientId, day: null))),
        builder: (a) {
          Widget form(CareTask? initial) => _TaskForm(
                patientId: patientId,
                initial: initial,
                positionChanges: a.positionChanges,
                extended: a.extendedCareTracking,
              );
          if (tasks == null) return form(null);
          return AsyncView(
            value: tasks,
            onRetry: () => ref.invalidate(tasksProvider(patientId)),
            builder: (list) {
              final task = list.where((t) => t.id == taskId).firstOrNull;
              return task == null ? const Center(child: Text('Tarea no encontrada.')) : form(task);
            },
          );
        },
      ),
    );
  }
}

class _TaskForm extends ConsumerStatefulWidget {
  const _TaskForm({required this.patientId, required this.positionChanges, required this.extended, this.initial});
  final String patientId;
  final CareTask? initial;
  final bool positionChanges;
  final bool extended;

  @override
  ConsumerState<_TaskForm> createState() => _TaskFormState();
}

class _TaskFormState extends ConsumerState<_TaskForm> {
  final _form = GlobalKey<FormState>();
  late final _title = TextEditingController(text: widget.initial?.title);
  late final _description = TextEditingController(text: widget.initial?.description);
  late String _kind = widget.initial?.kind ?? 'general';
  late String _type = widget.initial?.scheduleType ?? 'fixed';
  late List<String> _times = [...?widget.initial?.schedule?.times];
  late List<int> _days = [...?widget.initial?.schedule?.daysOfWeek];
  late DateTime _start = widget.initial?.startDate ?? DateTime.now();
  late DateTime? _end = widget.initial?.endDate;
  late String? _assignee = widget.initial?.assignedTo;
  String? _timesError;
  String? _error;
  bool _busy = false;

  @override
  void dispose() {
    _title.dispose();
    _description.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final timesOk = _type == 'unscheduled' || _times.isNotEmpty;
    setState(() => _timesError = timesOk ? null : 'Agrega al menos una hora.');
    if (_busy || !_form.currentState!.validate() || !timesOk) return;
    setState(() {
      _busy = true;
      _error = null;
    });
    final draft = CareTaskDraft(
      title: _title.text,
      description: _description.text,
      kind: _kind,
      scheduleType: _type,
      schedule: _type == 'fixed' ? ScheduleSpec(times: _times, daysOfWeek: _days) : null,
      startDate: _start,
      endDate: _end,
      assignedTo: _assignee,
    );
    try {
      final api = ref.read(careApiProvider);
      final body = draft.toJson(forUpdate: widget.initial != null);
      // Sin seguimiento ampliado no se envía responsable (el backend lo rechazaría).
      if (!widget.extended) body.remove('assignedTo');
      widget.initial == null
          ? await api.createTask(widget.patientId, draft)
          : await api.updateTask(widget.patientId, widget.initial!.id, body);
      ref.invalidate(tasksProvider(widget.patientId));
      ref.invalidate(agendaProvider((patientId: widget.patientId, day: null)));
      if (mounted) context.pop();
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.message);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final members = ref.watch(memberNamesProvider(widget.patientId)).value ?? const <String, String>{};
    final isNew = widget.initial == null;
    return Form(
      key: _form,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 32),
        children: [
          if (isNew && widget.positionChanges) ...[
            const Text('Tipo de tarea', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
            const SizedBox(height: 8),
            SegmentedButton<String>(
              segments: const [
                ButtonSegment(value: 'general', label: Text('General')),
                ButtonSegment(value: 'position_change', label: Text('Cambio de posición')),
              ],
              selected: {_kind},
              onSelectionChanged: (s) => setState(() {
                _kind = s.first;
                if (_kind == 'position_change' && _title.text.trim().isEmpty) _title.text = 'Cambio de posición';
              }),
            ),
            const SizedBox(height: 16),
          ],
          TextFormField(
            key: const Key('task-title'),
            controller: _title,
            decoration: const InputDecoration(labelText: 'Nombre de la tarea *', hintText: 'Ej.: Hidratar'),
            maxLength: 120,
            validator: (v) => Validators.required(v, 'Escribe el nombre de la tarea.'),
          ),
          TextFormField(
            controller: _description,
            decoration: const InputDecoration(labelText: 'Descripción (opcional)'),
            maxLength: 1000,
            maxLines: 2,
          ),
          const SizedBox(height: 8),
          SegmentedButton<String>(
            segments: const [
              ButtonSegment(value: 'fixed', label: Text('Con horario'), icon: Icon(Icons.schedule)),
              ButtonSegment(value: 'unscheduled', label: Text('Sin horario'), icon: Icon(Icons.all_inclusive)),
            ],
            selected: {_type},
            onSelectionChanged: (s) => setState(() => _type = s.first),
          ),
          const SizedBox(height: 16),
          if (_type == 'fixed')
            ScheduleEditor(
              times: _times,
              days: _days,
              errorText: _timesError,
              onTimesChanged: (t) => setState(() {
                _times = t;
                _timesError = null;
              }),
              onDaysChanged: (d) => setState(() => _days = d),
            )
          else
            const Text('Se registra cada vez que se hace, desde la pestaña Cuidados.', style: TextStyle(color: VigiaColors.inkMuted)),
          const SizedBox(height: 16),
          if (widget.extended)
            DropdownButtonFormField<String?>(
              initialValue: members.containsKey(_assignee) ? _assignee : null,
              decoration: const InputDecoration(labelText: 'Responsable asignado (opcional)'),
              items: [
                const DropdownMenuItem<String?>(value: null, child: Text('Sin asignar')),
                for (final e in members.entries) DropdownMenuItem<String?>(value: e.key, child: Text(e.value)),
              ],
              onChanged: (v) => setState(() => _assignee = v),
            ),
          const SizedBox(height: 16),
          DateButton(label: 'Inicio', value: _start, onChanged: (d) => setState(() => _start = d ?? _start)),
          const SizedBox(height: 8),
          DateButton(label: 'Término (opcional)', value: _end, allowClear: true, onChanged: (d) => setState(() => _end = d)),
          const SizedBox(height: 24),
          if (_error != null) ...[ErrorBanner(_error!), const SizedBox(height: 16)],
          FilledButton(
            key: const Key('task-save'),
            onPressed: _busy ? null : _submit,
            child: Text(_busy ? 'Guardando…' : (isNew ? 'Crear tarea' : 'Guardar cambios')),
          ),
        ],
      ),
    );
  }
}
