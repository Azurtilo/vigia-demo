import 'package:flutter/material.dart';

import '../../shared/care_widgets.dart';
import '../../shared/vigia_design.dart';

class HomeOverview extends StatelessWidget {
  final Map<String, dynamic>? me, patients, agenda;
  final bool busy;
  final VoidCallback onProfile, onNewPatient, onJoin, onMedicines, onPostures;
  final VoidCallback onCamera;
  final void Function(Map<String, dynamic>) onPatient;
  const HomeOverview({
    super.key,
    required this.me,
    required this.patients,
    required this.agenda,
    this.busy = false,
    required this.onProfile,
    required this.onNewPatient,
    required this.onJoin,
    required this.onMedicines,
    required this.onPostures,
    required this.onCamera,
    required this.onPatient,
  });
  @override
  Widget build(BuildContext context) {
    final name = (me?['name'] as String? ?? '').trim();
    final first = name.isEmpty ? '' : name.split(' ').first;
    final active = (patients?['patients'] as List? ?? []).where(
      (p) => p['active'] == true,
    );
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    crossAxisAlignment: WrapCrossAlignment.center,
                    children: [
                      Text(
                        'Hola, $first 👋',
                        style: Theme.of(context).textTheme.headlineLarge,
                      ),
                      if (me?['capabilities']?['name'] != null)
                        PlanPill(
                          me!['capabilities']['name']
                              .toString()
                              .replaceFirst('VIGIA ', '')
                              .toUpperCase(),
                        ),
                    ],
                  ),
                  const SizedBox(height: 6),
                  const Text(
                    '¿Cómo podemos ayudarte hoy con el cuidado?',
                    style: TextStyle(color: VigiaColors.muted, height: 1.5),
                  ),
                ],
              ),
            ),
            const SizedBox(width: 10),
            IconButton.filledTonal(
              onPressed: onProfile,
              tooltip: 'Mi perfil',
              style: IconButton.styleFrom(
                backgroundColor: Colors.white,
                side: const BorderSide(color: VigiaColors.line),
              ),
              icon: const Icon(Icons.person_outline, color: VigiaColors.brand),
            ),
          ],
        ),
        const SizedBox(height: 24),
        for (final p in active.take(1))
          _patientCard(context, Map<String, dynamic>.from(p)),
        const SizedBox(height: 24),
        const Text(
          'ACCIONES RÁPIDAS',
          style: TextStyle(
            fontSize: 11,
            letterSpacing: 1.2,
            fontWeight: FontWeight.w700,
            color: VigiaColors.muted,
          ),
        ),
        const SizedBox(height: 14),
        LayoutBuilder(
          builder: (_, constraints) => Wrap(
            spacing: 12,
            runSpacing: 12,
            children: [
              _quick(
                'Registrar\nmedicamento',
                Icons.medication_outlined,
                const Color(0xffe8e6f6),
                onMedicines,
                constraints.maxWidth,
              ),
              _quick(
                'Registrar\npaciente',
                Icons.person_add_alt,
                const Color(0xffe5f1ec),
                onNewPatient,
                constraints.maxWidth,
              ),
              // Spec 013: a familiar or caregiver joins with the owner's code.
              _quick(
                'Unirme con\nun código',
                Icons.key_outlined,
                const Color(0xfff3e9f0),
                onJoin,
                constraints.maxWidth,
              ),
              _quick(
                'Ver\nposturas',
                Icons.visibility_outlined,
                const Color(0xffe6edf8),
                onPostures,
                constraints.maxWidth,
              ),
              _quick(
                'Analizar\npostura IA',
                Icons.auto_awesome_outlined,
                const Color(0xffeee8f7),
                onCamera,
                constraints.maxWidth,
              ),
            ],
          ),
        ),
        const SizedBox(height: 28),
      ],
    );
  }

  Widget _quick(
    String title,
    IconData icon,
    Color color,
    VoidCallback onTap,
    double width,
  ) => SizedBox(
    width: (width - 12) / 2,
    child: Material(
      color: Colors.white,
      borderRadius: BorderRadius.circular(22),
      child: InkWell(
        borderRadius: BorderRadius.circular(22),
        onTap: busy ? null : onTap,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 18),
          child: Row(
            children: [
              Container(
                padding: const EdgeInsets.all(9),
                decoration: BoxDecoration(
                  color: color,
                  borderRadius: BorderRadius.circular(13),
                ),
                child: Icon(icon, color: VigiaColors.brand, size: 21),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  title,
                  style: const TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                    height: 1.4,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    ),
  );

  Widget _patientCard(BuildContext context, Map<String, dynamic> p) {
    final medication = (agenda?['items'] as List? ?? [])
        .where(
          (m) =>
              m['patient_id'] == p['id'] &&
              m['kind'] == 'medication' &&
              m['status'] == 'pending',
        )
        .firstOrNull;
    final birth = DateTime.tryParse(p['birth_date']?.toString() ?? '');
    final now = DateTime.now();
    final age = birth == null
        ? null
        : now.year -
              birth.year -
              ((now.month < birth.month ||
                      now.month == birth.month && now.day < birth.day)
                  ? 1
                  : 0);
    return Card(
      margin: EdgeInsets.zero,
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: () => onPatient(p),
        child: Column(
          children: [
            Container(
              height: 5,
              decoration: const BoxDecoration(
                gradient: LinearGradient(
                  colors: [VigiaColors.brand, Color(0xffbdd7d6)],
                ),
              ),
            ),
            Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                children: [
                  Row(
                    children: [
                      Container(
                        width: 58,
                        height: 64,
                        decoration: BoxDecoration(
                          color: const Color(0xffe8edf6),
                          borderRadius: BorderRadius.circular(18),
                        ),
                        child: const Icon(
                          Icons.person_outline,
                          size: 34,
                          color: VigiaColors.brand,
                        ),
                      ),
                      const SizedBox(width: 14),
                      Expanded(
                        child: Text(
                          p['name'],
                          style: const TextStyle(
                            fontSize: 19,
                            fontWeight: FontWeight.w800,
                          ),
                        ),
                      ),
                      if (age != null)
                        Container(
                          padding: const EdgeInsets.all(9),
                          decoration: BoxDecoration(
                            color: const Color(0xfff3e9f0),
                            borderRadius: BorderRadius.circular(20),
                          ),
                          child: Text(
                            '$age\naños',
                            textAlign: TextAlign.center,
                            style: const TextStyle(
                              fontSize: 11,
                              color: Color(0xff795777),
                            ),
                          ),
                        ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  Container(
                    padding: const EdgeInsets.all(13),
                    decoration: BoxDecoration(
                      color: VigiaColors.page,
                      borderRadius: BorderRadius.circular(16),
                    ),
                    child: Row(
                      children: [
                        const Icon(
                          Icons.schedule,
                          size: 17,
                          color: VigiaColors.brand,
                        ),
                        const SizedBox(width: 10),
                        Expanded(
                          child: Text(
                            medication == null
                                ? 'Ficha, horarios y contacto'
                                : 'Medicación pendiente:\n${medication['label']} · ${when(medication['due'])}',
                            style: const TextStyle(fontSize: 12, height: 1.4),
                          ),
                        ),
                        const SizedBox(width: 8),
                        const Text(
                          'Ver ficha\n→',
                          style: TextStyle(
                            color: VigiaColors.brand,
                            fontSize: 12,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
