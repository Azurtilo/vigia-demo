import 'package:flutter/material.dart';

/// Paleta aprobada (docs/diseno-visual.md, ADR 027). Contrastes medidos con WCAG 2.
///
/// Regla: los tonos claros son fondos con texto oscuro; las acciones usan el tono oscuro.
abstract final class VigiaColors {
  static const background = Color(0xFFF4F0FC); // tinta 13,0:1
  static const surface = Color(0xFFFFFFFF);
  static const primary = Color(0xFF5E4BA3); // blanco 7,0:1
  static const primaryPressed = Color(0xFF4A3A86);
  static const primarySoft = Color(0xFFE9E2F8); // primary 5,6:1
  static const lavender = Color(0xFFC6B2EC); // tinta 7,6:1
  static const mint = Color(0xFFA9E6CC);
  static const mintInk = Color(0xFF1E6B52); // sobre menta 4,5:1
  static const sky = Color(0xFFDCEEF8);
  static const rose = Color(0xFFF7E1EC);
  static const roseInk = Color(0xFF7A2E50);
  static const ink = Color(0xFF2B2541); // 13,0:1
  static const inkMuted = Color(0xFF5A5370); // 6,4:1
  static const outline = Color(0xFF8F86AE); // borde de campos 3,4:1 (no texto)
  static const risk = Color(0xFFB3261E);
  static const riskSoft = Color(0xFFFBE4E2); // risk 5,4:1
  static const attention = Color(0xFF7A4F00);
  static const attentionSoft = Color(0xFFFCEBC8); // attention 6,1:1
}
