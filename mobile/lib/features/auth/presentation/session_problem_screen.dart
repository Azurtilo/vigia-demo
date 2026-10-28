import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/theme/vigia_colors.dart';
import '../../../core/widgets/form_page.dart';
import '../application/session_controller.dart';

/// Sin conexión con VIGIA, o cuenta suspendida. Nunca deja a la persona en una pantalla vacía.
class SessionProblemScreen extends ConsumerStatefulWidget {
  const SessionProblemScreen({super.key});

  @override
  ConsumerState<SessionProblemScreen> createState() => _SessionProblemScreenState();
}

class _SessionProblemScreenState extends ConsumerState<SessionProblemScreen> {
  bool _retrying = false;

  Future<void> _retry() async {
    setState(() => _retrying = true);
    await ref.read(sessionControllerProvider.notifier).retry();
    if (mounted) setState(() => _retrying = false);
  }

  @override
  Widget build(BuildContext context) {
    final session = ref.watch(sessionControllerProvider);
    final blocked = session is SessionBlocked;
    final message = switch (session) {
      SessionBlocked(:final message) => message,
      SessionUnavailable(:final error) => error.message,
      _ => 'No pudimos verificar tu cuenta.',
    };
    return FormPage(
      title: blocked ? 'Cuenta sin acceso' : 'Sin conexión con VIGIA',
      children: [
        Icon(
          blocked ? Icons.lock_outline : Icons.cloud_off_outlined,
          size: 56,
          color: blocked ? VigiaColors.risk : VigiaColors.primary,
        ),
        const SizedBox(height: 16),
        Text(message, textAlign: TextAlign.center, style: const TextStyle(fontSize: 17)),
        const SizedBox(height: 28),
        if (!blocked)
          FilledButton(
            key: const Key('retry'),
            onPressed: _retrying ? null : _retry,
            child: Text(_retrying ? 'Reintentando…' : 'Reintentar'),
          ),
        const SizedBox(height: 12),
        OutlinedButton(
          onPressed: () => ref.read(sessionControllerProvider.notifier).signOut(),
          child: const Text('Cerrar sesión'),
        ),
      ],
    );
  }
}
