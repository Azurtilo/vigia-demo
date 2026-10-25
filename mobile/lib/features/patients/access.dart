import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../core/api.dart';
import '../../shared/care_widgets.dart';

/// Spec 013: the server decides; these helpers only adapt what is shown.
bool allows(Map<String, dynamic>? patient, String action) {
  final actions = patient?['allowed_actions'];
  // Older servers send no roles: the account owns every patient it lists.
  return actions is List ? actions.contains(action) : action != 'leave';
}

String roleLabel(dynamic role) => switch (role) {
  'familiar' => 'Familiar',
  'cuidador' => 'Cuidador',
  _ => 'Responsable',
};

Future<String?> askCode(BuildContext context) async {
  final controller = TextEditingController();
  final code = await showDialog<String>(
    context: context,
    builder: (c) => AlertDialog(
      title: const Text('Unirme con un código'),
      content: TextField(
        controller: controller,
        autofocus: true,
        textCapitalization: TextCapitalization.characters,
        decoration: const InputDecoration(
          labelText: 'Código de invitación',
          helperText:
              'Lo entrega la persona responsable. Vence a las 48 horas.',
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(c),
          child: const Text('Volver'),
        ),
        FilledButton(
          onPressed: () => Navigator.pop(c, controller.text.trim()),
          child: const Text('Revisar código'),
        ),
      ],
    ),
  );
  controller.dispose();
  return code == null || code.isEmpty ? null : code;
}

/// Preview first, then accept: the person sees patient and role before joining.
Future<bool> joinWithCode(BuildContext context, VigiaApi api) async {
  final code = await askCode(context);
  if (code == null || !context.mounted) return false;
  try {
    final found = await api.post('access/preview', {'code': code});
    if (!context.mounted) return false;
    final ok = await confirm(
      context,
      'Unirte a ${found['patient_name']}',
      'Acompañarás a este paciente como ${roleLabel(found['role']).toLowerCase()}. '
          'La persona responsable puede retirar tu acceso cuando quiera.',
    );
    if (!ok) return false;
    await api.post('access/accept', {'code': code});
    if (context.mounted) {
      notice(context, 'Listo. Ya puedes acompañar a este paciente.');
    }
    return true;
  } catch (e) {
    if (context.mounted) notice(context, e);
    return false;
  }
}

class AccessPanel extends StatefulWidget {
  final VigiaApi api;
  final int patientId;
  const AccessPanel({super.key, required this.api, required this.patientId});
  @override
  State<AccessPanel> createState() => _AccessPanelState();
}

class _AccessPanelState extends State<AccessPanel> {
  List<dynamic> accesses = [], invitations = [];
  bool busy = false;

  @override
  void initState() {
    super.initState();
    load();
  }

  Future<void> load() async {
    try {
      final r = await widget.api.get('patients/${widget.patientId}/access');
      if (mounted) {
        setState(() {
          accesses = r['accesses'] ?? [];
          invitations = r['invitations'] ?? [];
        });
      }
    } catch (e) {
      if (mounted) notice(context, e);
    }
  }

  Future<void> run(Future<void> Function() action) async {
    if (busy) return;
    setState(() => busy = true);
    try {
      await action();
    } catch (e) {
      if (mounted) notice(context, e);
    } finally {
      if (mounted) setState(() => busy = false);
      await load();
    }
  }

  Future<void> invite() async {
    final role = await showDialog<String>(
      context: context,
      builder: (c) => SimpleDialog(
        title: const Text('¿A quién invitas?'),
        children: [
          SimpleDialogOption(
            onPressed: () => Navigator.pop(c, 'cuidador'),
            child: const ListTile(
              title: Text('Cuidador'),
              subtitle: Text('Ve la agenda y registra cuidados y posturas'),
            ),
          ),
          SimpleDialogOption(
            onPressed: () => Navigator.pop(c, 'familiar'),
            child: const ListTile(
              title: Text('Familiar'),
              subtitle: Text('Configura cuidados y revisa el historial'),
            ),
          ),
        ],
      ),
    );
    if (role == null) return;
    await run(() async {
      final r = await widget.api.post('patients/${widget.patientId}/access', {
        'role': role,
      });
      if (!mounted) return;
      await showDialog<void>(
        context: context,
        builder: (c) => AlertDialog(
          title: const Text('Código de invitación'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              SelectableText(
                r['code'],
                style: const TextStyle(
                  fontSize: 28,
                  fontWeight: FontWeight.w700,
                ),
              ),
              const SizedBox(height: 12),
              Text(
                'Compártelo solo con la persona que invitas. Sirve una vez y vence el ${when(r['expires_at'])}.',
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () =>
                  Clipboard.setData(ClipboardData(text: r['code'])),
              child: const Text('Copiar'),
            ),
            FilledButton(
              onPressed: () => Navigator.pop(c),
              child: const Text('Listo'),
            ),
          ],
        ),
      );
    });
  }

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Row(
        children: [
          const Expanded(
            child: Text(
              'Personas con acceso',
              style: TextStyle(fontSize: 22, fontWeight: FontWeight.w700),
            ),
          ),
          IconButton(
            onPressed: busy ? null : invite,
            tooltip: 'Invitar con un código',
            icon: const Icon(Icons.person_add_alt),
          ),
        ],
      ),
      if (accesses.isEmpty && invitations.isEmpty)
        const Text('Nadie más tiene acceso a esta ficha.'),
      for (final a in accesses)
        Card(
          child: ListTile(
            leading: const Icon(Icons.people_outline),
            title: Text(a['name']),
            subtitle: Text(
              '${roleLabel(a['role'])} · desde ${when(a['accepted_at'])}',
            ),
            trailing: IconButton(
              tooltip: 'Revocar acceso',
              icon: const Icon(Icons.person_remove_outlined),
              onPressed: busy
                  ? null
                  : () async {
                      if (await confirm(
                        context,
                        '¿Revocar acceso?',
                        'Dejará de ver esta ficha de inmediato. Sus registros se conservan.',
                      )) {
                        await run(
                          () => widget.api.post('access/${a['id']}/revoke', {}),
                        );
                      }
                    },
            ),
          ),
        ),
      for (final i in invitations)
        Card(
          child: ListTile(
            leading: const Icon(Icons.key_outlined),
            title: const Text('Código sin usar'),
            subtitle: Text(
              '${roleLabel(i['role'])} · vence ${when(i['expires_at'])}',
            ),
            trailing: TextButton(
              onPressed: busy
                  ? null
                  : () => run(
                      () =>
                          widget.api.post('invitations/${i['id']}/revoke', {}),
                    ),
              child: const Text('Anular'),
            ),
          ),
        ),
    ],
  );
}
