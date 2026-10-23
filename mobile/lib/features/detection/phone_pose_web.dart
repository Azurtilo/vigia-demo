import 'package:flutter/material.dart';

import '../../core/api.dart';

class PhonePoseScreen extends StatelessWidget {
  final VigiaApi api;
  final int patientId;
  const PhonePoseScreen({
    super.key,
    required this.api,
    required this.patientId,
  });
  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Cámara del teléfono')),
    body: const Padding(
      padding: EdgeInsets.all(24),
      child: Text(
        'El análisis local con MediaPipe requiere la aplicación Android o iOS. La vista previa web permite revisar los demás flujos.',
      ),
    ),
  );
}
