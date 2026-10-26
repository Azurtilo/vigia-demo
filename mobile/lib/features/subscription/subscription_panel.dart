import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../shared/care_widgets.dart';
import '../../shared/vigia_design.dart';

Uri changePlanUri(String baseUrl, Map<String, dynamic> caps) =>
    Uri.parse(baseUrl).resolve(caps['change_plan_path'] ?? '/planes/');

class SubscriptionPanel extends StatelessWidget {
  final Map<String, dynamic> caps;
  final String baseUrl;
  final VoidCallback enableNotifications;
  final Future<bool> Function(Uri)? openPortal;
  const SubscriptionPanel({
    super.key,
    required this.caps,
    required this.baseUrl,
    required this.enableNotifications,
    this.openPortal,
  });

  Future<void> changePlan(BuildContext context) async {
    try {
      final uri = changePlanUri(baseUrl, caps);
      final opened = openPortal != null
          ? await openPortal!(uri)
          : await launchUrl(uri, mode: LaunchMode.externalApplication);
      if (!opened && context.mounted) {
        notice(
          context,
          'No se pudo abrir la web de planes. Inténtalo otra vez.',
        );
      }
    } catch (_) {
      if (context.mounted) {
        notice(
          context,
          'No se pudo abrir la web de planes. Revisa la conexión.',
        );
      }
    }
  }

  String price(dynamic value) {
    final number = (value as num?)?.toInt() ?? 0;
    if (number == 0) return 'Gratis';
    return '\$${number.toString().replaceAllMapped(RegExp(r'(\d)(?=(\d{3})+(?!\d))'), (m) => '${m[1]}.')}';
  }

  @override
  Widget build(BuildContext context) {
    final plans = (caps['plans'] as List? ?? []).cast<Map<String, dynamic>>();
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Container(
          padding: const EdgeInsets.all(24),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(26),
            gradient: const LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [Color(0xff7563a2), Color(0xff5057a0)],
            ),
            boxShadow: const [
              BoxShadow(
                color: Color(0x165057a0),
                blurRadius: 18,
                offset: Offset(0, 8),
              ),
            ],
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 13,
                  vertical: 7,
                ),
                decoration: BoxDecoration(
                  color: Colors.white.withValues(alpha: .16),
                  borderRadius: BorderRadius.circular(20),
                ),
                child: const Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                      Icons.auto_awesome_outlined,
                      size: 16,
                      color: Colors.white,
                    ),
                    SizedBox(width: 7),
                    Text(
                      'VIGIA · PLANES',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 11,
                        fontWeight: FontWeight.w700,
                        letterSpacing: .7,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 18),
              const Text(
                'La mejor tecnología al servicio de quien más quieres',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 27,
                  height: 1.25,
                  fontWeight: FontWeight.w800,
                ),
              ),
              const SizedBox(height: 14),
              const Text(
                'Organiza pacientes, medicamentos y posturas con el plan que se adapta a tus cuidados.',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 14,
                  height: 1.6,
                ),
              ),
              const SizedBox(height: 22),
              Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 14,
                  vertical: 11,
                ),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(22),
                ),
                child: Row(
                  children: [
                    Expanded(
                      child: Text(
                        'Tu estado actual: ${caps['name']}',
                        style: const TextStyle(
                          color: VigiaColors.brand,
                          fontSize: 12,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ),
                    const SizedBox(width: 6),
                    TextButton(
                      onPressed: () => changePlan(context),
                      style: TextButton.styleFrom(
                        padding: const EdgeInsets.symmetric(horizontal: 8),
                        minimumSize: const Size(44, 44),
                      ),
                      child: const Text(
                        'Cambiar plan',
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              if (caps['expires_at'] != null)
                Padding(
                  padding: const EdgeInsets.only(top: 12),
                  child: Text(
                    'Vigente hasta ${when(caps['expires_at'])}',
                    style: const TextStyle(color: Colors.white, fontSize: 12),
                  ),
                ),
              if (caps['cancel_at_period_end'] == true)
                const Padding(
                  padding: EdgeInsets.only(top: 8),
                  child: Text(
                    'Cancelación al terminar el período',
                    style: TextStyle(color: Colors.white, fontSize: 12),
                  ),
                ),
            ],
          ),
        ),
        const SizedBox(height: 24),
        const Text(
          'Elige tu plan',
          style: TextStyle(fontSize: 22, fontWeight: FontWeight.w800),
        ),
        const SizedBox(height: 8),
        const Text(
          'Los mismos planes y beneficios que en la web de VIGIA.',
          style: TextStyle(color: VigiaColors.muted, height: 1.5),
        ),
        const SizedBox(height: 16),
        for (final plan in plans) _planCard(context, plan),
        if (plans.isEmpty)
          const Padding(
            padding: EdgeInsets.symmetric(vertical: 16),
            child: Text('Consulta los planes disponibles en la web.'),
          ),
        FilledButton.icon(
          onPressed: () => changePlan(context),
          icon: const Icon(Icons.open_in_new, size: 18),
          label: const Text('Cambiar plan en la web'),
        ),
        const SizedBox(height: 10),
        const Text(
          'Se abrirá la plataforma web. Allí puedes iniciar sesión y gestionar tu suscripción.',
          style: TextStyle(fontSize: 12, color: VigiaColors.muted, height: 1.5),
        ),
        const SizedBox(height: 20),
        OutlinedButton.icon(
          onPressed: enableNotifications,
          icon: const Icon(Icons.notifications_outlined),
          label: const Text('Activar avisos en este teléfono'),
        ),
        Padding(
          padding: const EdgeInsets.only(top: 12),
          // T-011-13: only plans with detection mention the camera.
          child: Text(
            caps['features']?['posture_detection'] == true
                ? 'Puedes analizar con la cámara de este teléfono o consultar un nodo fijo vinculado. Los avisos requieren permiso y conexión.'
                : 'Los avisos requieren permiso y conexión.',
          ),
        ),
      ],
    );
  }

  Widget _planCard(BuildContext context, Map<String, dynamic> plan) {
    final active = caps['plan'] == plan['code'];
    final benefits = (plan['benefits'] as List? ?? []).cast<String>();
    final limit = plan['max_active_patients'];
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(22),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(24),
        border: Border.all(
          color: active ? VigiaColors.brand : VigiaColors.line,
          width: active ? 1.5 : 1,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  plan['name'],
                  style: const TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.w800,
                  ),
                ),
              ),
              if (active) const PlanPill('PLAN ACTUAL'),
            ],
          ),
          const SizedBox(height: 16),
          Text(
            price(plan['price_clp']),
            style: const TextStyle(fontSize: 32, fontWeight: FontWeight.w800),
          ),
          if (plan['price_clp'] != 0)
            const Text(
              'CLP / mes',
              style: TextStyle(color: VigiaColors.muted, fontSize: 12),
            ),
          const SizedBox(height: 12),
          Text(
            plan['description'] ?? '',
            style: const TextStyle(color: VigiaColors.muted, height: 1.5),
          ),
          const Divider(height: 30),
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Icon(
                Icons.people_outline,
                size: 18,
                color: VigiaColors.brand,
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  limit == null
                      ? 'Pacientes activos ilimitados'
                      : '$limit ${limit == 1 ? 'paciente activo' : 'pacientes activos'}',
                  style: const TextStyle(
                    fontWeight: FontWeight.w600,
                    fontSize: 13,
                  ),
                ),
              ),
            ],
          ),
          for (final benefit in benefits.where(
            (text) =>
                !text.toLowerCase().contains('paciente activo') &&
                !text.toLowerCase().contains('pacientes activos'),
          ))
            Padding(
              padding: const EdgeInsets.only(top: 12),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Icon(Icons.check, size: 17, color: Color(0xff39715e)),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      benefit,
                      style: const TextStyle(fontSize: 13, height: 1.5),
                    ),
                  ),
                ],
              ),
            ),
          const SizedBox(height: 20),
          if (active)
            const Text(
              'Tu plan actual',
              style: TextStyle(
                color: VigiaColors.brand,
                fontWeight: FontWeight.w700,
                fontSize: 13,
              ),
            )
          else
            OutlinedButton.icon(
              onPressed: () => changePlan(context),
              icon: const Icon(Icons.open_in_new, size: 16),
              label: Text('Ver ${plan['name']} en la web'),
            ),
        ],
      ),
    );
  }
}
