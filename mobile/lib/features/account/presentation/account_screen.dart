import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/router/app_router.dart';
import '../../../core/theme/vigia_colors.dart';
import '../../auth/application/session_controller.dart';

class AccountScreen extends ConsumerWidget {
  const AccountScreen({super.key});

  Future<void> _confirmSignOut(BuildContext context, WidgetRef ref) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('¿Cerrar sesión?'),
        content: const Text('Tendrás que ingresar tu correo y contraseña la próxima vez.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancelar')),
          TextButton(onPressed: () => Navigator.pop(context, true), child: const Text('Cerrar sesión')),
        ],
      ),
    );
    if (confirmed == true) await ref.read(sessionControllerProvider.notifier).signOut();
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final session = ref.watch(sessionControllerProvider);
    final profile = session is SessionReady ? session.profile : null;
    return Scaffold(
      appBar: AppBar(title: const Text('Cuenta')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Container(
            padding: const EdgeInsets.all(18),
            decoration: BoxDecoration(color: VigiaColors.surface, borderRadius: BorderRadius.circular(18)),
            child: Row(
              children: [
                CircleAvatar(
                  radius: 28,
                  backgroundColor: VigiaColors.rose,
                  child: Text(
                    (profile?.displayName.isNotEmpty ?? false) ? profile!.displayName[0].toUpperCase() : '?',
                    style: const TextStyle(color: VigiaColors.roseInk, fontSize: 22, fontWeight: FontWeight.w800),
                  ),
                ),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(profile?.displayName ?? '', style: Theme.of(context).textTheme.titleLarge),
                      Text(profile?.email ?? '', style: const TextStyle(color: VigiaColors.inkMuted)),
                      if (profile?.isAdmin ?? false)
                        const Text('Administración de VIGIA', style: TextStyle(color: VigiaColors.primary, fontWeight: FontWeight.w700)),
                    ],
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          ListTile(
            leading: const Icon(Icons.workspace_premium_outlined),
            title: const Text('Plan y límites'),
            subtitle: const Text('Tu plan, uso y cambio de plan (simulado)'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => context.push(Routes.plan),
          ),
          ListTile(
            leading: const Icon(Icons.key_outlined),
            title: const Text('Unirse con código de invitación'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => context.push(Routes.joinPatient),
          ),
          const SizedBox(height: 24),
          OutlinedButton.icon(
            onPressed: () => _confirmSignOut(context, ref),
            icon: const Icon(Icons.logout),
            label: const Text('Cerrar sesión'),
          ),
        ],
      ),
    );
  }
}
