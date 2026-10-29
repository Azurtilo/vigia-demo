import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/widgets/form_page.dart';
import '../data/auth_repository.dart';

/// Paso 1 del registro: correo y contraseña (Firebase).
/// El paso 2 (nombre) es "Completar perfil", al que la app lleva sola.
class CreateAccountScreen extends ConsumerStatefulWidget {
  const CreateAccountScreen({super.key});

  @override
  ConsumerState<CreateAccountScreen> createState() => _CreateAccountScreenState();
}

class _CreateAccountScreenState extends ConsumerState<CreateAccountScreen> {
  final _form = GlobalKey<FormState>();
  final _email = TextEditingController();
  final _password = TextEditingController();
  final _confirm = TextEditingController();
  bool _busy = false;
  String? _error;

  @override
  void dispose() {
    _email.dispose();
    _password.dispose();
    _confirm.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (_busy || !_form.currentState!.validate()) return;
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final auth = ref.read(authRepositoryProvider);
      await auth.createAccount(email: _email.text, password: _password.text);
      // Para unirse a un paciente se necesita el correo verificado (en producción). Si el envío
      // falla, se puede reenviar desde «Unirme con código».
      unawaited(auth.sendEmailVerification().catchError((Object _) {}));
    } on AuthFailure catch (e) {
      if (mounted) setState(() => _error = e.message);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return FormPage(
      title: 'Crear cuenta',
      subtitle: 'Paso 1 de 2 · Después te pediremos tu nombre.',
      showBack: true,
      children: [
        Form(
          key: _form,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              TextFormField(
                key: const Key('create-email'),
                controller: _email,
                decoration: const InputDecoration(labelText: 'Correo electrónico'),
                keyboardType: TextInputType.emailAddress,
                autofillHints: const [AutofillHints.email],
                validator: Validators.email,
              ),
              const SizedBox(height: 16),
              TextFormField(
                key: const Key('create-password'),
                controller: _password,
                decoration: const InputDecoration(labelText: 'Contraseña', helperText: 'Al menos 8 caracteres'),
                obscureText: true,
                autofillHints: const [AutofillHints.newPassword],
                validator: Validators.password,
              ),
              const SizedBox(height: 16),
              TextFormField(
                key: const Key('create-confirm'),
                controller: _confirm,
                decoration: const InputDecoration(labelText: 'Repite la contraseña'),
                obscureText: true,
                validator: (v) => v != _password.text ? 'Las contraseñas no coinciden.' : null,
              ),
            ],
          ),
        ),
        const SizedBox(height: 20),
        if (_error != null) ...[ErrorBanner(_error!), const SizedBox(height: 16)],
        FilledButton(onPressed: _busy ? null : _submit, child: Text(_busy ? 'Creando…' : 'Continuar')),
      ],
    );
  }
}
