import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/network/api_exception.dart';
import '../../core/theme/vigia_colors.dart';
import '../../core/widgets/async_view.dart';
import '../../core/widgets/form_page.dart';
import '../patients/application/patients_providers.dart';
import '../today/application/today_providers.dart';
import 'subscription.dart';

/// Plan, uso y cambio de plan SIMULADO (el MVP no cobra).
class PlanScreen extends ConsumerWidget {
  const PlanScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final sub = ref.watch(subscriptionProvider);
    final plans = ref.watch(plansProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('Plan y límites')),
      body: AsyncView(
        value: sub,
        onRetry: () => ref.invalidate(subscriptionProvider),
        builder: (s) => ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(color: VigiaColors.attentionSoft, borderRadius: BorderRadius.circular(14)),
              child: const Row(
                children: [
                  Icon(Icons.info_outline, color: VigiaColors.attention),
                  SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      'Precios de prueba. Los cambios de plan son simulados: no se realiza ningún cobro.',
                      style: TextStyle(color: VigiaColors.attention, fontWeight: FontWeight.w600),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),
            _CurrentPlanCard(sub: s, plan: plans.value?.where((p) => p.id == s.planId).firstOrNull),
            const SizedBox(height: 20),
            const Text('Otros planes', style: TextStyle(fontSize: 20, fontWeight: FontWeight.w800)),
            const SizedBox(height: 10),
            if (plans.hasError) const Text('No pudimos cargar los planes.', style: TextStyle(color: VigiaColors.risk)),
            for (final p in plans.value ?? const <PlanInfo>[])
              if (p.id != s.planId) _OtherPlanCard(plan: p),
          ],
        ),
      ),
    );
  }
}

class _CurrentPlanCard extends StatelessWidget {
  const _CurrentPlanCard({required this.sub, required this.plan});
  final SubscriptionInfo sub;
  final PlanInfo? plan;

  @override
  Widget build(BuildContext context) {
    final max = sub.maxPatients;
    final full = max != null && sub.activePatients >= max;
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(color: VigiaColors.primary, borderRadius: BorderRadius.circular(20)),
      child: DefaultTextStyle(
        style: const TextStyle(color: Colors.white, fontFamily: 'Nunito', fontSize: 15),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Tu plan actual'),
            Row(
              children: [
                Expanded(child: Text(sub.planName, style: const TextStyle(fontSize: 26, fontWeight: FontWeight.w800))),
                if (plan != null) Text(plan!.priceLabel, style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w800)),
              ],
            ),
            const SizedBox(height: 10),
            Text(max == null ? '${sub.activePatients} pacientes activos · sin límite' : 'Pacientes activos: ${sub.activePatients} de $max',
                style: const TextStyle(fontWeight: FontWeight.w700)),
            if (max != null) ...[
              const SizedBox(height: 6),
              ClipRRect(
                borderRadius: BorderRadius.circular(5),
                child: LinearProgressIndicator(
                  value: (sub.activePatients / max).clamp(0, 1).toDouble(),
                  minHeight: 10,
                  backgroundColor: Colors.white24,
                  color: Colors.white,
                  semanticsLabel: 'Pacientes activos',
                ),
              ),
            ],
            if (full) const Padding(padding: EdgeInsets.only(top: 6), child: Text('Llegaste al límite de tu plan.')),
            if (plan != null) ...[
              const SizedBox(height: 12),
              for (final f in plan!.featureLabels)
                Row(children: [const Icon(Icons.check, color: Colors.white, size: 18), const SizedBox(width: 6), Expanded(child: Text(f))]),
            ],
          ],
        ),
      ),
    );
  }
}

class _OtherPlanCard extends ConsumerWidget {
  const _OtherPlanCard({required this.plan});
  final PlanInfo plan;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Card(
      elevation: 0,
      color: plan.id == 'premium' ? VigiaColors.primarySoft : VigiaColors.surface,
      margin: const EdgeInsets.only(bottom: 10),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('${plan.name} · ${plan.priceLabel}', style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w800)),
                  Text(plan.patientsLabel, style: const TextStyle(color: VigiaColors.inkMuted)),
                ],
              ),
            ),
            OutlinedButton(
              style: OutlinedButton.styleFrom(minimumSize: const Size(96, 48)),
              onPressed: () => showModalBottomSheet<void>(
                context: context,
                isScrollControlled: true,
                showDragHandle: true,
                builder: (_) => _PreviewSheet(plan: plan),
              ),
              child: Text('Simular', key: Key('simulate-${plan.id}')),
            ),
          ],
        ),
      ),
    );
  }
}

class _PreviewSheet extends ConsumerStatefulWidget {
  const _PreviewSheet({required this.plan});
  final PlanInfo plan;

  @override
  ConsumerState<_PreviewSheet> createState() => _PreviewSheetState();
}

class _PreviewSheetState extends ConsumerState<_PreviewSheet> {
  late final Future<PlanPreview> _preview = ref.read(subscriptionApiProvider).preview(widget.plan.id);
  bool _understood = false;
  bool _busy = false;
  String? _error;

  Future<void> _change(PlanPreview p) async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await ref.read(subscriptionApiProvider).change(widget.plan.id, confirmOverLimit: p.requiresConfirmation);
      // El plan cambia límites y funciones: se recargan los datos que dependen de él.
      ref.invalidate(subscriptionProvider);
      ref.invalidate(plansProvider);
      refreshPatients(ref);
      ref.invalidate(agendaProvider);
      if (mounted) {
        Navigator.pop(context);
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Ahora tienes el plan ${widget.plan.name} (simulado).')));
      }
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.message);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: FutureBuilder<PlanPreview>(
        future: _preview,
        builder: (context, snap) {
          if (snap.hasError) {
            final e = snap.error;
            return Padding(
              padding: const EdgeInsets.all(24),
              child: Text(e is ApiException ? e.message : 'No pudimos simular el cambio.', style: const TextStyle(color: VigiaColors.risk)),
            );
          }
          if (!snap.hasData) return const Padding(padding: EdgeInsets.all(40), child: Center(child: CircularProgressIndicator()));
          final p = snap.data!;
          return SingleChildScrollView(
            padding: const EdgeInsets.fromLTRB(20, 0, 20, 20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Text('Cambiar a ${p.target.name}', style: Theme.of(context).textTheme.headlineMedium?.copyWith(fontSize: 24)),
                Text('${p.target.priceLabel} · ${p.target.patientsLabel}', style: const TextStyle(color: VigiaColors.inkMuted)),
                const SizedBox(height: 12),
                for (final f in p.target.featureLabels)
                  Row(children: [const Icon(Icons.check, color: VigiaColors.mintInk, size: 18), const SizedBox(width: 6), Expanded(child: Text(f))]),
                const SizedBox(height: 12),
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: p.overLimit || p.lostFeatures.isNotEmpty ? VigiaColors.attentionSoft : VigiaColors.mint,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(p.message, key: const Key('preview-message')),
                ),
                if (p.requiresConfirmation)
                  CheckboxListTile(
                    key: const Key('understood'),
                    contentPadding: EdgeInsets.zero,
                    value: _understood,
                    onChanged: (v) => setState(() => _understood = v ?? false),
                    title: const Text('Entiendo que no podré agregar ni reactivar pacientes hasta quedar dentro del límite.'),
                  ),
                const SizedBox(height: 12),
                if (_error != null) ...[ErrorBanner(_error!), const SizedBox(height: 12)],
                FilledButton(
                  key: const Key('confirm-change'),
                  onPressed: _busy || (p.requiresConfirmation && !_understood) ? null : () => _change(p),
                  child: Text(_busy ? 'Cambiando…' : 'Cambiar a ${p.target.name}'),
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}
