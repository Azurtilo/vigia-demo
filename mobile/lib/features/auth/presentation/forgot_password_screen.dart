import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/theme/vigia_colors.dart';
import '../../../core/widgets/form_page.dart';
import '../data/auth_repository.dart';

class ForgotPasswordScreen extends ConsumerStatefulWidget {
  const ForgotPasswordScreen({super.key});

  @override
  ConsumerState<ForgotPasswordScreen> createState() => _ForgotPasswordScreenState();
}

class _ForgotPasswordScreenState extends ConsumerState<ForgotPasswordScreen> {
  final _form = GlobalKey<FormState>();
  final _email = TextEditingController();
  bool _busy = false;
  bool _sent = false;
  String? _error;

  @override
  void dispose() {
    _email.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (_busy || !_form.currentState!.validate()) return;
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await ref.read(authRepositoryProvider).sendPasswordReset(_email.text);
      if (mounted) setState(() => _sent = true);
    } on AuthFailure catch (e) {
      if (mounted) setState(() => _error = e.message);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return FormPage(
      title: 'Recuperar contraseña',
      subtitle: 'Te enviaremos un enlace para crear una nueva.',
      showBack: true,
      children: [
        if (_sent)
          // Mismo mensaje exista o no la cuenta: no se revela qué correos están registrados.
          Container(
            key: const Key('reset-sent'),
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(color: VigiaColors.mint, borderRadius: BorderRadius.circular(14)),
            child: const Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Icon(Icons.mark_email_read_outlined, color: VigiaColors.mintInk),
                SizedBox(width: 10),
                Expanded(
                  child: Text(
                    'Si existe una cuenta con ese correo, te enviamos un enlace. Revisa también la carpeta de spam.',
                    style: TextStyle(color: VigiaColors.mintInk, fontWeight: FontWeight.w600),
                  ),
                ),
              ],
            ),
          )
        else ...[
          Form(
            key: _form,
            child: TextFormField(
              key: const Key('reset-email'),
              controller: _email,
              decoration: const InputDecoration(labelText: 'Correo electrónico'),
              keyboardType: TextInputType.emailAddress,
              validator: Validators.email,
            ),
          ),
          const SizedBox(height: 20),
          if (_error != null) ...[ErrorBanner(_error!), const SizedBox(height: 16)],
          FilledButton(onPressed: _busy ? null : _submit, child: Text(_busy ? 'Enviando…' : 'Enviar enlace')),
        ],
      ],
    );
  }
}
