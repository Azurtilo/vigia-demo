import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/network/api_exception.dart';
import '../../core/router/app_router.dart';
import '../../core/theme/vigia_colors.dart';
import '../../core/widgets/async_view.dart';
import '../patients/application/patients_providers.dart';
import '../patients/data/patients_api.dart';
import '../patients/domain/patient.dart';
import 'privacy.dart';

final patientConsentsProvider = FutureProvider.autoDispose.family<List<PatientConsent>, String>(
  (ref, id) => ref.watch(patientsApiProvider).consents(id),
);

final patientExportProvider = FutureProvider.autoDispose.family<Map<String, dynamic>, String>(
  (ref, id) => ref.watch(patientsApiProvider).exportPatient(id),
);

/// Consentimiento activo para una finalidad (null mientras carga o si falló la consulta).
bool? consentActive(AsyncValue<List<PatientConsent>> consents, String scope) =>
    consents.value?.any((c) => c.scope == scope && c.active);

/// Pide quién consiente (paciente o representante con nombre y relación) y la confirmación.
Future<ConsentDraft?> askConsent(BuildContext context, String scope) =>
    showDialog<ConsentDraft>(context: context, builder: (_) => _ConsentDialog(scope: scope));

/// Ficha › Privacidad: consentimientos por finalidad, descarga y eliminación del paciente (RF-019-17, 25, 26).
class PatientPrivacyScreen extends ConsumerWidget {
  const PatientPrivacyScreen({super.key, required this.patientId});
  final String patientId;

  Future<void> _register(BuildContext context, WidgetRef ref, String scope) async {
    final draft = await askConsent(context, scope);
    if (draft == null || !context.mounted) return;
    await _run(context, ref, () => ref.read(patientsApiProvider).registerConsent(patientId, scope, draft));
  }

  Future<void> _revoke(BuildContext context, WidgetRef ref, String scope) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('¿Revocar «${consentTitles[scope]}»?'),
        content: Text(revokeEffects[scope]!),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancelar')),
          TextButton(onPressed: () => Navigator.pop(context, true), child: const Text('Revocar')),
        ],
      ),
    );
    if (ok != true || !context.mounted) return;
    await _run(context, ref, () => ref.read(patientsApiProvider).revokeConsent(patientId, scope));
  }

  Future<void> _run(BuildContext context, WidgetRef ref, Future<Object?> Function() action) async {
    try {
      await action();
    } on ApiException catch (e) {
      if (context.mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.message)));
    }
    ref.invalidate(patientConsentsProvider(patientId));
  }

  Future<void> _delete(BuildContext context, WidgetRef ref, Patient p) async {
    final confirmed = await showDialog<String>(context: context, builder: (_) => _DeletePatientDialog(name: p.displayName));
    if (confirmed == null || !context.mounted) return;
    try {
      await ref.read(patientsApiProvider).deletePatient(p.id, confirmed);
      refreshPatients(ref);
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('${p.displayName} y sus datos fueron eliminados.')));
        context.go(Routes.patients);
      }
    } on ApiException catch (e) {
      if (context.mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.message)));
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final patient = ref.watch(patientProvider(patientId));
    final consents = ref.watch(patientConsentsProvider(patientId));
    return Scaffold(
      appBar: AppBar(title: const Text('Privacidad')),
      body: AsyncView(
        value: patient,
        onRetry: () => ref.invalidate(patientProvider(patientId)),
        builder: (p) => AsyncView(
          value: consents,
          onRetry: () => ref.invalidate(patientConsentsProvider(patientId)),
          builder: (items) => ListView(
            padding: const EdgeInsets.all(16),
            children: [
              Text('Consentimientos de ${p.displayName}', style: Theme.of(context).textTheme.titleLarge),
              const SizedBox(height: 4),
              Text(
                p.isOwner
                    ? 'Registra quién da el consentimiento para cada finalidad. Puedes revocarlo cuando quieras.'
                    : 'Solo la persona responsable registra o revoca los consentimientos.',
                style: const TextStyle(color: VigiaColors.inkMuted),
              ),
              const SizedBox(height: 12),
              for (final scope in consentScopes)
                _ConsentCard(
                  scope: scope,
                  consent: items.where((c) => c.scope == scope).firstOrNull,
                  canManage: p.isOwner && !p.isArchived,
                  onRegister: () => _register(context, ref, scope),
                  onRevoke: () => _revoke(context, ref, scope),
                ),
              if (p.isOwner) ...[
                const SizedBox(height: 16),
                ListTile(
                  leading: const Icon(Icons.download_outlined),
                  title: const Text('Descargar datos del paciente'),
                  subtitle: const Text('Ficha, medicamentos, registros e historial en JSON'),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () => context.push(Routes.patientExport(p.id)),
                ),
                const SizedBox(height: 20),
                OutlinedButton.icon(
                  style: OutlinedButton.styleFrom(foregroundColor: VigiaColors.risk),
                  onPressed: () => _delete(context, ref, p),
                  icon: const Icon(Icons.delete_forever_outlined),
                  label: const Text('Eliminar paciente y todos sus datos'),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

class _ConsentCard extends StatelessWidget {
  const _ConsentCard({
    required this.scope,
    required this.consent,
    required this.canManage,
    required this.onRegister,
    required this.onRevoke,
  });
  final String scope;
  final PatientConsent? consent;
  final bool canManage;
  final VoidCallback onRegister;
  final VoidCallback onRevoke;

  @override
  Widget build(BuildContext context) {
    final active = consent?.active ?? false;
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: active ? VigiaColors.surface : VigiaColors.attentionSoft,
        borderRadius: BorderRadius.circular(18),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(active ? Icons.verified_user_outlined : Icons.gpp_maybe_outlined,
                  color: active ? VigiaColors.mintInk : VigiaColors.attention),
              const SizedBox(width: 10),
              Expanded(
                child: Text(consentTitles[scope]!, style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w800)),
              ),
              Text(
                consent?.statusLabel ?? 'Sin registrar',
                style: TextStyle(fontWeight: FontWeight.w700, color: active ? VigiaColors.mintInk : VigiaColors.attention),
              ),
            ],
          ),
          const SizedBox(height: 6),
          Text(consentDescriptions[scope]!),
          if (active && consent!.basisLabel.isNotEmpty) ...[
            const SizedBox(height: 6),
            Text(consent!.basisLabel, style: const TextStyle(color: VigiaColors.inkMuted)),
          ],
          if (canManage) ...[
            const SizedBox(height: 10),
            Align(
              alignment: Alignment.centerLeft,
              child: active
                  ? TextButton(onPressed: onRevoke, child: const Text('Revocar'))
                  : FilledButton(onPressed: onRegister, child: const Text('Registrar consentimiento')),
            ),
          ],
        ],
      ),
    );
  }
}

class _ConsentDialog extends StatefulWidget {
  const _ConsentDialog({required this.scope});
  final String scope;

  @override
  State<_ConsentDialog> createState() => _ConsentDialogState();
}

class _ConsentDialogState extends State<_ConsentDialog> {
  String _basis = 'titular';
  bool _confirmed = false;
  final _name = TextEditingController();
  final _relation = TextEditingController();

  @override
  void dispose() {
    _name.dispose();
    _relation.dispose();
    super.dispose();
  }

  bool get _valid =>
      _confirmed && (_basis == 'titular' || (_name.text.trim().isNotEmpty && _relation.text.trim().isNotEmpty));

  @override
  Widget build(BuildContext context) => AlertDialog(
        title: Text(consentTitles[widget.scope]!),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(consentDescriptions[widget.scope]!),
              const SizedBox(height: 12),
              const Text('¿Quién da el consentimiento?', style: TextStyle(fontWeight: FontWeight.w700)),
              RadioGroup<String>(
                groupValue: _basis,
                onChanged: (v) => setState(() => _basis = v ?? 'titular'),
                child: const Column(
                  children: [
                    RadioListTile(value: 'titular', contentPadding: EdgeInsets.zero, title: Text('El propio paciente')),
                    RadioListTile(
                      value: 'representante',
                      contentPadding: EdgeInsets.zero,
                      title: Text('Un representante del paciente'),
                    ),
                  ],
                ),
              ),
              if (_basis == 'representante') ...[
                TextField(
                  key: const Key('consent-name'),
                  controller: _name,
                  maxLength: 120,
                  decoration: const InputDecoration(labelText: 'Nombre del representante'),
                  onChanged: (_) => setState(() {}),
                ),
                TextField(
                  key: const Key('consent-relation'),
                  controller: _relation,
                  maxLength: 60,
                  decoration: const InputDecoration(labelText: 'Relación con el paciente'),
                  onChanged: (_) => setState(() {}),
                ),
              ],
              CheckboxListTile(
                key: const Key('consent-confirm'),
                value: _confirmed,
                onChanged: (v) => setState(() => _confirmed = v ?? false),
                controlAffinity: ListTileControlAffinity.leading,
                contentPadding: EdgeInsets.zero,
                title: const Text('Confirmo que cuento con este consentimiento.'),
              ),
            ],
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancelar')),
          TextButton(
            onPressed: _valid
                ? () => Navigator.pop(
                      context,
                      _basis == 'titular'
                          ? const ConsentDraft.titular()
                          : ConsentDraft.representative(_name.text, _relation.text),
                    )
                : null,
            child: const Text('Registrar'),
          ),
        ],
      );
}

class _DeletePatientDialog extends StatefulWidget {
  const _DeletePatientDialog({required this.name});
  final String name;

  @override
  State<_DeletePatientDialog> createState() => _DeletePatientDialogState();
}

class _DeletePatientDialogState extends State<_DeletePatientDialog> {
  final _typed = TextEditingController();

  @override
  void dispose() {
    _typed.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => AlertDialog(
        title: Text('¿Eliminar a ${widget.name}?'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Text(
                'Se borran la ficha, los medicamentos, los registros, el historial, las alertas, los nodos y el '
                'acceso de todas las personas. No se puede deshacer. Si solo quieres dejar de usarla, archívala.',
              ),
              const SizedBox(height: 12),
              TextField(
                key: const Key('delete-patient-name'),
                controller: _typed,
                decoration: InputDecoration(labelText: 'Escribe «${widget.name}» para confirmar'),
                onChanged: (_) => setState(() {}),
              ),
            ],
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancelar')),
          TextButton(
            style: TextButton.styleFrom(foregroundColor: VigiaColors.risk),
            onPressed: sameName(_typed.text, widget.name) ? () => Navigator.pop(context, _typed.text) : null,
            child: const Text('Eliminar'),
          ),
        ],
      );
}
