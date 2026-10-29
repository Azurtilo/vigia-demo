import 'package:flutter/material.dart';

import '../theme/vigia_colors.dart';
import 'vigia_logo.dart';

/// Estructura común de las pantallas de cuenta: logo, título y contenido desplazable
/// (cabe en teléfonos pequeños y con letra grande).
class FormPage extends StatelessWidget {
  const FormPage({super.key, required this.title, required this.children, this.subtitle, this.showBack = false});

  final String title;
  final String? subtitle;
  final List<Widget> children;
  final bool showBack;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: showBack ? AppBar() : null,
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.fromLTRB(24, 24, 24, 32),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 440),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const Center(child: VigiaLogo(size: 88)),
                  const SizedBox(height: 16),
                  Text(title, textAlign: TextAlign.center, style: Theme.of(context).textTheme.headlineMedium),
                  if (subtitle != null) ...[
                    const SizedBox(height: 8),
                    Text(
                      subtitle!,
                      textAlign: TextAlign.center,
                      style: const TextStyle(fontSize: 16, color: VigiaColors.inkMuted),
                    ),
                  ],
                  const SizedBox(height: 28),
                  ...children,
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

/// Mensaje de error visible (rojo de riesgo + ícono, no solo color).
class ErrorBanner extends StatelessWidget {
  const ErrorBanner(this.message, {super.key});
  final String message;

  @override
  Widget build(BuildContext context) {
    return Semantics(
      liveRegion: true,
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(color: VigiaColors.riskSoft, borderRadius: BorderRadius.circular(14)),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Icon(Icons.error_outline, color: VigiaColors.risk),
            const SizedBox(width: 10),
            Expanded(child: Text(message, style: const TextStyle(color: VigiaColors.risk, fontWeight: FontWeight.w600))),
          ],
        ),
      ),
    );
  }
}

/// Validaciones de formularios compartidas.
abstract final class Validators {
  static final _email = RegExp(r'^[^@\s]+@[^@\s]+\.[^@\s]+$');

  static String? email(String? value) {
    final v = value?.trim() ?? '';
    if (v.isEmpty) return 'Escribe tu correo.';
    if (!_email.hasMatch(v)) return 'El correo no tiene un formato válido.';
    return null;
  }

  static String? password(String? value) {
    if ((value ?? '').length < 8) return 'La contraseña debe tener al menos 8 caracteres.';
    return null;
  }

  static String? required(String? value, String message) => (value?.trim() ?? '').isEmpty ? message : null;
}
