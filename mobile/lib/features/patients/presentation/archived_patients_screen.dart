import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/router/app_router.dart';
import '../../../core/theme/vigia_colors.dart';
import '../../../core/widgets/async_view.dart';
import '../application/patients_providers.dart';

class ArchivedPatientsScreen extends ConsumerWidget {
  const ArchivedPatientsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final archived = ref.watch(archivedPatientsProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('Pacientes archivados')),
      body: AsyncView(
        value: archived,
        onRetry: () => ref.invalidate(archivedPatientsProvider),
        builder: (list) => list.isEmpty
            ? const EmptyState(
                icon: Icons.inventory_2_outlined,
                title: 'No hay pacientes archivados',
                message: 'Al archivar un paciente se conserva toda su información y deja de contar para tu plan.',
              )
            : ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  for (final p in list)
                    ListTile(
                      tileColor: VigiaColors.surface,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                      title: Text(p.displayName, style: const TextStyle(fontWeight: FontWeight.w700)),
                      subtitle: Text(p.relationLabel),
                      trailing: const Icon(Icons.chevron_right),
                      onTap: () => context.push(Routes.patientDetail(p.id)),
                    ),
                ],
              ),
      ),
    );
  }
}
