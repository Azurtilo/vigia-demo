import 'package:flutter/material.dart';

import '../../../core/theme/vigia_colors.dart';

/// Sección aún no construida. Lo dice claramente en vez de mostrar datos de ejemplo.
class PendingSectionScreen extends StatelessWidget {
  const PendingSectionScreen({super.key, required this.title, this.phase = 'el siguiente paso'});
  final String title;
  final String phase;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(title)),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.construction_outlined, size: 48, color: VigiaColors.primary),
              const SizedBox(height: 16),
              Text(
                'Esta sección se construye en $phase.',
                textAlign: TextAlign.center,
                style: const TextStyle(fontSize: 17, color: VigiaColors.inkMuted),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
