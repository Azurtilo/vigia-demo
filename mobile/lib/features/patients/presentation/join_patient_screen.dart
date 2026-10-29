import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/network/api_exception.dart';
import '../../../core/router/app_router.dart';
import '../../../core/theme/vigia_colors.dart';
import '../../../core/widgets/form_page.dart';
import '../../auth/data/auth_repository.dart';
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

  /// El backend exige el correo verificado para aceptar invitaciones (en producción, QA-2026-10-28-01).
  bool _needsVerification = false;
  String? _verificationNote;

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
      if (!mounted) return;
      setState(() {
        if (e.code == 'email_not_verified') {
          _needsVerification = true;
          _verificationNote = null;
        } else {
          _error = e.message;
        }
      });
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  /// «Ya lo verifiqué»: renueva el token y, si el correo ya está verificado, reintenta unirse.
  Future<void> _checkVerified() async {
    setState(() {
      _busy = true;
      _verificationNote = null;
    });
    try {
      final verified = await ref.read(authRepositoryProvider).refreshEmailVerified();
      if (!mounted) return;
      if (!verified) {
        setState(() => _verificationNote = 'Tu correo aún no aparece verificado. Abre el enlace que te enviamos '
            '(revisa también la carpeta de spam) y vuelve a intentarlo.');
        return;
      }
      setState(() => _needsVerification = false);
    } on AuthFailure catch (e) {
      if (mounted) setState(() => _verificationNote = e.message);
      return;
    } finally {
      if (mounted) setState(() => _busy = false);
    }
    await _submit();
  }

  Future<void> _resend() async {
    try {
      await ref.read(authRepositoryProvider).sendEmailVerification();
      if (mounted) setState(() => _verificationNote = 'Te enviamos otro correo de verificación.');
    } on AuthFailure catch (e) {
      if (mounted) setState(() => _verificationNote = e.message);
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
        if (_needsVerification)
          _VerifyEmailCard(
            busy: _busy,
            note: _verificationNote,
            onVerified: _checkVerified,
            onResend: _resend,
          )
        else
          FilledButton(onPressed: _busy ? null : _submit, child: Text(_busy ? 'Verificando…' : 'Unirme')),
      ],
    );
  }
}

class _VerifyEmailCard extends StatelessWidget {
  const _VerifyEmailCard({required this.busy, required this.note, required this.onVerified, required this.onResend});
  final bool busy;
  final String? note;
  final VoidCallback onVerified;
  final VoidCallback onResend;

  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(color: VigiaColors.attentionSoft, borderRadius: BorderRadius.circular(18)),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text(
              'Verifica tu correo',
              style: TextStyle(color: VigiaColors.attention, fontSize: 18, fontWeight: FontWeight.w800),
            ),
            const SizedBox(height: 6),
            const Text(
              'Para unirte a un paciente, confirma que el correo es tuyo: abre el enlace que te enviamos '
              'al crear la cuenta y vuelve aquí.',
            ),
            if (note != null) ...[
              const SizedBox(height: 10),
              Text(note!, style: const TextStyle(fontWeight: FontWeight.w700)),
            ],
            const SizedBox(height: 14),
            FilledButton(
              onPressed: busy ? null : onVerified,
              child: Text(busy ? 'Comprobando…' : 'Ya lo verifiqué'),
            ),
            TextButton(onPressed: busy ? null : onResend, child: const Text('Reenviar correo')),
          ],
        ),
      );
}
