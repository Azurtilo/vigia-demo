import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/network/api_exception.dart';
import '../../core/router/app_router.dart';
import '../../core/theme/vigia_colors.dart';
import '../../core/widgets/async_view.dart';
import '../../core/widgets/form_page.dart';
import '../auth/application/session_controller.dart';
import '../care/domain/care_models.dart';
import '../patients/application/patients_providers.dart';
import '../patients/domain/patient.dart';
import '../today/application/today_providers.dart';
import 'members.dart';

void _snack(BuildContext context, String m) => ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(m)));

Future<bool> _confirm(BuildContext context, String title, String message, String action) async =>
    await showDialog<bool>(
      context: context,
      builder: (c) => AlertDialog(
        title: Text(title),
        content: Text(message),
        actions: [
          TextButton(onPressed: () => Navigator.pop(c, false), child: const Text('Cancelar')),
          TextButton(onPressed: () => Navigator.pop(c, true), child: Text(action)),
        ],
      ),
    ) ??
    false;

/// Personas con acceso al paciente. El responsable invita, ajusta permisos y quita personas;
/// los demás pueden retirarse.
class MembersScreen extends ConsumerWidget {
  const MembersScreen({super.key, required this.patientId});
  final String patientId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final patient = ref.watch(patientProvider(patientId));
    final members = ref.watch(membersProvider(patientId));
    final session = ref.watch(sessionControllerProvider);
    final myUid = session is SessionReady ? session.profile.uid : null;

    return Scaffold(
      appBar: AppBar(title: const Text('Personas con acceso')),
      body: AsyncView(
        value: patient,
        onRetry: () => ref.invalidate(patientProvider(patientId)),
        builder: (p) => AsyncView(
          value: members,
          onRetry: () => ref.invalidate(membersProvider(patientId)),
          builder: (list) => ListView(
            padding: const EdgeInsets.all(16),
            children: [
              if (p.isOwner && !p.isArchived) ...[
                FilledButton.icon(
                  key: const Key('invite'),
                  onPressed: () => _invite(context, ref),
                  icon: const Icon(Icons.person_add_alt),
                  label: const Text('Invitar a una persona'),
                ),
                const SizedBox(height: 16),
              ],
              for (final m in list) _MemberTile(patient: p, member: m, isMe: m.uid == myUid),
              if (p.isOwner) _InvitationsSection(patientId: patientId),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _invite(BuildContext context, WidgetRef ref) async {
    final created = await showModalBottomSheet<CreatedInvitation>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (c) => Padding(
        padding: EdgeInsets.only(bottom: MediaQuery.of(c).viewInsets.bottom),
        child: _InviteSheet(patientId: patientId),
      ),
    );
    if (created == null || !context.mounted) return;
    ref.invalidate(invitationsProvider(patientId));
    await showDialog<void>(context: context, builder: (_) => _CodeDialog(created: created));
  }
}

class _MemberTile extends ConsumerWidget {
  const _MemberTile({required this.patient, required this.member, required this.isMe});
  final Patient patient;
  final Member member;
  final bool isMe;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final canEdit = patient.isOwner && member.relation != 'owner' && !patient.isArchived;
    final canLeave = isMe && member.relation != 'owner';
    return Card(
      elevation: 0,
      color: VigiaColors.surface,
      margin: const EdgeInsets.only(bottom: 10),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: ListTile(
        minVerticalPadding: 12,
        leading: CircleAvatar(
          backgroundColor: VigiaColors.rose,
          child: Text(member.displayName.characters.first.toUpperCase(),
              style: const TextStyle(color: VigiaColors.roseInk, fontWeight: FontWeight.w800)),
        ),
        title: Text(isMe ? '${member.displayName} (tú)' : member.displayName, style: const TextStyle(fontWeight: FontWeight.w700)),
        subtitle: Text('${relationLabel(member.relation)} · ${member.permissions.length} permisos'),
        trailing: canEdit || canLeave
            ? PopupMenuButton<String>(
                tooltip: 'Opciones de ${member.displayName}',
                onSelected: (v) => switch (v) {
                  'permissions' => _editPermissions(context, ref),
                  _ => _remove(context, ref, leaving: v == 'leave'),
                },
                itemBuilder: (_) => [
                  if (canEdit) const PopupMenuItem(value: 'permissions', child: Text('Cambiar permisos')),
                  if (canEdit) const PopupMenuItem(value: 'remove', child: Text('Quitar acceso')),
                  if (canLeave) const PopupMenuItem(value: 'leave', child: Text('Dejar de cuidar a este paciente')),
                ],
              )
            : null,
      ),
    );
  }

  Future<void> _editPermissions(BuildContext context, WidgetRef ref) async {
    final updated = await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (_) => _PermissionsSheet(patientId: patient.id, member: member),
    );
    if (updated == true) ref.invalidate(membersProvider(patient.id));
  }

  Future<void> _remove(BuildContext context, WidgetRef ref, {required bool leaving}) async {
    final ok = await _confirm(
      context,
      leaving ? '¿Dejar de cuidar a ${patient.displayName}?' : '¿Quitar el acceso de ${member.displayName}?',
      leaving
          ? 'Ya no verás a este paciente. Lo que registraste se conserva en su historial.'
          : 'Ya no podrá ver ni registrar nada de ${patient.displayName}. Lo que registró se conserva.',
      leaving ? 'Dejar de cuidar' : 'Quitar acceso',
    );
    if (!ok) return;
    try {
      await ref.read(membersApiProvider).remove(patient.id, member.uid);
      if (!context.mounted) return;
      if (leaving) {
        refreshPatients(ref);
        context.go(Routes.patients);
      } else {
        ref.invalidate(membersProvider(patient.id));
        ref.invalidate(memberNamesProvider(patient.id));
      }
    } on ApiException catch (e) {
      if (context.mounted) _snack(context, e.message);
    }
  }
}

class _InvitationsSection extends ConsumerWidget {
  const _InvitationsSection({required this.patientId});
  final String patientId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final invitations = ref.watch(invitationsProvider(patientId)).value ?? const <Invitation>[];
    if (invitations.isEmpty) return const SizedBox.shrink();
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        const Padding(
          padding: EdgeInsets.only(top: 16, bottom: 8),
          child: Text('Invitaciones', style: TextStyle(fontSize: 20, fontWeight: FontWeight.w800)),
        ),
        for (final i in invitations)
          ListTile(
            tileColor: VigiaColors.surface,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
            title: Text(i.email),
            subtitle: Text('${relationLabel(i.relation)} · ${i.statusLabel}'
                '${i.status == 'pending' ? ' · vence el ${formatDate(i.expiresAt.toLocal())}' : ''}'),
            trailing: i.status == 'pending'
                ? TextButton(
                    onPressed: () async {
                      if (!await _confirm(context, '¿Anular la invitación?', 'El código dejará de funcionar.', 'Anular')) return;
                      try {
                        await ref.read(membersApiProvider).revoke(patientId, i.id);
                        ref.invalidate(invitationsProvider(patientId));
                      } on ApiException catch (e) {
                        if (context.mounted) _snack(context, e.message);
                      }
                    },
                    child: const Text('Anular'),
                  )
                : null,
          ),
      ],
    );
  }
}

class _InviteSheet extends ConsumerStatefulWidget {
  const _InviteSheet({required this.patientId});
  final String patientId;

  @override
  ConsumerState<_InviteSheet> createState() => _InviteSheetState();
}

class _InviteSheetState extends ConsumerState<_InviteSheet> {
  final _form = GlobalKey<FormState>();
  final _email = TextEditingController();
  String _relation = 'caregiver';
  bool _busy = false;
  String? _error;

  @override
  void dispose() {
    _email.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (_busy || !_form.currentState!.validate()) return;
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final created = await ref.read(membersApiProvider).invite(widget.patientId, email: _email.text, relation: _relation);
      if (mounted) Navigator.pop(context, created);
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.message);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(20, 0, 20, 20),
        child: Form(
          key: _form,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text('Invitar a una persona', style: Theme.of(context).textTheme.headlineMedium?.copyWith(fontSize: 24)),
              const SizedBox(height: 12),
              TextFormField(
                key: const Key('invite-email'),
                controller: _email,
                decoration: const InputDecoration(labelText: 'Correo de la persona', helperText: 'Debe crear su cuenta VIGIA con este correo.'),
                keyboardType: TextInputType.emailAddress,
                validator: Validators.email,
              ),
              const SizedBox(height: 16),
              SegmentedButton<String>(
                segments: const [
                  ButtonSegment(value: 'caregiver', label: Text('Cuidador/a')),
                  ButtonSegment(value: 'family', label: Text('Familiar')),
                ],
                selected: {_relation},
                onSelectionChanged: (s) => setState(() => _relation = s.first),
              ),
              const SizedBox(height: 8),
              Text(
                _relation == 'caregiver'
                    ? 'Podrá ver la ficha, registrar tomas y tareas, ver el historial y atender alertas. No podrá modificar la ficha ni los medicamentos.'
                    : 'Tendrá los mismos permisos que tú, salvo invitar personas o archivar al paciente.',
                style: const TextStyle(fontSize: 14, color: VigiaColors.inkMuted),
              ),
              const Text('Podrás ajustar sus permisos cuando acepte.', style: TextStyle(fontSize: 14, color: VigiaColors.inkMuted)),
              const SizedBox(height: 16),
              if (_error != null) ...[ErrorBanner(_error!), const SizedBox(height: 12)],
              FilledButton(onPressed: _busy ? null : _submit, child: Text(_busy ? 'Creando…' : 'Crear invitación')),
            ],
          ),
        ),
      ),
    );
  }
}

class _CodeDialog extends StatelessWidget {
  const _CodeDialog({required this.created});
  final CreatedInvitation created;

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Comparte este código'),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text('Para ${created.invitation.email}. Vence en 7 días y sirve una sola vez.'),
          const SizedBox(height: 16),
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(color: VigiaColors.primarySoft, borderRadius: BorderRadius.circular(12)),
            child: SelectableText(
              created.code,
              key: const Key('invite-code'),
              textAlign: TextAlign.center,
              style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w800, letterSpacing: 1.5, color: VigiaColors.primary),
            ),
          ),
          const SizedBox(height: 12),
          const Text(
            'Por seguridad no lo volverás a ver: si se pierde, anula la invitación y crea otra.',
            style: TextStyle(fontSize: 14, color: VigiaColors.inkMuted),
          ),
        ],
      ),
      actions: [
        TextButton.icon(
          onPressed: () async {
            await Clipboard.setData(ClipboardData(text: created.code));
            if (context.mounted) _snack(context, 'Código copiado.');
          },
          icon: const Icon(Icons.copy),
          label: const Text('Copiar'),
        ),
        TextButton(onPressed: () => Navigator.pop(context), child: const Text('Listo')),
      ],
    );
  }
}

class _PermissionsSheet extends ConsumerStatefulWidget {
  const _PermissionsSheet({required this.patientId, required this.member});
  final String patientId;
  final Member member;

  @override
  ConsumerState<_PermissionsSheet> createState() => _PermissionsSheetState();
}

class _PermissionsSheetState extends ConsumerState<_PermissionsSheet> {
  late final Set<String> _selected = {...widget.member.permissions};
  bool _busy = false;
  String? _error;

  Future<void> _save() async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await ref.read(membersApiProvider).updatePermissions(widget.patientId, widget.member.uid, _selected);
      if (mounted) Navigator.pop(context, true);
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.message);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(12, 0, 12, 20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 8),
              child: Text('Permisos de ${widget.member.displayName}',
                  style: Theme.of(context).textTheme.headlineMedium?.copyWith(fontSize: 22)),
            ),
            for (final e in permissionLabels.entries)
              CheckboxListTile(
                value: _selected.contains(e.key),
                title: Text(e.value),
                // "Ver la ficha" es obligatorio: sin él la persona no vería al paciente.
                subtitle: e.key == 'patient.view' ? const Text('Obligatorio') : null,
                onChanged: e.key == 'patient.view'
                    ? null
                    : (on) => setState(() => on == true ? _selected.add(e.key) : _selected.remove(e.key)),
              ),
            const SizedBox(height: 8),
            if (_error != null) ...[ErrorBanner(_error!), const SizedBox(height: 12)],
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 8),
              child: FilledButton(onPressed: _busy ? null : _save, child: Text(_busy ? 'Guardando…' : 'Guardar permisos')),
            ),
          ],
        ),
      ),
    );
  }
}
