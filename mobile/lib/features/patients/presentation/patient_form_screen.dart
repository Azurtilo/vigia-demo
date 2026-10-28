import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/network/api_exception.dart';
import '../../../core/router/app_router.dart';
import '../../../core/theme/vigia_colors.dart';
import '../../../core/widgets/async_view.dart';
import '../../../core/widgets/form_page.dart';
import '../application/patients_providers.dart';
import '../data/patients_api.dart';
import '../domain/patient.dart';

/// Registrar (sin [patientId]) o editar un paciente. Solo datos necesarios para el cuidado.
class PatientFormScreen extends ConsumerWidget {
  const PatientFormScreen({super.key, this.patientId});
  final String? patientId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    if (patientId == null) return const _PatientForm(initial: null);
    final patient = ref.watch(patientProvider(patientId!));
    return Scaffold(
      appBar: AppBar(title: const Text('Editar paciente')),
      body: AsyncView(
        value: patient,
        onRetry: () => ref.invalidate(patientProvider(patientId!)),
        builder: (p) => _PatientForm(initial: p, embedded: true),
      ),
    );
  }
}

class _PatientForm extends ConsumerStatefulWidget {
  const _PatientForm({required this.initial, this.embedded = false});
  final Patient? initial;
  final bool embedded;

  @override
  ConsumerState<_PatientForm> createState() => _PatientFormState();
}

class _ContactFields {
  _ContactFields([EmergencyContact? c])
      : name = TextEditingController(text: c?.name),
        phone = TextEditingController(text: c?.phone),
        relation = TextEditingController(text: c?.relation);
  final TextEditingController name;
  final TextEditingController phone;
  final TextEditingController relation;

  void dispose() {
    name.dispose();
    phone.dispose();
    relation.dispose();
  }
}

class _PatientFormState extends ConsumerState<_PatientForm> {
  final _form = GlobalKey<FormState>();
  late final _name = TextEditingController(text: widget.initial?.displayName);
  late final _mobility = TextEditingController(text: widget.initial?.mobility);
  late final _careNeeds = TextEditingController(text: widget.initial?.careNeeds);
  late final _notes = TextEditingController(text: widget.initial?.notes);
  final _allergyInput = TextEditingController();
  late final List<String> _allergies = [...?widget.initial?.allergies];
  late final List<_ContactFields> _contacts = [
    for (final c in widget.initial?.emergencyContacts ?? const <EmergencyContact>[]) _ContactFields(c),
  ];
  late DateTime? _birthDate = widget.initial?.birthDate;
  bool _busy = false;
  String? _error;

  static final _phone = RegExp(r'^\+?[0-9 ]{6,20}$');

  @override
  void dispose() {
    for (final c in [_name, _mobility, _careNeeds, _notes, _allergyInput]) {
      c.dispose();
    }
    for (final c in _contacts) {
      c.dispose();
    }
    super.dispose();
  }

  void _addAllergy() {
    final value = _allergyInput.text.trim();
    if (value.isEmpty || _allergies.contains(value) || _allergies.length >= 20) return;
    setState(() {
      _allergies.add(value);
      _allergyInput.clear();
    });
  }

  Future<void> _pickBirthDate() async {
    final now = DateTime.now();
    final picked = await showDatePicker(
      context: context,
      initialDate: _birthDate ?? DateTime(now.year - 70),
      firstDate: DateTime(1900),
      lastDate: now,
      helpText: 'Fecha de nacimiento',
    );
    if (picked != null) setState(() => _birthDate = picked);
  }

  Future<void> _submit() async {
    if (_busy || !_form.currentState!.validate()) return;
    setState(() {
      _busy = true;
      _error = null;
    });
    final draft = PatientDraft(
      displayName: _name.text,
      birthDate: _birthDate,
      mobility: _mobility.text,
      careNeeds: _careNeeds.text,
      notes: _notes.text,
      allergies: _allergies,
      emergencyContacts: [
        for (final c in _contacts)
          EmergencyContact(
            name: c.name.text.trim(),
            phone: c.phone.text.trim(),
            relation: c.relation.text.trim().isEmpty ? null : c.relation.text.trim(),
          ),
      ],
    );
    try {
      final api = ref.read(patientsApiProvider);
      final saved = widget.initial == null ? await api.create(draft) : await api.update(widget.initial!.id, draft);
      if (!mounted) return;
      refreshPatients(ref, patientId: saved.id);
      if (widget.initial == null) {
        context.pushReplacement(Routes.patientDetail(saved.id));
      } else {
        context.pop();
      }
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.message);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final isNew = widget.initial == null;
    final form = Form(
      key: _form,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 32),
        children: [
          const _Section('Datos básicos'),
          TextFormField(
            key: const Key('patient-name'),
            controller: _name,
            decoration: const InputDecoration(
              labelText: 'Nombre o identificador *',
              helperText: 'Puede ser un apodo, por ejemplo "Abuela Rosa".',
            ),
            textCapitalization: TextCapitalization.words,
            maxLength: 80,
            validator: (v) => Validators.required(v, 'Escribe un nombre o identificador.'),
          ),
          const SizedBox(height: 8),
          OutlinedButton.icon(
            onPressed: _pickBirthDate,
            icon: const Icon(Icons.cake_outlined),
            label: Text(
              _birthDate == null
                  ? 'Fecha de nacimiento (opcional)'
                  : 'Nació el ${_birthDate!.day.toString().padLeft(2, '0')}-${_birthDate!.month.toString().padLeft(2, '0')}-${_birthDate!.year}',
            ),
          ),
          if (_birthDate != null)
            TextButton(onPressed: () => setState(() => _birthDate = null), child: const Text('Quitar fecha')),
          const _Section('Para organizar el cuidado (opcional)'),
          TextFormField(
            controller: _mobility,
            decoration: const InputDecoration(labelText: 'Movilidad y dependencia', hintText: 'Ej.: camina con andador'),
            maxLines: 2,
            maxLength: 500,
          ),
          const SizedBox(height: 8),
          TextFormField(
            controller: _careNeeds,
            decoration: const InputDecoration(labelText: 'Necesidades de cuidado'),
            maxLines: 3,
            maxLength: 1000,
          ),
          const SizedBox(height: 8),
          TextFormField(controller: _notes, decoration: const InputDecoration(labelText: 'Observaciones'), maxLines: 3, maxLength: 2000),
          const _Section('Alergias relevantes'),
          Row(
            children: [
              Expanded(
                child: TextField(
                  key: const Key('allergy-input'),
                  controller: _allergyInput,
                  decoration: const InputDecoration(labelText: 'Agregar alergia'),
                  maxLength: 100,
                  onSubmitted: (_) => _addAllergy(),
                ),
              ),
              const SizedBox(width: 8),
              Padding(
                padding: const EdgeInsets.only(bottom: 20),
                child: IconButton.filledTonal(tooltip: 'Agregar alergia', onPressed: _addAllergy, icon: const Icon(Icons.add)),
              ),
            ],
          ),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              for (final a in _allergies)
                InputChip(
                  label: Text(a),
                  backgroundColor: VigiaColors.riskSoft,
                  labelStyle: const TextStyle(color: VigiaColors.risk, fontWeight: FontWeight.w700),
                  deleteButtonTooltipMessage: 'Quitar $a',
                  onDeleted: () => setState(() => _allergies.remove(a)),
                ),
            ],
          ),
          const _Section('Contactos de emergencia (hasta 3)'),
          for (var i = 0; i < _contacts.length; i++) _contactCard(i),
          if (_contacts.length < 3)
            OutlinedButton.icon(
              onPressed: () => setState(() => _contacts.add(_ContactFields())),
              icon: const Icon(Icons.person_add_alt),
              label: const Text('Agregar contacto'),
            ),
          const SizedBox(height: 24),
          if (_error != null) ...[ErrorBanner(_error!), const SizedBox(height: 16)],
          FilledButton(
            key: const Key('patient-save'),
            onPressed: _busy ? null : _submit,
            child: Text(_busy ? 'Guardando…' : (isNew ? 'Registrar paciente' : 'Guardar cambios')),
          ),
        ],
      ),
    );
    if (widget.embedded) return form;
    return Scaffold(appBar: AppBar(title: const Text('Nuevo paciente')), body: form);
  }

  Widget _contactCard(int i) {
    final c = _contacts[i];
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(color: VigiaColors.surface, borderRadius: BorderRadius.circular(14)),
      child: Column(
        children: [
          Row(
            children: [
              Text('Contacto ${i + 1}', style: const TextStyle(fontWeight: FontWeight.w700)),
              const Spacer(),
              IconButton(
                tooltip: 'Quitar contacto ${i + 1}',
                icon: const Icon(Icons.delete_outline),
                onPressed: () => setState(() => _contacts.removeAt(i).dispose()),
              ),
            ],
          ),
          TextFormField(
            controller: c.name,
            decoration: const InputDecoration(labelText: 'Nombre *'),
            maxLength: 80,
            validator: (v) => Validators.required(v, 'Escribe el nombre del contacto.'),
          ),
          TextFormField(
            controller: c.phone,
            decoration: const InputDecoration(labelText: 'Teléfono *', hintText: '+56 9 1234 5678'),
            keyboardType: TextInputType.phone,
            validator: (v) => _phone.hasMatch(v?.trim() ?? '') ? null : 'Usa solo números, espacios y + (6 a 20).',
          ),
          const SizedBox(height: 12),
          TextFormField(controller: c.relation, decoration: const InputDecoration(labelText: 'Relación (opcional)'), maxLength: 40),
        ],
      ),
    );
  }
}

class _Section extends StatelessWidget {
  const _Section(this.title);
  final String title;

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.only(top: 20, bottom: 10),
        child: Text(title, style: Theme.of(context).textTheme.titleLarge),
      );
}
