import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/widgets/form_page.dart';
import '../application/session_controller.dart';

/// Paso 2 del registro: crea el perfil en VIGIA (POST /v1/auth/register).
/// También aparece si la cuenta de Firebase existe pero el perfil no se alcanzó a crear.
class CompleteProfileScreen extends ConsumerStatefulWidget {
  const CompleteProfileScreen({super.key});

  @override
  ConsumerState<CompleteProfileScreen> createState() => _CompleteProfileScreenState();
}

class _CompleteProfileScreenState extends ConsumerState<CompleteProfileScreen> {
  final _form = GlobalKey<FormState>();
  final _name = TextEditingController();
  bool _busy = false;
  String? _error;

  @override
  void dispose() {
    _name.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (_busy || !_form.currentState!.validate()) return;
    setState(() {
      _busy = true;
      _error = null;
    });
    final error = await ref.read(sessionControllerProvider.notifier).completeProfile(_name.text);
    if (mounted) {
      setState(() {
        _busy = false;
        _error = error;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final session = ref.watch(sessionControllerProvider);
    final email = session is NeedsProfile ? session.email : null;
    return FormPage(
      title: 'Completa tu perfil',
      subtitle: email == null ? 'Paso 2 de 2' : 'Paso 2 de 2 · $email',
      children: [
        Form(
          key: _form,
          child: TextFormField(
            key: const Key('profile-name'),
            controller: _name,
            decoration: const InputDecoration(
              labelText: '¿Cómo te llamas?',
              helperText: 'Así te verán las otras personas que cuidan contigo.',
            ),
            textCapitalization: TextCapitalization.words,
            maxLength: 80,
            validator: (v) => Validators.required(v, 'Escribe tu nombre.'),
          ),
        ),
        const SizedBox(height: 12),
        if (_error != null) ...[ErrorBanner(_error!), const SizedBox(height: 16)],
        FilledButton(onPressed: _busy ? null : _submit, child: Text(_busy ? 'Guardando…' : 'Comenzar')),
        const SizedBox(height: 12),
        TextButton(
          onPressed: _busy ? null : () => ref.read(sessionControllerProvider.notifier).signOut(),
          child: const Text('Usar otra cuenta'),
        ),
      ],
    );
  }
}
