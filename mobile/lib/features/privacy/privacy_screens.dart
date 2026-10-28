import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/router/app_router.dart';
import '../../core/theme/vigia_colors.dart';
import '../../core/widgets/async_view.dart';
import '../auth/application/session_controller.dart';
import '../auth/data/profile_api.dart';
import 'policy_text.dart';

/// Texto de la política, por secciones.
class PolicyBody extends StatelessWidget {
  const PolicyBody({super.key, required this.version});
  final String version;

  @override
  Widget build(BuildContext context) => Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Versión $version', style: const TextStyle(color: VigiaColors.inkMuted)),
          for (final (title, paragraphs) in policySections) ...[
            const SizedBox(height: 18),
            Text(title, style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800)),
            for (final paragraph in paragraphs)
              Padding(padding: const EdgeInsets.only(top: 6), child: Text(paragraph, style: const TextStyle(fontSize: 16))),
          ],
          const SizedBox(height: 18),
          const Text(policyFrame, style: TextStyle(color: VigiaColors.inkMuted, fontSize: 14)),
        ],
      );
}

/// Paso obligatorio cuando la política vigente no está aceptada (D-101).
class AcceptPolicyScreen extends ConsumerStatefulWidget {
  const AcceptPolicyScreen({super.key});

  @override
  ConsumerState<AcceptPolicyScreen> createState() => _AcceptPolicyScreenState();
}

class _AcceptPolicyScreenState extends ConsumerState<AcceptPolicyScreen> {
  bool _read = false;
  bool _saving = false;
  String? _error;

  Future<void> _accept() async {
    setState(() {
      _saving = true;
      _error = null;
    });
    final error = await ref.read(sessionControllerProvider.notifier).acceptPolicy();
    if (mounted) {
      setState(() {
        _saving = false;
        _error = error;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final session = ref.watch(sessionControllerProvider);
    final version = session is NeedsPolicy ? session.policyVersion : policyTextVersion;
    return Scaffold(
      appBar: AppBar(title: const Text('Política de privacidad'), automaticallyImplyLeading: false),
      body: SafeArea(
        child: Column(
          children: [
            Expanded(
              child: ListView(
                padding: const EdgeInsets.all(20),
                children: [
                  const Text(
                    'Antes de continuar, lee cómo VIGIA cuida los datos de salud de las personas que cuidas.',
                    style: TextStyle(fontSize: 17, fontWeight: FontWeight.w700),
                  ),
                  const SizedBox(height: 8),
                  PolicyBody(version: version),
                ],
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 8, 20, 16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  CheckboxListTile(
                    key: const Key('policy-read'),
                    value: _read,
                    onChanged: _saving ? null : (v) => setState(() => _read = v ?? false),
                    controlAffinity: ListTileControlAffinity.leading,
                    contentPadding: EdgeInsets.zero,
                    title: const Text('Leí y acepto la política de privacidad'),
                  ),
                  if (_error != null)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 8),
                      child: Text(_error!, style: const TextStyle(color: VigiaColors.risk)),
                    ),
                  FilledButton(
                    onPressed: _read && !_saving ? _accept : null,
                    child: Text(_saving ? 'Guardando…' : 'Aceptar y continuar'),
                  ),
                  TextButton(
                    onPressed: _saving ? null : () => ref.read(sessionControllerProvider.notifier).signOut(),
                    child: const Text('Usar otra cuenta'),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// La política para consultarla en cualquier momento (Cuenta › Privacidad).
class PolicyScreen extends StatelessWidget {
  const PolicyScreen({super.key});

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('Política de privacidad')),
        body: ListView(padding: const EdgeInsets.all(20), children: const [PolicyBody(version: policyTextVersion)]),
      );
}

/// Cuenta › Privacidad: política, descarga de mis datos y eliminación de la cuenta.
class PrivacyScreen extends ConsumerWidget {
  const PrivacyScreen({super.key});

  Future<void> _deleteAccount(BuildContext context, WidgetRef ref) async {
    final password = await showDialog<String>(context: context, builder: (_) => const _DeleteAccountDialog());
    if (password == null || !context.mounted) return;
    final error = await ref.read(sessionControllerProvider.notifier).deleteAccount(password);
    if (error != null && context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(error)));
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) => Scaffold(
        appBar: AppBar(title: const Text('Privacidad')),
        body: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            ListTile(
              leading: const Icon(Icons.policy_outlined),
              title: const Text('Política de privacidad'),
              subtitle: const Text('Qué datos guardamos, para qué y por cuánto tiempo'),
              trailing: const Icon(Icons.chevron_right),
              onTap: () => context.push(Routes.policy),
            ),
            ListTile(
              leading: const Icon(Icons.download_outlined),
              title: const Text('Descargar mis datos'),
              subtitle: const Text('Tu cuenta y lo que registraste, en formato JSON'),
              trailing: const Icon(Icons.chevron_right),
              onTap: () => context.push(Routes.myData),
            ),
            const SizedBox(height: 8),
            const Padding(
              padding: EdgeInsets.symmetric(horizontal: 16),
              child: Text(
                'Los consentimientos, la descarga y la eliminación de cada paciente están en su ficha › Privacidad.',
                style: TextStyle(color: VigiaColors.inkMuted),
              ),
            ),
            const SizedBox(height: 28),
            OutlinedButton.icon(
              style: OutlinedButton.styleFrom(foregroundColor: VigiaColors.risk),
              onPressed: () => _deleteAccount(context, ref),
              icon: const Icon(Icons.delete_forever_outlined),
              label: const Text('Eliminar mi cuenta'),
            ),
          ],
        ),
      );
}

class _DeleteAccountDialog extends StatefulWidget {
  const _DeleteAccountDialog();

  @override
  State<_DeleteAccountDialog> createState() => _DeleteAccountDialogState();
}

class _DeleteAccountDialogState extends State<_DeleteAccountDialog> {
  final _password = TextEditingController();

  @override
  void dispose() {
    _password.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => AlertDialog(
        title: const Text('¿Eliminar tu cuenta?'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Se borran tu cuenta y los pacientes de los que eres responsable, con todos sus datos. '
                'Lo que registraste en pacientes de otras personas se conserva sin tu nombre. No se puede deshacer.',
              ),
              const SizedBox(height: 14),
              TextField(
                key: const Key('delete-account-password'),
                controller: _password,
                obscureText: true,
                decoration: const InputDecoration(labelText: 'Tu contraseña, para confirmar'),
                onChanged: (_) => setState(() {}),
              ),
            ],
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancelar')),
          TextButton(
            style: TextButton.styleFrom(foregroundColor: VigiaColors.risk),
            onPressed: _password.text.isEmpty ? null : () => Navigator.pop(context, _password.text),
            child: const Text('Eliminar cuenta'),
          ),
        ],
      );
}

/// Muestra una exportación JSON con un botón para copiarla (D-102).
class ExportScreen extends ConsumerWidget {
  const ExportScreen({super.key, required this.title, required this.provider});
  final String title;
  final FutureProvider<Map<String, dynamic>> provider;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final data = ref.watch(provider);
    return Scaffold(
      appBar: AppBar(title: Text(title)),
      body: AsyncView(
        value: data,
        onRetry: () => ref.invalidate(provider),
        builder: (json) {
          final text = const JsonEncoder.withIndent('  ').convert(json);
          return Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    const Text(
                      'Copia el contenido y guárdalo donde prefieras. No incluye contraseñas, tokens ni códigos de invitación.',
                      style: TextStyle(color: VigiaColors.inkMuted),
                    ),
                    const SizedBox(height: 10),
                    FilledButton.icon(
                      onPressed: () async {
                        await Clipboard.setData(ClipboardData(text: text));
                        if (context.mounted) {
                          ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Datos copiados.')));
                        }
                      },
                      icon: const Icon(Icons.copy),
                      label: const Text('Copiar'),
                    ),
                  ],
                ),
              ),
              Expanded(
                child: Container(
                  margin: const EdgeInsets.fromLTRB(16, 0, 16, 16),
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(color: VigiaColors.surface, borderRadius: BorderRadius.circular(14)),
                  child: SingleChildScrollView(
                    child: SelectableText(text, style: const TextStyle(fontFamily: 'monospace', fontSize: 13)),
                  ),
                ),
              ),
            ],
          );
        },
      ),
    );
  }
}

final myDataProvider = FutureProvider.autoDispose<Map<String, dynamic>>(
  (ref) => ref.watch(profileApiProvider).exportAccount(),
);
