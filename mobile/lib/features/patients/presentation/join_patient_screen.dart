import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/network/api_exception.dart';
import '../../../core/router/app_router.dart';
import '../../../core/widgets/form_page.dart';
import '../application/patients_providers.dart';
import '../data/patients_api.dart';

/// Unirse a un paciente con el código que compartió su responsable.
class JoinPatientScreen extends ConsumerStatefulWidget {
  const JoinPatientScreen({super.key});

  @override
  ConsumerState<JoinPatientScreen> createState() => _JoinPatientScreenState();
}

class _JoinPatientScreenState extends ConsumerState<JoinPatientScreen> {
  final _form = GlobalKey<FormState>();
  final _code = TextEditingController();
  bool _busy = false;
  String? _error;

  @override
  void dispose() {
    _code.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (_busy || !_form.currentState!.validate()) return;
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final patient = await ref.read(patientsApiProvider).acceptInvitation(_code.text);
      if (!mounted) return;
      refreshPatients(ref, patientId: patient.id);
      context.pushReplacement(Routes.patientDetail(patient.id));
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.message);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return FormPage(
      title: 'Unirme con código',
      subtitle: 'Escribe el código que te compartió la persona responsable del paciente. Tu cuenta debe usar el mismo correo al que se envió la invitación.',
      showBack: true,
      children: [
        Form(
          key: _form,
          child: TextFormField(
            key: const Key('join-code'),
            controller: _code,
            decoration: const InputDecoration(labelText: 'Código de invitación', hintText: 'ABCD-EFGH-JKMN-PQRS-TUVW'),
            textCapitalization: TextCapitalization.characters,
            inputFormatters: [FilteringTextInputFormatter.allow(RegExp(r'[A-Za-z0-9\- ]'))],
            maxLength: 29,
            validator: (v) => (v?.replaceAll(RegExp(r'[^A-Za-z0-9]'), '').length ?? 0) == 20
                ? null
                : 'El código tiene 20 letras y números (5 grupos de 4).',
          ),
        ),
        const SizedBox(height: 12),
        if (_error != null) ...[ErrorBanner(_error!), const SizedBox(height: 16)],
        FilledButton(onPressed: _busy ? null : _submit, child: Text(_busy ? 'Verificando…' : 'Unirme')),
      ],
    );
  }
}
