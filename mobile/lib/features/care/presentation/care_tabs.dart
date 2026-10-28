import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/network/api_exception.dart';
import '../../../core/router/app_router.dart';
import '../../../core/theme/vigia_colors.dart';
import '../../../core/widgets/async_view.dart';
import '../../patients/domain/patient.dart';
import '../../today/application/today_providers.dart';
import '../../today/domain/agenda.dart';
import '../../today/presentation/record_sheets.dart';
import '../data/care_api.dart';
import '../domain/care_models.dart';

Future<bool> _confirm(BuildContext context, String title, String message, String action) async =>
    await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(title),
        content: Text(message),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancelar')),
          TextButton(onPressed: () => Navigator.pop(context, true), child: Text(action)),
        ],
      ),
    ) ??
    false;

void _snack(BuildContext context, String message) =>
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(message)));

String _dates(DateTime start, DateTime? end) =>
    end == null ? 'Desde ${formatDate(start)}' : 'Del ${formatDate(start)} al ${formatDate(end)}';

/// Etiqueta "Inactivo" con texto + ícono.
class _InactiveTag extends StatelessWidget {
  const _InactiveTag();

  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
        decoration: BoxDecoration(color: const Color(0xFFECEAF2), borderRadius: BorderRadius.circular(999)),
        child: const Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.pause_circle_outline, size: 14, color: VigiaColors.inkMuted),
            SizedBox(width: 4),
            Text('Inactivo', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: VigiaColors.inkMuted)),
          ],
        ),
      );
}

// ============================================================================================
// Medicamentos
// ============================================================================================

class MedicationsTab extends ConsumerWidget {
  const MedicationsTab({super.key, required this.patient});
  final Patient patient;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final meds = ref.watch(medicationsProvider(patient.id));
    final canManage = patient.can('meds.manage') && !patient.isArchived;
    final canAdminister = patient.can('meds.administer') && !patient.isArchived;

    Future<void> setActive(Medication m, bool active) async {
      if (!active &&
          !await _confirm(
            context,
            '¿Desactivar ${m.name}?',
            'Deja de aparecer en la agenda. Las tomas ya registradas se conservan y puedes reactivarlo después.',
            'Desactivar',
          )) {
        return;
      }
      try {
        await ref.read(careApiProvider).updateMedication(patient.id, m.id, {'active': active});
        ref.invalidate(medicationsProvider(patient.id));
        ref.invalidate(agendaProvider((patientId: patient.id, day: null)));
      } on ApiException catch (e) {
        if (context.mounted) _snack(context, e.message);
      }
    }

    Future<void> recordAsNeeded(Medication m) async {
      if (!await _confirm(context, 'Registrar toma', '¿Registrar que se dio ${m.name} (${m.dose}) ahora?', 'Registrar')) return;
      try {
        await ref.read(careApiProvider).recordAsNeededDose(patient.id, m.id);
        ref.invalidate(agendaProvider((patientId: patient.id, day: null)));
        if (context.mounted) _snack(context, 'Toma de ${m.name} registrada.');
      } on ApiException catch (e) {
        if (context.mounted) _snack(context, e.message);
      }
    }

    return AsyncView(
      value: meds,
      onRetry: () => ref.invalidate(medicationsProvider(patient.id)),
      builder: (list) {
        final sorted = [...list]..sort((a, b) => a.active == b.active ? a.name.compareTo(b.name) : (a.active ? -1 : 1));
        return ListView(
          padding: const EdgeInsets.all(16),
          children: [
            if (canManage)
              FilledButton.icon(
                key: const Key('add-medication'),
                onPressed: () => context.push(Routes.newMedication(patient.id)),
                icon: const Icon(Icons.add),
                label: const Text('Agregar medicamento'),
              ),
            if (list.isEmpty)
              const Padding(
                padding: EdgeInsets.symmetric(vertical: 32),
                child: Text('No hay medicamentos registrados.', textAlign: TextAlign.center, style: TextStyle(color: VigiaColors.inkMuted)),
              ),
            const SizedBox(height: 12),
            for (final m in sorted)
              Card(
                elevation: 0,
                color: VigiaColors.surface,
                margin: const EdgeInsets.only(bottom: 10),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(16, 12, 8, 12),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Expanded(child: Text(m.name, style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w700))),
                          if (!m.active) const _InactiveTag(),
                          if (canManage)
                            PopupMenuButton<String>(
                              tooltip: 'Opciones de ${m.name}',
                              onSelected: (v) => v == 'edit'
                                  ? context.push(Routes.editMedication(patient.id, m.id))
                                  : setActive(m, v == 'activate'),
                              itemBuilder: (_) => [
                                const PopupMenuItem(value: 'edit', child: Text('Editar')),
                                PopupMenuItem(value: m.active ? 'deactivate' : 'activate', child: Text(m.active ? 'Desactivar' : 'Reactivar')),
                              ],
                            ),
                        ],
                      ),
                      Text(m.dose, style: const TextStyle(fontSize: 15)),
                      if (m.instructions != null) Text(m.instructions!, style: const TextStyle(color: VigiaColors.inkMuted)),
                      const SizedBox(height: 4),
                      Row(
                        children: [
                          const Icon(Icons.schedule, size: 16, color: VigiaColors.primary),
                          const SizedBox(width: 6),
                          Expanded(child: Text(m.scheduleLabel, style: const TextStyle(fontWeight: FontWeight.w600))),
                        ],
                      ),
                      Text(_dates(m.startDate, m.endDate), style: const TextStyle(fontSize: 14, color: VigiaColors.inkMuted)),
                      if (m.asNeeded && m.active && canAdminister)
                        Padding(
                          padding: const EdgeInsets.only(top: 8, right: 8),
                          child: OutlinedButton.icon(
                            onPressed: () => recordAsNeeded(m),
                            icon: const Icon(Icons.check),
                            label: const Text('Registrar toma'),
                          ),
                        ),
                    ],
                  ),
                ),
              ),
          ],
        );
      },
    );
  }
}

// ============================================================================================
// Cuidados
// ============================================================================================

class CareTasksTab extends ConsumerWidget {
  const CareTasksTab({super.key, required this.patient});
  final Patient patient;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final tasks = ref.watch(tasksProvider(patient.id));
    final names = ref.watch(memberNamesProvider(patient.id)).value ?? const <String, String>{};
    final agenda = ref.watch(agendaProvider((patientId: patient.id, day: null))).value;
    final canManage = patient.can('care.manage') && !patient.isArchived;
    final canRecord = patient.can('care.record') && !patient.isArchived;

    Future<void> setActive(CareTask t, bool active) async {
      if (!active &&
          !await _confirm(context, '¿Desactivar "${t.title}"?',
              'Deja de aparecer en la agenda. Los registros se conservan y puedes reactivarla después.', 'Desactivar')) {
        return;
      }
      try {
        await ref.read(careApiProvider).updateTask(patient.id, t.id, {'active': active});
        ref.invalidate(tasksProvider(patient.id));
        ref.invalidate(agendaProvider((patientId: patient.id, day: null)));
      } on ApiException catch (e) {
        if (context.mounted) _snack(context, e.message);
      }
    }

    Future<void> record(CareTask t) async {
      final item = TaskItem(taskId: t.id, title: t.title, description: t.description, taskKind: t.kind, status: 'pending');
      final saved = await showRecordSheet(
        context,
        TaskSheet(patientId: patient.id, item: item, extendedTracking: agenda?.extendedCareTracking ?? false, allowSkip: false),
      );
      if (saved) {
        ref.invalidate(agendaProvider((patientId: patient.id, day: null)));
        if (context.mounted) _snack(context, '"${t.title}" registrada.');
      }
    }

    return AsyncView(
      value: tasks,
      onRetry: () => ref.invalidate(tasksProvider(patient.id)),
      builder: (list) {
        final sorted = [...list]..sort((a, b) => a.active == b.active ? a.title.compareTo(b.title) : (a.active ? -1 : 1));
        return ListView(
          padding: const EdgeInsets.all(16),
          children: [
            if (canManage)
              FilledButton.icon(
                key: const Key('add-task'),
                onPressed: () => context.push(Routes.newTask(patient.id)),
                icon: const Icon(Icons.add),
                label: const Text('Agregar tarea'),
              ),
            if (list.isEmpty)
              const Padding(
                padding: EdgeInsets.symmetric(vertical: 32),
                child: Text('No hay tareas en el plan de cuidados.', textAlign: TextAlign.center, style: TextStyle(color: VigiaColors.inkMuted)),
              ),
            const SizedBox(height: 12),
            for (final t in sorted)
              Card(
                elevation: 0,
                color: VigiaColors.surface,
                margin: const EdgeInsets.only(bottom: 10),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(16, 12, 8, 12),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Expanded(child: Text(t.title, style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w700))),
                          if (!t.active) const _InactiveTag(),
                          if (canManage)
                            PopupMenuButton<String>(
                              tooltip: 'Opciones de ${t.title}',
                              onSelected: (v) =>
                                  v == 'edit' ? context.push(Routes.editTask(patient.id, t.id)) : setActive(t, v == 'activate'),
                              itemBuilder: (_) => [
                                const PopupMenuItem(value: 'edit', child: Text('Editar')),
                                PopupMenuItem(value: t.active ? 'deactivate' : 'activate', child: Text(t.active ? 'Desactivar' : 'Reactivar')),
                              ],
                            ),
                        ],
                      ),
                      if (t.isPositionChange)
                        const Text('Cambio de posición', style: TextStyle(color: VigiaColors.primary, fontWeight: FontWeight.w700)),
                      if (t.description != null) Text(t.description!, style: const TextStyle(color: VigiaColors.inkMuted)),
                      const SizedBox(height: 4),
                      Row(
                        children: [
                          const Icon(Icons.schedule, size: 16, color: VigiaColors.primary),
                          const SizedBox(width: 6),
                          Expanded(child: Text(t.scheduleLabel, style: const TextStyle(fontWeight: FontWeight.w600))),
                        ],
                      ),
                      if (t.assignedTo != null)
                        Text('Responsable: ${names[t.assignedTo] ?? 'otra persona'}', style: const TextStyle(fontSize: 14)),
                      Text(_dates(t.startDate, t.endDate), style: const TextStyle(fontSize: 14, color: VigiaColors.inkMuted)),
                      if (t.unscheduled && t.active && canRecord && (!t.isPositionChange || (agenda?.positionChanges ?? false)))
                        Padding(
                          padding: const EdgeInsets.only(top: 8, right: 8),
                          child: OutlinedButton.icon(onPressed: () => record(t), icon: const Icon(Icons.check), label: const Text('Registrar')),
                        ),
                    ],
                  ),
                ),
              ),
          ],
        );
      },
    );
  }
}
