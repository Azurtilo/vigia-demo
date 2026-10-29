import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../core/router/app_router.dart';
import '../../core/theme/vigia_colors.dart';
import '../patients/domain/patient.dart';

/// Aviso de que falta el consentimiento de cuidado. Solo el responsable ve el botón para registrarlo.
/// Se muestra en el resumen de la ficha y en Medicamentos y Cuidados (T-019-19, RF-019-17).
class CareConsentNotice extends StatelessWidget {
  const CareConsentNotice({super.key, required this.patient});
  final Patient patient;

  @override
  Widget build(BuildContext context) => Container(
        key: const Key('care-consent-notice'),
        width: double.infinity,
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(color: VigiaColors.attentionSoft, borderRadius: BorderRadius.circular(18)),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Falta el consentimiento de datos de cuidado',
              style: TextStyle(color: VigiaColors.attention, fontSize: 17, fontWeight: FontWeight.w800),
            ),
            const SizedBox(height: 6),
            Text(
              patient.isOwner
                  ? 'Sin él no se pueden registrar medicamentos, tomas, tareas ni cambios de posición.'
                  : 'La persona responsable debe registrarlo antes de que se puedan anotar tomas y cuidados.',
            ),
            if (patient.isOwner) ...[
              const SizedBox(height: 10),
              FilledButton(
                onPressed: () => context.push(Routes.patientPrivacy(patient.id)),
                child: const Text('Registrar consentimiento'),
              ),
            ],
          ],
        ),
      );
}
