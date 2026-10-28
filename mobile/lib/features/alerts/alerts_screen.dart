import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/network/api_exception.dart';
import '../../core/theme/vigia_colors.dart';
import '../../core/widgets/async_view.dart';
import 'alerts.dart';

/// Bandeja de alertas de todos los pacientes que la persona atiende (RF-019-14).
/// Se recarga al abrir, al volver la app al primer plano y al deslizar hacia abajo.
class AlertsScreen extends ConsumerStatefulWidget {
  const AlertsScreen({super.key});

  @override
  ConsumerState<AlertsScreen> createState() => _AlertsScreenState();
}

class _AlertsScreenState extends ConsumerState<AlertsScreen> {
  late final AppLifecycleListener _lifecycle;
  final Set<String> _attending = {};

  @override
  void initState() {
    super.initState();
    _lifecycle = AppLifecycleListener(onResume: () => ref.invalidate(myAlertsProvider));
  }

  @override
  void dispose() {
    _lifecycle.dispose();
    super.dispose();
  }

  Future<void> _attend(AlertItem alert) async {
    setState(() => _attending.add(alert.id));
    try {
      await ref.read(alertsApiProvider).attend(alert.patientId, alert.id);
    } on ApiException catch (e) {
      // 409: otra persona ya la atendió. Se informa y la lista se recarga igual.
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.message)));
    } finally {
      if (mounted) setState(() => _attending.remove(alert.id));
      ref.invalidate(myAlertsProvider);
    }
  }

  @override
  Widget build(BuildContext context) {
    final alerts = ref.watch(myAlertsProvider);
    return Scaffold(
      appBar: AppBar(
        title: const Text('Alertas'),
        actions: [
          IconButton(
            tooltip: 'Actualizar',
            icon: const Icon(Icons.refresh),
            onPressed: () => ref.invalidate(myAlertsProvider),
          ),
        ],
      ),
      body: AsyncView(
        value: alerts,
        onRetry: () => ref.invalidate(myAlertsProvider),
        builder: (items) => RefreshIndicator(
          onRefresh: () => ref.refresh(myAlertsProvider.future),
          child: items.isEmpty
              ? ListView(
                  children: const [
                    SizedBox(height: 120),
                    EmptyState(
                      icon: Icons.notifications_none,
                      title: 'Sin alertas',
                      message: 'Aquí aparecerán las posibles caídas, la inmovilidad prolongada y los avisos '
                          'de la cámara de los pacientes que cuidas.',
                    ),
                  ],
                )
              : ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: items.length,
                  itemBuilder: (_, i) => _AlertCard(
                    alert: items[i],
                    busy: _attending.contains(items[i].id),
                    onAttend: () => _attend(items[i]),
                  ),
                ),
        ),
      ),
    );
  }
}

class _AlertCard extends StatelessWidget {
  const _AlertCard({required this.alert, required this.busy, required this.onAttend});
  final AlertItem alert;
  final bool busy;
  final VoidCallback onAttend;

  @override
  Widget build(BuildContext context) {
    final open = alert.isOpen;
    final (Color soft, Color ink, IconData icon) = switch ((open, alert.isRisk)) {
      (false, _) => (VigiaColors.surface, VigiaColors.inkMuted, Icons.check_circle_outline),
      (true, true) => (VigiaColors.riskSoft, VigiaColors.risk, Icons.warning_amber_rounded),
      (true, false) => (VigiaColors.attentionSoft, VigiaColors.attention, Icons.videocam_off_outlined),
    };
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(color: soft, borderRadius: BorderRadius.circular(18)),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Icon(icon, color: ink),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(alert.title, style: TextStyle(color: ink, fontSize: 18, fontWeight: FontWeight.w800)),
                    if (alert.patientName != null)
                      Text(alert.patientName!, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
                    Text(alertTime(alert.occurredAt), style: const TextStyle(color: VigiaColors.inkMuted)),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          if (open) ...[
            Text(alert.advice),
            const SizedBox(height: 12),
            FilledButton(
              onPressed: busy ? null : onAttend,
              child: Text(busy ? 'Guardando…' : 'Marcar como atendida'),
            ),
          ] else
            Text(
              alert.attendedAt == null ? 'Atendida' : 'Atendida · ${alertTime(alert.attendedAt!)}',
              style: const TextStyle(color: VigiaColors.inkMuted, fontWeight: FontWeight.w700),
            ),
        ],
      ),
    );
  }
}

/// Hora local de la alerta: "hoy 19:58", "ayer 08:10" o "26-10-2026 08:10".
String alertTime(DateTime at, {DateTime? now}) {
  final local = at.toLocal();
  final today = (now ?? DateTime.now()).toLocal();
  final hm = '${local.hour.toString().padLeft(2, '0')}:${local.minute.toString().padLeft(2, '0')}';
  final day = DateTime(local.year, local.month, local.day);
  final diff = DateTime(today.year, today.month, today.day).difference(day).inDays;
  if (diff == 0) return 'hoy $hm';
  if (diff == 1) return 'ayer $hm';
  return '${local.day.toString().padLeft(2, '0')}-${local.month.toString().padLeft(2, '0')}-${local.year} $hm';
}
