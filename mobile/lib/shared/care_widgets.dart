import 'package:flutter/material.dart';

String when(dynamic raw) {
  if (raw == null || raw == '') return 'Sin horario';
  final d = DateTime.tryParse(raw.toString())?.toLocal();
  if (d == null) return raw.toString();
  return '${d.day.toString().padLeft(2, '0')}/${d.month.toString().padLeft(2, '0')} ${d.hour.toString().padLeft(2, '0')}:${d.minute.toString().padLeft(2, '0')}';
}

String postureName(dynamic p) =>
    {
      'supina': 'Boca arriba',
      'lateral-izquierda': 'Lateral izquierda',
      'lateral-derecha': 'Lateral derecha',
      'indeterminada': 'No se puede determinar',
    }[p] ??
    p.toString();
void notice(BuildContext context, Object error) {
  if (context.mounted) {
    ScaffoldMessenger.of(context)
        .showSnackBar(SnackBar(content: Text(error.toString())));
  }
}

Future<bool> confirm(BuildContext context, String title, String detail) async =>
    await showDialog<bool>(
      context: context,
      builder: (c) => AlertDialog(
        title: Text(title),
        content: Text(detail),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(c, false),
            child: const Text('Volver'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(c, true),
            child: const Text('Confirmar'),
          ),
        ],
      ),
    ) ??
    false;

class FormFieldSpec {
  final String key, label;
  final bool required, multiline;
  const FormFieldSpec(
    this.key,
    this.label, {
    this.required = false,
    this.multiline = false,
  });
}

Future<Map<String, dynamic>?> editForm(
  BuildContext context,
  String title,
  List<FormFieldSpec> fields, {
  Map<String, dynamic> initial = const {},
  bool? active,
}) => Navigator.push(
  context,
  MaterialPageRoute(
    builder: (_) => EditScreen(
      title: title,
      fields: fields,
      initial: initial,
      active: active,
    ),
  ),
);

class EditScreen extends StatefulWidget {
  final String title;
  final List<FormFieldSpec> fields;
  final Map<String, dynamic> initial;
  final bool? active;
  const EditScreen({
    super.key,
    required this.title,
    required this.fields,
    required this.initial,
    this.active,
  });
  @override
  State<EditScreen> createState() => _EditScreenState();
}

class _EditScreenState extends State<EditScreen> {
  final form = GlobalKey<FormState>();
  late Map<String, TextEditingController> controllers;
  late bool active;
  @override
  void initState() {
    super.initState();
    controllers = {
      for (final f in widget.fields)
        f.key: TextEditingController(
          text: widget.initial[f.key]?.toString() ?? '',
        ),
    };
    active = widget.active ?? true;
  }

  @override
  void dispose() {
    for (final c in controllers.values) {
      c.dispose();
    }
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: Text(widget.title)),
    body: Form(
      key: form,
      child: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          for (final f in widget.fields)
            Padding(
              padding: const EdgeInsets.only(bottom: 16),
              child: TextFormField(
                controller: controllers[f.key],
                decoration: InputDecoration(labelText: f.label),
                minLines: f.multiline ? 3 : 1,
                maxLines: f.multiline ? 5 : 1,
                validator: (v) => f.required && (v == null || v.trim().isEmpty)
                    ? 'Completa este campo.'
                    : null,
              ),
            ),
          if (widget.active != null)
            SwitchListTile(
              title: const Text('Programación activa'),
              value: active,
              onChanged: (v) => setState(() => active = v),
            ),
          FilledButton(
            onPressed: () {
              if (form.currentState!.validate()) {
                Navigator.pop(context, <String, dynamic>{
                  for (final e in controllers.entries)
                    e.key: e.value.text.trim(),
                  if (widget.initial.containsKey('version'))
                    'version': widget.initial['version'],
                  if (widget.active != null) 'active': active,
                });
              }
            },
            child: const Text('Continuar'),
          ),
        ],
      ),
    ),
  );
}

const patientFields = [
  FormFieldSpec('name', 'Nombre del paciente', required: true),
  FormFieldSpec('birth_date', 'Nacimiento (AAAA-MM-DD)'),
  FormFieldSpec('notes', 'Información relevante', multiline: true),
  FormFieldSpec('contact_name', 'Contacto de emergencia'),
  FormFieldSpec('contact_phone', 'Teléfono de contacto'),
  FormFieldSpec('contact_relation', 'Relación con el paciente'),
];
