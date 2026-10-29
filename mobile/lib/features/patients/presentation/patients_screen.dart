import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/router/app_router.dart';
import '../../../core/theme/vigia_colors.dart';
import '../../../core/widgets/async_view.dart';
import '../application/patients_providers.dart';
import '../domain/patient.dart';

class PatientsScreen extends ConsumerWidget {
  const PatientsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final patients = ref.watch(patientsProvider);
    final usage = ref.watch(planUsageProvider);
    return Scaffold(
      appBar: AppBar(
        title: const Text('Pacientes'),
        actions: [
          IconButton(
            tooltip: 'Pacientes archivados',
            icon: const Icon(Icons.inventory_2_outlined),
            onPressed: () => context.push(Routes.archivedPatients),
          ),
        ],
      ),
      body: AsyncView(
        value: patients,
        onRetry: () => refreshPatients(ref),
        builder: (list) => list.isEmpty
            ? EmptyState(
                icon: Icons.favorite_border,
                title: 'Aún no tienes pacientes',
                message: 'Registra a la persona que cuidas, o únete con el código que te compartió su responsable.',
                actions: [
                  _AddPatientButton(usage: usage.value),
                  OutlinedButton(onPressed: () => context.push(Routes.joinPatient), child: const Text('Unirme con código')),
                ],
              )
            : RefreshIndicator(
                onRefresh: () async => refreshPatients(ref),
                child: ListView(
                  padding: const EdgeInsets.fromLTRB(16, 4, 16, 24),
                  children: [
                    if (usage.value != null) _PlanUsageBanner(usage.value!),
                    for (final p in list) _PatientCard(patient: p),
                    const SizedBox(height: 12),
                    _AddPatientButton(usage: usage.value),
                    const SizedBox(height: 12),
                    OutlinedButton(onPressed: () => context.push(Routes.joinPatient), child: const Text('Unirme con código')),
                  ],
                ),
              ),
      ),
    );
  }
}

class _PlanUsageBanner extends StatelessWidget {
  const _PlanUsageBanner(this.usage);
  final PlanUsage usage;

  @override
  Widget build(BuildContext context) {
    final full = !usage.canAddPatient;
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: full ? VigiaColors.attentionSoft : VigiaColors.primarySoft,
        borderRadius: BorderRadius.circular(14),
      ),
      child: Row(
        children: [
          Icon(full ? Icons.info_outline : Icons.people_outline, color: full ? VigiaColors.attention : VigiaColors.primary),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              full ? '${usage.usageLabel}. Llegaste al límite de tu plan.' : usage.usageLabel,
              style: TextStyle(fontWeight: FontWeight.w600, color: full ? VigiaColors.attention : VigiaColors.ink),
            ),
          ),
        ],
      ),
    );
  }
}

/// El límite lo aplica el backend; aquí solo se anticipa para no ofrecer algo que se rechazará.
class _AddPatientButton extends StatelessWidget {
  const _AddPatientButton({required this.usage});
  final PlanUsage? usage;

  @override
  Widget build(BuildContext context) {
    final blocked = usage != null && !usage!.canAddPatient;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        FilledButton.icon(
          onPressed: blocked ? null : () => context.push(Routes.newPatient),
          icon: const Icon(Icons.add),
          label: const Text('Registrar paciente'),
        ),
        if (blocked)
          const Padding(
            padding: EdgeInsets.only(top: 6),
            child: Text(
              'Para agregar otro, archiva un paciente o cambia de plan en Cuenta.',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 14, color: VigiaColors.inkMuted),
            ),
          ),
      ],
    );
  }
}

class _PatientCard extends StatelessWidget {
  const _PatientCard({required this.patient});
  final Patient patient;

  @override
  Widget build(BuildContext context) {
    return Card(
      color: VigiaColors.surface,
      elevation: 0,
      margin: const EdgeInsets.only(bottom: 10),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
      child: ListTile(
        minVerticalPadding: 14,
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
        leading: CircleAvatar(
          radius: 24,
          backgroundColor: VigiaColors.sky,
          child: Text(
            patient.displayName.characters.first.toUpperCase(),
            style: const TextStyle(fontWeight: FontWeight.w800, color: VigiaColors.ink, fontSize: 18),
          ),
        ),
        title: Text(patient.displayName, style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w700)),
        subtitle: Text(patient.relationLabel, style: const TextStyle(color: VigiaColors.inkMuted)),
        trailing: const Icon(Icons.chevron_right),
        onTap: () => context.push(Routes.patientDetail(patient.id)),
      ),
    );
  }
}
