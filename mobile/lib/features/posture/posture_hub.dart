import 'package:flutter/material.dart';

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
        'Selecciona una persona para ver sus guías, reloj y observaciones.',
      ),
      const SizedBox(height: 20),
      Card(
        child: ListTile(
          leading: const Icon(Icons.menu_book_outlined),
          title: const Text('Guías de postura'),
          subtitle: const Text('Orientación y registro de cambios realizados'),
          onTap: () => choosePatient(1),
        ),
      ),
      Card(
        child: ListTile(
          leading: const Icon(Icons.timer_outlined),
          title: const Text('Reloj de cuidados'),
          subtitle: const Text('Intervalos de 60, 90 o 120 minutos'),
          onTap: () => choosePatient(4),
        ),
      ),
      Card(
        child: ListTile(
          leading: const Icon(Icons.camera_alt_outlined),
          title: const Text('Cámara y MediaPipe'),
          subtitle: const Text('Teléfono y cámara fija · Premium'),
          onTap: () => choosePatient(3),
        ),
      ),
    ],
  );
}
