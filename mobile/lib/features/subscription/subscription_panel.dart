import '../../shared/care_widgets.dart';

import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

class SubscriptionPanel extends StatelessWidget {
  final Map<String, dynamic> caps;
  final String baseUrl;
  final VoidCallback enableNotifications;
  const SubscriptionPanel({
    super.key,
    required this.caps,
    required this.baseUrl,
    required this.enableNotifications,
  });
  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.stretch,
    children: [
      Text(
        'Tu espacio VIGIA',
        style: Theme.of(context).textTheme.headlineLarge,
      ),
      const SizedBox(height: 20),
      Container(
        padding: const EdgeInsets.all(24),
        decoration: BoxDecoration(
          color: const Color(0xff5057a0),
          borderRadius: BorderRadius.circular(24),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              caps['name'],
              style: const TextStyle(
                color: Colors.white,
                fontSize: 28,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 12),
            Text(
              caps['max_active_patients'] == null
                  ? 'Pacientes activos ilimitados'
                  : '${caps['max_active_patients']} pacientes activos',
              style: const TextStyle(color: Colors.white, fontSize: 18),
            ),
            if (caps['expires_at'] != null)
              Text(
                'Vigente hasta ${when(caps['expires_at'])}',
                style: const TextStyle(color: Colors.white),
              ),
            if (caps['cancel_at_period_end'] == true)
              const Text(
                'Cancelación al terminar el período',
                style: TextStyle(color: Colors.white),
              ),
          ],
        ),
      ),
      const SizedBox(height: 16),
      for (final f in const {
        'care_manual': 'Agenda y cuidados',
        'medication_schedule': 'Medicamentos y horarios',
        'posture_manual': 'Guías y cambios de postura',
        'care_history': 'Historial de cuidados',
        'posture_detection': 'Detección de posición con cámara',
      }.entries)
        ListTile(
          leading: Icon(
            caps['features'][f.key] == true
                ? Icons.check_circle_outline
                : Icons.lock_outline,
          ),
          title: Text(f.value),
          subtitle: caps['features'][f.key] == true
              ? null
              : const Text('Disponible en Premium'),
        ),
      const SizedBox(height: 12),
      FilledButton(
        onPressed: () => launchUrl(
          Uri.parse('$baseUrl${caps['portal_path']}'),
          mode: LaunchMode.externalApplication,
        ),
        child: const Text('Gestionar plan en el portal'),
      ),
      const SizedBox(height: 12),
      OutlinedButton.icon(
        onPressed: enableNotifications,
        icon: const Icon(Icons.notifications_outlined),
        label: const Text('Activar avisos en este teléfono'),
      ),
      Padding(
        padding: const EdgeInsets.only(top: 12),
        // T-011-13: only plans with detection mention the camera.
        child: Text(
          caps['features']['posture_detection'] == true
              ? 'Puedes analizar con la cámara de este teléfono o consultar un nodo fijo vinculado. Los avisos requieren permiso y conexión.'
              : 'Los avisos requieren permiso y conexión.',
        ),
      ),
    ],
  );
}
