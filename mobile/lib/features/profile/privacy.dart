import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../core/api.dart';
import '../../shared/care_widgets.dart';

/// Spec 014: the policy, exports and account deletion live in the web portal.
bool consentRequired(Object? error) =>
    error is ApiError && error.response['consent_required'] == true;

Future<void> openPortal(String baseUrl, String path) =>
    launchUrl(Uri.parse('$baseUrl$path'), mode: LaunchMode.externalApplication);

/// Who consents to the patient's health data; null if the person cancels.
Future<Map<String, dynamic>?> askPatientConsent(BuildContext context) async {
  final basis = await showDialog<String>(
    context: context,
    builder: (c) => SimpleDialog(
      title: const Text('¿Quién da el consentimiento?'),
      children: [
        const Padding(
          padding: EdgeInsets.symmetric(horizontal: 24),
          child: Text(
            'VIGIA guarda datos de salud solo con el consentimiento del paciente o de su representante.',
          ),
        ),
        SimpleDialogOption(
          onPressed: () => Navigator.pop(c, 'titular'),
          child: const ListTile(title: Text('El propio paciente')),
        ),
        SimpleDialogOption(
          onPressed: () => Navigator.pop(c, 'representante'),
          child: const ListTile(title: Text('Un representante del paciente')),
        ),
      ],
    ),
  );
  if (basis == null || !context.mounted) return null;
  var representative = <String, dynamic>{};
  if (basis == 'representante') {
    final data = await editForm(context, 'Representante', const [
      FormFieldSpec(
        'representative_name',
        'Nombre del representante',
        required: true,
      ),
      FormFieldSpec(
        'representative_relation',
        'Relación con el paciente',
        required: true,
      ),
    ]);
    if (data == null || !context.mounted) return null;
    representative = data;
  }
  final ok = await confirm(
    context,
    'Confirmar consentimiento',
    'Confirmo que cuento con ese consentimiento para registrar estos datos de salud.',
  );
  if (!ok) return null;
  return {'consent_basis': basis, ...representative, 'consent_confirm': true};
}

class ConsentRequiredCard extends StatelessWidget {
  final String baseUrl;
  final VoidCallback onRetry;
  const ConsentRequiredCard({
    super.key,
    required this.baseUrl,
    required this.onRetry,
  });
  @override
  Widget build(BuildContext context) => Card(
    child: Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Acepta la política de privacidad',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700),
          ),
          const SizedBox(height: 8),
          const Text(
            'Para seguir usando VIGIA debes aceptar la política vigente en el portal web. Después vuelve y actualiza.',
          ),
          const SizedBox(height: 12),
          Wrap(
            spacing: 8,
            children: [
              FilledButton(
                onPressed: () => openPortal(baseUrl, '/privacidad/aceptar/'),
                child: const Text('Abrir el portal'),
              ),
              TextButton(onPressed: onRetry, child: const Text('Ya la acepté')),
            ],
          ),
        ],
      ),
    ),
  );
}
