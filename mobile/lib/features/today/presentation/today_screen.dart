import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/router/app_router.dart';
import '../../../core/theme/vigia_colors.dart';
import '../../../core/widgets/async_view.dart';
import '../../../core/widgets/vigia_logo.dart';
import '../../auth/application/session_controller.dart';
import '../../patients/application/patients_providers.dart';
import '../../patients/domain/patient.dart';
import '../application/today_providers.dart';
import '../domain/agenda.dart';
import 'record_sheets.dart';

const _weekdays = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo'];
const _months = [
  'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
  'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre',
];

String _longDate(DateTime d) => '${_weekdays[d.weekday - 1]} ${d.day} de ${_months[d.month - 1]}';

/// Inicio: lo que hay que hacer en el día con el paciente activo.
class TodayScreen extends ConsumerWidget {
  const TodayScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final active = ref.watch(activePatientProvider);
    return Scaffold(
      body: AsyncView(
        value: active,
        onRetry: () => ref.invalidate(patientsProvider),
        builder: (patient) => patient == null
            ? SafeArea(
                child: EmptyState(
                  icon: Icons.favorite_border,
                  title: 'Aún no hay pacientes',
                  message: 'Para ver la agenda del día, registra a la persona que cuidas o únete con un código.',
                  actions: [FilledButton(onPressed: () => context.go(Routes.patients), child: const Text('Ir a Pacientes'))],
                ),
              )
            : _AgendaView(patient: patient),
      ),
    );
  }
}

class _AgendaView extends ConsumerWidget {
  const _AgendaView({required this.patient});
  final Patient patient;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final day = ref.watch(selectedDayProvider);
    final key = (patientId: patient.id, day: day);
    final agenda = ref.watch(agendaProvider(key));
    final names = ref.watch(memberNamesProvider(patient.id)).value ?? const {};
    final session = ref.watch(sessionControllerProvider);
    final myUid = session is SessionReady ? session.profile.uid : null;

    void refresh() {
      ref.invalidate(agendaProvider(key));
      ref.invalidate(memberNamesProvider(patient.id));
    }

    return Column(
      children: [
        _Header(patient: patient, agenda: agenda.value, isToday: day == null),
        Expanded(
          child: AsyncView(
            value: agenda,
            onRetry: refresh,
            builder: (a) => RefreshIndicator(
              onRefresh: () async => refresh(),
              child: ListView(
                padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
                children: [
                  if (a.items.isEmpty)
                    const Padding(
                      padding: EdgeInsets.symmetric(vertical: 40),
                      child: Text(
                        'No hay medicamentos ni tareas programadas para este día.',
                        textAlign: TextAlign.center,
                        style: TextStyle(fontSize: 16, color: VigiaColors.inkMuted),
                      ),
                    ),
                  for (final item in a.items)
                    _ItemCard(
                      item: item,
                      who: _who(item.log?.recordedBy, names, myUid),
                      canRecord: !item.isRecorded &&
                          item.scheduledAt != null &&
                          (item is MedicationItem ? patient.can('meds.administer') : patient.can('care.record')),
                      onRecord: () async {
                        final sheet = switch (item) {
                          MedicationItem() => DoseSheet(patientId: patient.id, item: item, day: a.date),
                          TaskItem() => TaskSheet(patientId: patient.id, item: item, extendedTracking: a.extendedCareTracking),
                        };
                        if (await showRecordSheet(context, sheet)) refresh();
                      },
                      canCorrect: _canCorrect(item, patient, myUid),
                      onCorrect: () async {
                        final logId = item.log!.id;
                        final sheet = switch (item) {
                          MedicationItem() => DoseSheet(patientId: patient.id, item: item, day: a.date, correctLogId: logId),
                          TaskItem() => TaskSheet(
                              patientId: patient.id,
                              item: item,
                              extendedTracking: a.extendedCareTracking,
                              allowSkip: a.extendedCareTracking && item.scheduledAt != null,
                              correctLogId: logId,
                            ),
                        };
                        if (await showRecordSheet(context, sheet)) refresh();
                      },
                    ),
                  if (a.positionChanges && patient.can('care.record') && day == null) ...[
                    const SizedBox(height: 4),
                    OutlinedButton.icon(
                      key: const Key('position-button'),
                      onPressed: () async {
                        final sheet = PositionSheet(patientId: patient.id, extendedTracking: a.extendedCareTracking);
                        if (await showRecordSheet(context, sheet)) refresh();
                      },
                      icon: const Icon(Icons.add),
                      label: const Text('Registrar cambio de posición'),
                    ),
                  ],
                ],
              ),
            ),
          ),
        ),
      ],
    );
  }

  /// Puede corregir quien hizo el registro (si conserva el permiso) o el responsable del paciente.
  /// Las tomas "si es necesario" solo pueden ser "dadas": no se ofrece corregirlas aquí.
  static bool _canCorrect(AgendaItem item, Patient patient, String? myUid) {
    final log = item.log;
    if (log == null || patient.isArchived) return false;
    if (item is MedicationItem && item.scheduledAt == null) return false;
    if (patient.isOwner) return true;
    final permission = item is MedicationItem ? 'meds.administer' : 'care.record';
    return log.recordedBy == myUid && patient.can(permission);
  }

  static String? _who(String? uid, Map<String, String> names, String? myUid) {
    if (uid == null) return null;
    if (uid == myUid) return 'ti';
    return names[uid] ?? 'otra persona';
  }
}

class _Header extends ConsumerWidget {
  const _Header({required this.patient, required this.agenda, required this.isToday});
  final Patient patient;
  final Agenda? agenda;
  final bool isToday;

  Future<void> _choosePatient(BuildContext context, WidgetRef ref) async {
    final patients = ref.read(patientsProvider).value ?? const <Patient>[];
    final chosen = await showModalBottomSheet<String>(
      context: context,
      showDragHandle: true,
      builder: (context) => SafeArea(
        child: ListView(
          shrinkWrap: true,
          children: [
            const Padding(
              padding: EdgeInsets.fromLTRB(20, 0, 20, 8),
              child: Text('Elegir paciente', style: TextStyle(fontSize: 20, fontWeight: FontWeight.w800)),
            ),
            for (final p in patients)
              ListTile(
                minTileHeight: 56,
                leading: Icon(p.id == patient.id ? Icons.radio_button_checked : Icons.radio_button_off, color: VigiaColors.primary),
                title: Text(p.displayName, style: const TextStyle(fontWeight: FontWeight.w700)),
                subtitle: Text(p.relationLabel),
                onTap: () => Navigator.pop(context, p.id),
              ),
          ],
        ),
      ),
    );
    if (chosen != null) ref.read(activePatientIdProvider.notifier).select(chosen);
  }

  void _shiftDay(WidgetRef ref, int days) {
    final base = agenda?.date;
    if (base == null) return;
    final target = DateTime(base.year, base.month, base.day + days);
    ref.read(selectedDayProvider.notifier).set(target);
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final several = (ref.watch(patientsProvider).value?.length ?? 0) > 1;
    final a = agenda;
    return Container(
      decoration: const BoxDecoration(
        color: VigiaColors.primarySoft,
        borderRadius: BorderRadius.vertical(bottom: Radius.circular(24)),
      ),
      padding: EdgeInsets.fromLTRB(16, MediaQuery.of(context).padding.top + 12, 16, 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Flexible(
                child: Material(
                  color: VigiaColors.surface,
                  shape: const StadiumBorder(),
                  child: InkWell(
                    customBorder: const StadiumBorder(),
                    onTap: several ? () => _choosePatient(context, ref) : null,
                    child: Padding(
                      padding: const EdgeInsets.fromLTRB(6, 6, 14, 6),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          CircleAvatar(
                            radius: 18,
                            backgroundColor: VigiaColors.sky,
                            child: Text(patient.displayName.characters.first.toUpperCase(),
                                style: const TextStyle(fontWeight: FontWeight.w800, color: VigiaColors.ink)),
                          ),
                          const SizedBox(width: 10),
                          Flexible(
                            child: Text(patient.displayName,
                                overflow: TextOverflow.ellipsis, style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w700)),
                          ),
                          if (several) const Icon(Icons.expand_more),
                        ],
                      ),
                    ),
                  ),
                ),
              ),
              const Spacer(),
              const VigiaLogo(size: 44),
            ],
          ),
          const SizedBox(height: 14),
          Row(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(isToday ? 'Hoy' : 'Agenda', style: Theme.of(context).textTheme.headlineMedium),
                    Text(a == null ? '' : _longDate(a.date), style: const TextStyle(fontSize: 16, color: VigiaColors.inkMuted)),
                  ],
                ),
              ),
              if (a != null && a.items.isNotEmpty)
                Column(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Text('${a.recordedCount} de ${a.items.length}',
                        style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w800, color: VigiaColors.primary)),
                    const Text('registrados', style: TextStyle(fontSize: 14, color: VigiaColors.inkMuted)),
                  ],
                ),
            ],
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              IconButton(tooltip: 'Día anterior', onPressed: () => _shiftDay(ref, -1), icon: const Icon(Icons.chevron_left)),
              if (!isToday)
                TextButton(
                  onPressed: () => ref.read(selectedDayProvider.notifier).set(null),
                  child: const Text('Volver a hoy'),
                ),
              const Spacer(),
              IconButton(tooltip: 'Día siguiente', onPressed: () => _shiftDay(ref, 1), icon: const Icon(Icons.chevron_right)),
            ],
          ),
        ],
      ),
    );
  }
}

class _ItemCard extends StatelessWidget {
  const _ItemCard({
    required this.item,
    required this.who,
    required this.canRecord,
    required this.onRecord,
    required this.canCorrect,
    required this.onCorrect,
  });
  final AgendaItem item;
  final String? who;
  final bool canRecord;
  final VoidCallback onRecord;
  final bool canCorrect;
  final VoidCallback onCorrect;

  @override
  Widget build(BuildContext context) {
    final subtitle = switch (item) {
      MedicationItem(:final dose, :final instructions) => [dose, ?instructions].join(' · '),
      TaskItem(:final isPositionChange, :final description) =>
        isPositionChange ? 'Cambio de posición' : (description ?? 'Tarea del plan de cuidados'),
    };
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: VigiaColors.surface,
        borderRadius: BorderRadius.circular(18),
        border: canRecord ? Border.all(color: VigiaColors.primarySoft, width: 2) : null,
      ),
      child: Row(
        children: [
          SizedBox(
            width: 56,
            child: Text(
              item.localTime ?? (item.log?.at == null ? '—' : hhmm(item.log!.at!)),
              textAlign: TextAlign.center,
              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w800),
            ),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(item.title, style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w700)),
                Text(subtitle, style: const TextStyle(fontSize: 14, color: VigiaColors.inkMuted)),
                const SizedBox(height: 6),
                StatusChip(item: item, who: who),
                if (item.log?.reason != null)
                  Padding(
                    padding: const EdgeInsets.only(top: 4),
                    child: Text('Motivo: ${item.log!.reason}', style: const TextStyle(fontSize: 14, color: VigiaColors.inkMuted)),
                  ),
                if ((item.log?.corrections ?? 0) > 0)
                  const Text('Corregido', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: VigiaColors.inkMuted)),
                if (canCorrect)
                  Align(
                    alignment: Alignment.centerLeft,
                    child: TextButton.icon(
                      onPressed: onCorrect,
                      icon: const Icon(Icons.edit_outlined, size: 18),
                      label: Text('Corregir', semanticsLabel: 'Corregir registro de ${item.title}'),
                    ),
                  ),
              ],
            ),
          ),
          if (canRecord)
            IconButton.filled(
              tooltip: 'Registrar ${item.title}${item.localTime == null ? '' : ' de las ${item.localTime}'}',
              onPressed: onRecord,
              style: IconButton.styleFrom(minimumSize: const Size(52, 52), shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14))),
              icon: const Icon(Icons.check),
            ),
        ],
      ),
    );
  }
}

/// Estado con texto + ícono (nunca solo color), hora real y quién registró.
class StatusChip extends StatelessWidget {
  const StatusChip({super.key, required this.item, this.who});
  final AgendaItem item;
  final String? who;

  @override
  Widget build(BuildContext context) {
    final (label, icon, fg, bg) = switch (item.status) {
      'given' => ('Dada', Icons.check, VigiaColors.mintInk, VigiaColors.mint),
      'done' => (
          item is TaskItem && (item as TaskItem).isPositionChange && item.log?.position != null
              ? positionLabels[item.log!.position] ?? 'Realizada'
              : 'Realizada',
          Icons.check,
          VigiaColors.mintInk,
          VigiaColors.mint
        ),
      'delayed' => ('Retrasada', Icons.schedule, VigiaColors.attention, VigiaColors.attentionSoft),
      'omitted' => ('No se dio', Icons.block, VigiaColors.inkMuted, const Color(0xFFECEAF2)),
      'skipped' => ('No realizada', Icons.block, VigiaColors.inkMuted, const Color(0xFFECEAF2)),
      _ => ('Pendiente', Icons.radio_button_unchecked, VigiaColors.primary, VigiaColors.primarySoft),
    };
    final parts = [label, if (item.log?.at != null) hhmm(item.log!.at!), ?who];
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(color: bg, borderRadius: BorderRadius.circular(999)),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 16, color: fg),
          const SizedBox(width: 6),
          Flexible(child: Text(parts.join(' · '), style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: fg))),
        ],
      ),
    );
  }
}
