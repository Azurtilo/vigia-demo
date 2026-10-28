import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../network/api_exception.dart';
import '../theme/vigia_colors.dart';

/// Muestra los estados de una carga: cargando, error (con "Reintentar") o contenido.
/// Ninguna pantalla queda en blanco ni cargando sin fin.
class AsyncView<T> extends StatelessWidget {
  const AsyncView({super.key, required this.value, required this.onRetry, required this.builder});

  final AsyncValue<T> value;
  final VoidCallback onRetry;
  final Widget Function(T data) builder;

  @override
  Widget build(BuildContext context) {
    return value.when(
      skipLoadingOnRefresh: true,
      data: builder,
      loading: () => const Center(child: CircularProgressIndicator(semanticsLabel: 'Cargando')),
      error: (error, _) => ErrorState(
        message: error is ApiException ? error.message : 'Ocurrió un error inesperado. Inténtalo de nuevo.',
        offline: error is ApiException && error.isConnectivity,
        onRetry: onRetry,
      ),
    );
  }
}

class ErrorState extends StatelessWidget {
  const ErrorState({super.key, required this.message, required this.onRetry, this.offline = false});
  final String message;
  final bool offline;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(28),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(offline ? Icons.cloud_off_outlined : Icons.error_outline, size: 48, color: VigiaColors.primary),
            const SizedBox(height: 14),
            Text(message, textAlign: TextAlign.center, style: const TextStyle(fontSize: 16)),
            const SizedBox(height: 20),
            SizedBox(width: 220, child: FilledButton(onPressed: onRetry, child: const Text('Reintentar'))),
          ],
        ),
      ),
    );
  }
}

/// Lista vacía con explicación y acciones (nunca datos de ejemplo).
class EmptyState extends StatelessWidget {
  const EmptyState({super.key, required this.icon, required this.title, required this.message, this.actions = const []});
  final IconData icon;
  final String title;
  final String message;
  final List<Widget> actions;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(28),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Icon(icon, size: 56, color: VigiaColors.lavender),
            const SizedBox(height: 14),
            Text(title, textAlign: TextAlign.center, style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 8),
            Text(message, textAlign: TextAlign.center, style: const TextStyle(color: VigiaColors.inkMuted)),
            const SizedBox(height: 24),
            for (final action in actions) ...[action, const SizedBox(height: 12)],
          ],
        ),
      ),
    );
  }
}
