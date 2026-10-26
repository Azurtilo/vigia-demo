import 'package:flutter/material.dart';

import '../../shared/vigia_design.dart';

class PostureHub extends StatelessWidget {
  final void Function(int) choosePatient;
  const PostureHub({super.key, required this.choosePatient});
  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.stretch,
    children: [
      Text(
        'Posturas y cuidados',
        style: Theme.of(context).textTheme.headlineLarge,
      ),
      const SizedBox(height: 8),
      const Text(
        'Guías de postura, reloj de cuidados y análisis local con MediaPipe.',
        style: TextStyle(color: VigiaColors.muted, height: 1.5),
      ),
      const SizedBox(height: 22),
      Container(
        padding: const EdgeInsets.all(5),
        decoration: BoxDecoration(
          color: const Color(0xffedf0f8),
          borderRadius: BorderRadius.circular(18),
        ),
        child: Row(
          children: [
            for (final entry in const [
              (1, 'Guías', Icons.menu_book_outlined),
              (4, 'Reloj', Icons.schedule),
              (3, 'Cámara', Icons.camera_alt_outlined),
            ])
              Expanded(
                child: TextButton(
                  onPressed: () => choosePatient(entry.$1),
                  style: TextButton.styleFrom(
                    foregroundColor: VigiaColors.brand,
                    backgroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(
                      vertical: 12,
                      horizontal: 4,
                    ),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(13),
                    ),
                  ),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(entry.$3, size: 18),
                      const SizedBox(height: 5),
                      Text(
                        entry.$2,
                        style: const TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
          ],
        ),
      ),
      const SizedBox(height: 20),
      Container(
        padding: const EdgeInsets.all(18),
        decoration: BoxDecoration(
          color: const Color(0xffe7eff8),
          borderRadius: BorderRadius.circular(20),
        ),
        child: const Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(Icons.info_outline, size: 19, color: VigiaColors.brand),
            SizedBox(width: 12),
            Expanded(
              child: Text(
                'Orientación y apoyo. Selecciona al paciente para consultar sus guías, programar el próximo cuidado o analizar una postura. Sigue siempre su plan individual de cuidados.',
                style: TextStyle(fontSize: 13, height: 1.6),
              ),
            ),
          ],
        ),
      ),
      const SizedBox(height: 18),
      for (final entry in const [
        (
          1,
          'Guías de postura',
          'Orientación y registro de cambios realizados',
          Icons.accessibility_new,
        ),
        (
          4,
          'Reloj de cuidados',
          'Intervalos de 60, 90 o 120 minutos',
          Icons.alarm_outlined,
        ),
        (
          3,
          'Cámara y MediaPipe',
          'Teléfono y cámara fija · Premium',
          Icons.camera_alt_outlined,
        ),
      ])
        Card(
          margin: const EdgeInsets.only(bottom: 14),
          child: ListTile(
            contentPadding: const EdgeInsets.all(18),
            leading: Icon(entry.$4, color: VigiaColors.brand),
            title: Text(
              entry.$2,
              style: const TextStyle(fontWeight: FontWeight.w700),
            ),
            subtitle: Text(entry.$3),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => choosePatient(entry.$1),
          ),
        ),
    ],
  );
}
