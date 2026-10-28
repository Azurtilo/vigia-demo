import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/network/api_exception.dart';
import '../../../core/theme/vigia_colors.dart';
import '../../../core/widgets/async_view.dart';
import '../../../core/widgets/form_page.dart';
import '../data/care_api.dart';
import '../domain/care_models.dart';
import 'schedule_editor.dart';

/// Registrar o editar un medicamento TAL COMO FUE INDICADO. La app no sugiere ni calcula dosis.
class MedicationFormScreen extends ConsumerWidget {
  const MedicationFormScreen({super.key, required this.patientId, this.medicationId});
  final String patientId;
  final String? medicationId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final title = medicationId == null ? 'Nuevo medicamento' : 'Editar medicamento';
    if (medicationId == null) {
      return Scaffold(appBar: AppBar(title: Text(title)), body: _MedicationForm(patientId: patientId));
    }
    final meds = ref.watch(medicationsProvider(patientId));
    return Scaffold(
      appBar: AppBar(title: Text(title)),
      body: AsyncView(
        value: meds,
        onRetry: () => ref.invalidate(medicationsProvider(patientId)),
        builder: (list) {
          final med = list.where((m) => m.id == medicationId).firstOrNull;
          if (med == null) return const Center(child: Text('Medicamento no encontrado.'));
          return _MedicationForm(patientId: patientId, initial: med);
        },
      ),
    );
  }
}

class _MedicationForm extends ConsumerStatefulWidget {
  const _MedicationForm({required this.patientId, this.initial});
  final String patientId;
  final Medication? initial;

  @override
  ConsumerState<_MedicationForm> createState() => _MedicationFormState();
}

class _MedicationFormState extends ConsumerState<_MedicationForm> {
  final _form = GlobalKey<FormState>();
  late final _name = TextEditingController(text: widget.initial?.name);
  late final _dose = TextEditingController(text: widget.initial?.dose);
  late final _instructions = TextEditingController(text: widget.initial?.instructions);
  late String _type = widget.initial?.scheduleType ?? 'fixed';
  late List<String> _times = [...?widget.initial?.schedule?.times];
  late List<int> _days = [...?widget.initial?.schedule?.daysOfWeek];
  late DateTime _start = widget.initial?.startDate ?? DateTime.now();
  late DateTime? _end = widget.initial?.endDate;
  String? _timesError;
  String? _error;
  bool _busy = false;

  @override
  void dispose() {
    _name.dispose();
    _dose.dispose();
    _instructions.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final timesOk = _type == 'as_needed' || _times.isNotEmpty;
    setState(() => _timesError = timesOk ? null : 'Agrega al menos una hora.');
    if (_busy || !_form.currentState!.validate() || !timesOk) return;
    if (_end != null && _end!.isBefore(DateTime(_start.year, _start.month, _start.day))) {
      setState(() => _error = 'La fecha de término no puede ser anterior a la de inicio.');
      return;
    }
    setState(() {
      _busy = true;
      _error = null;
    });
    final draft = MedicationDraft(
      name: _name.text,
      dose: _dose.text,
      instructions: _instructions.text,
      scheduleType: _type,
      schedule: _type == 'fixed' ? ScheduleSpec(times: _times, daysOfWeek: _days) : null,
      startDate: _start,
      endDate: _end,
    );
    try {
      final api = ref.read(careApiProvider);
      widget.initial == null
          ? await api.createMedication(widget.patientId, draft)
          : await api.updateMedication(widget.patientId, widget.initial!.id, draft.toJson());
      ref.invalidate(medicationsProvider(widget.patientId));
      if (mounted) context.pop();
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.message);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Form(
      key: _form,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 32),
        children: [
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(color: VigiaColors.sky, borderRadius: BorderRadius.circular(14)),
            child: const Text(
              'Registra el medicamento tal como lo indicó el profesional tratante. VIGIA no sugiere ni calcula dosis.',
              style: TextStyle(fontSize: 14),
            ),
          ),
          const SizedBox(height: 16),
          TextFormField(
            key: const Key('med-name'),
            controller: _name,
            decoration: const InputDecoration(labelText: 'Nombre del medicamento *'),
            maxLength: 120,
            validator: (v) => Validators.required(v, 'Escribe el nombre.'),
          ),
          TextFormField(
            key: const Key('med-dose'),
            controller: _dose,
            decoration: const InputDecoration(labelText: 'Dosis indicada *', hintText: 'Ej.: 1 comprimido de 500 mg'),
            maxLength: 200,
            validator: (v) => Validators.required(v, 'Escribe la dosis tal como fue indicada.'),
          ),
          TextFormField(
            controller: _instructions,
            decoration: const InputDecoration(labelText: 'Instrucciones (opcional)', hintText: 'Ej.: con comida'),
            maxLength: 1000,
            maxLines: 2,
          ),
          const SizedBox(height: 8),
          const Text('¿Cuándo se da?', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
          const SizedBox(height: 8),
          SegmentedButton<String>(
            segments: const [
              ButtonSegment(value: 'fixed', label: Text('Horario fijo'), icon: Icon(Icons.schedule)),
              ButtonSegment(value: 'as_needed', label: Text('Si es necesario'), icon: Icon(Icons.pan_tool_alt_outlined)),
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
            const Text(
              'No aparece en la agenda: se registra cada vez que se da, desde la pestaña Medicamentos.',
              style: TextStyle(color: VigiaColors.inkMuted),
            ),
          const SizedBox(height: 16),
          DateButton(label: 'Inicio', value: _start, onChanged: (d) => setState(() => _start = d ?? _start)),
          const SizedBox(height: 8),
          DateButton(label: 'Término (opcional)', value: _end, allowClear: true, onChanged: (d) => setState(() => _end = d)),
          const SizedBox(height: 24),
          if (_error != null) ...[ErrorBanner(_error!), const SizedBox(height: 16)],
          FilledButton(
            key: const Key('med-save'),
            onPressed: _busy ? null : _submit,
            child: Text(_busy ? 'Guardando…' : (widget.initial == null ? 'Registrar medicamento' : 'Guardar cambios')),
          ),
          if (widget.initial != null)
            const Padding(
              padding: EdgeInsets.only(top: 8),
              child: Text(
                'Los cambios aplican desde ahora. Las tomas ya registradas no cambian.',
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 14, color: VigiaColors.inkMuted),
              ),
            ),
        ],
      ),
    );
  }
}
