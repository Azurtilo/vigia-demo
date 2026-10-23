import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

class ProfilePanel extends StatelessWidget {
  final Map<String, dynamic>? me;
  final String baseUrl;
  final VoidCallback onPlan, enableNotifications, logout;
  const ProfilePanel({
    super.key,
    required this.me,
    required this.baseUrl,
    required this.onPlan,
    required this.enableNotifications,
    required this.logout,
  });
  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.stretch,
    children: [
      Text('Mi perfil', style: Theme.of(context).textTheme.headlineLarge),
      const SizedBox(height: 20),
      Card(
        child: ListTile(
          leading: const Icon(Icons.account_circle, size: 40),
          title: Text(me?['name'] ?? ''),
          subtitle: Text('Usuario: ${me?['username'] ?? ''}'),
        ),
      ),
      const Text(
        'Tu cuenta y tu suscripción son las mismas que utilizas en la web de VIGIA.',
      ),
      const SizedBox(height: 16),
      ListTile(
        leading: const Icon(Icons.lock_outline),
        title: const Text('Seguridad de la cuenta'),
        onTap: () => launchUrl(
          Uri.parse('$baseUrl/accounts/password/change/'),
          mode: LaunchMode.externalApplication,
        ),
      ),
      ListTile(
        leading: const Icon(Icons.auto_awesome_outlined),
        title: const Text('Mi suscripción'),
        subtitle: Text(me?['capabilities']?['name'] ?? ''),
        onTap: onPlan,
      ),
      ListTile(
        leading: const Icon(Icons.notifications_outlined),
        title: const Text('Avisos de monitoreo y otros cuidados'),
        onTap: enableNotifications,
      ),
      const SizedBox(height: 24),
      OutlinedButton.icon(
        onPressed: logout,
        icon: const Icon(Icons.logout),
        label: const Text('Cerrar sesión'),
      ),
    ],
  );
}
