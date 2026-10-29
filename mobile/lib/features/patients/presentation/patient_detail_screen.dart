import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/network/api_exception.dart';
import '../../../core/router/app_router.dart';
import '../../../core/theme/vigia_colors.dart';
import '../../../core/widgets/async_view.dart';
import '../../care/presentation/care_tabs.dart';
import '../../privacy/care_consent_notice.dart';
import '../../privacy/patient_privacy_screen.dart';
import '../application/patients_providers.dart';
import '../data/patients_api.dart';
import '../domain/patient.dart';

/// Ficha del paciente (pestaña Resumen). Las demás pestañas llegan en los pasos siguientes.
class PatientDetailScreen extends ConsumerWidget {
  const PatientDetailScreen({super.key, required this.patientId});
  final String patientId;

  Future<void> _setArchived(BuildContext context, WidgetRef ref, Patient p, bool archive) async {
    if (archive) {
      final ok = await showDialog<bool>(
        context: context,
        builder: (context) => AlertDialog(
          title: Text('¿Archivar a ${p.displayName}?'),
          content: const Text(
            'Su información e historial se conservan, pero no aparecerá en Hoy ni se podrá editar. '
            'Libera un cupo de tu plan. Puedes reactivarlo después si tu plan lo permite.',
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancelar')),
            TextButton(onPressed: () => Navigator.pop(context, true), child: const Text('Archivar')),
          ],
        ),
      );
      if (ok != true) return;
    }
    try {
      final api = ref.read(patientsApiProvider);
      archive ? await api.archive(p.id) : await api.reactivate(p.id);
      refreshPatients(ref, patientId: p.id);
    } on ApiException catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.message)));
      }
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final patient = ref.watch(patientProvider(patientId));
    final p = patient.value;
    // null mientras carga o si falla: entonces no se muestra el aviso.
    final careConsent = consentActive(ref.watch(patientConsentsProvider(patientId)), 'cuidado');
    return DefaultTabController(
      length: 3,
      child: Scaffold(
        appBar: AppBar(
          title: Text(p?.displayName ?? 'Paciente'),
          // Sin desplazamiento: las pestañas se reparten el ancho y ninguna queda oculta fuera de la pantalla.
          bottom: const TabBar(
            labelStyle: TextStyle(fontFamily: 'Nunito', fontSize: 15, fontWeight: FontWeight.w800),
            tabs: [
              Tab(text: 'Resumen'),
              Tab(text: 'Medicamentos'),
              Tab(text: 'Cuidados'),
            ],
          ),
          actions: [
            if (p != null && p.can('patient.edit') && !p.isArchived)
              TextButton(onPressed: () => context.push(Routes.editPatient(p.id)), child: const Text('Editar')),
            if (p != null && p.isOwner)
              PopupMenuButton<String>(
                tooltip: 'Más opciones',
                onSelected: (v) => _setArchived(context, ref, p, v == 'archive'),
                itemBuilder: (_) => [
                  if (!p.isArchived) const PopupMenuItem(value: 'archive', child: Text('Archivar paciente')),
                  if (p.isArchived) const PopupMenuItem(value: 'reactivate', child: Text('Reactivar paciente')),
                ],
              ),
          ],
        ),
        body: AsyncView(
          value: patient,
          onRetry: () => ref.invalidate(patientProvider(patientId)),
          builder: (p) => TabBarView(
            children: [
              _summary(context, p, careConsent),
              MedicationsTab(patient: p),
              CareTasksTab(patient: p),
            ],
          ),
        ),
      ),
    );
  }

  Widget _summary(BuildContext context, Patient p, bool? careConsent) => ListView(
    padding: const EdgeInsets.all(16),
    children: [
      Text(p.relationLabel, style: const TextStyle(color: VigiaColors.inkMuted)),
      const SizedBox(height: 12),
      if (careConsent == false && !p.isArchived) CareConsentNotice(patient: p),
      _LinkCard(
        icon: Icons.history,
        title: 'Historial',
        subtitle: p.can('history.view') ? 'Tomas, tareas y cambios registrados' : 'No tienes permiso para ver el historial',
        onTap: p.can('history.view') ? () => context.push(Routes.patientHistory(p.id)) : null,
      ),
      _LinkCard(
        icon: Icons.group_outlined,
        title: 'Personas con acceso',
        subtitle: p.isOwner ? 'Invitar, ajustar permisos o quitar acceso' : 'Quiénes cuidan a ${p.displayName}',
        onTap: () => context.push(Routes.patientMembers(p.id)),
      ),
      _LinkCard(
        icon: Icons.privacy_tip_outlined,
        title: 'Privacidad',
        subtitle: p.isOwner ? 'Consentimientos, descargar o eliminar los datos' : 'Consentimientos registrados',
        onTap: () => context.push(Routes.patientPrivacy(p.id)),
      ),
      const SizedBox(height: 4),
      if (p.isArchived)
        const _Card(
          color: VigiaColors.attentionSoft,
          child: Text(
            'Paciente archivado: se puede consultar, pero no editar.',
            style: TextStyle(color: VigiaColors.attention, fontWeight: FontWeight.w700),
          ),
        ),
      if (p.allergies.isNotEmpty)
        _Card(
          color: VigiaColors.riskSoft,
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Icon(Icons.warning_amber_rounded, color: VigiaColors.risk),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Alergias',
                      style: TextStyle(color: VigiaColors.risk, fontWeight: FontWeight.w700),
                    ),
                    Text(p.allergies.join(' · '), style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w700)),
                  ],
                ),
              ),
            ],
          ),
        ),
      _Card(
        color: VigiaColors.sky,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Información para el cuidado', style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 8),
            _Field('Fecha de nacimiento', p.birthDate == null ? null : _date(p.birthDate!)),
            _Field('Movilidad y dependencia', p.mobility),
            _Field('Necesidades de cuidado', p.careNeeds),
            _Field('Observaciones', p.notes),
            if (p.birthDate == null && p.mobility == null && p.careNeeds == null && p.notes == null)
              const Text('Sin información registrada.', style: TextStyle(color: VigiaColors.inkMuted)),
          ],
        ),
      ),
      _Card(
        color: VigiaColors.surface,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Contactos de emergencia', style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 8),
            if (p.emergencyContacts.isEmpty)
              const Text('No hay contactos registrados.', style: TextStyle(color: VigiaColors.inkMuted)),
            for (final c in p.emergencyContacts)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 6),
                child: Row(
                  children: [
                    const Icon(Icons.phone_outlined, color: VigiaColors.primary),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            c.relation == null ? c.name : '${c.name} (${c.relation})',
                            style: const TextStyle(fontWeight: FontWeight.w700),
                          ),
                          SelectableText(c.phone, style: const TextStyle(color: VigiaColors.inkMuted)),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
          ],
        ),
      ),
    ],
  );

  static String _date(DateTime d) =>
      '${d.day.toString().padLeft(2, '0')}-${d.month.toString().padLeft(2, '0')}-${d.year}';
}

/// Acceso a una pantalla relacionada (historial, personas). Desactivado = sin permiso, con el motivo.
class _LinkCard extends StatelessWidget {
  const _LinkCard({required this.icon, required this.title, required this.subtitle, required this.onTap});
  final IconData icon;
  final String title;
  final String subtitle;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) => Card(
        elevation: 0,
        color: VigiaColors.surface,
        margin: const EdgeInsets.only(bottom: 10),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
        child: ListTile(
          minVerticalPadding: 12,
          enabled: onTap != null,
          leading: Icon(icon, color: VigiaColors.primary),
          title: Text(title, style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w700)),
          subtitle: Text(subtitle),
          trailing: onTap == null ? null : const Icon(Icons.chevron_right),
          onTap: onTap,
        ),
      );
}

class _Card extends StatelessWidget {
  const _Card({required this.color, required this.child});
  final Color color;
  final Widget child;

  @override
  Widget build(BuildContext context) => Container(
    width: double.infinity,
    margin: const EdgeInsets.only(bottom: 12),
    padding: const EdgeInsets.all(16),
    decoration: BoxDecoration(color: color, borderRadius: BorderRadius.circular(18)),
    child: child,
  );
}

class _Field extends StatelessWidget {
  const _Field(this.label, this.value);
  final String label;
  final String? value;

  @override
  Widget build(BuildContext context) {
    if (value == null) return const SizedBox.shrink();
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w700)),
          Text(value!, style: const TextStyle(fontSize: 16)),
        ],
      ),
    );
  }
}
