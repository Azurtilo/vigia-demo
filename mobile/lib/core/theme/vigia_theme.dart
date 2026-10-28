import 'package:flutter/material.dart';

import 'vigia_colors.dart';

/// Tema Material 3 con la paleta y tipografía aprobadas.
/// Áreas táctiles de al menos 48 px; cuerpo de texto 16.
ThemeData buildVigiaTheme() {
  const scheme = ColorScheme(
    brightness: Brightness.light,
    primary: VigiaColors.primary,
    onPrimary: Colors.white,
    primaryContainer: VigiaColors.primarySoft,
    onPrimaryContainer: VigiaColors.ink,
    secondary: VigiaColors.mintInk,
    onSecondary: Colors.white,
    secondaryContainer: VigiaColors.mint,
    onSecondaryContainer: VigiaColors.ink,
    tertiary: VigiaColors.lavender,
    onTertiary: VigiaColors.ink,
    error: VigiaColors.risk,
    onError: Colors.white,
    errorContainer: VigiaColors.riskSoft,
    onErrorContainer: VigiaColors.risk,
    surface: VigiaColors.surface,
    onSurface: VigiaColors.ink,
    onSurfaceVariant: VigiaColors.inkMuted,
    outline: VigiaColors.outline,
  );

  final base = ThemeData(useMaterial3: true, colorScheme: scheme, fontFamily: 'Nunito');
  final buttonShape = RoundedRectangleBorder(borderRadius: BorderRadius.circular(14));
  const buttonText = TextStyle(fontFamily: 'Nunito', fontSize: 17, fontWeight: FontWeight.w700);

  return base.copyWith(
    scaffoldBackgroundColor: VigiaColors.background,
    textTheme: base.textTheme.copyWith(
      headlineMedium: const TextStyle(fontSize: 28, fontWeight: FontWeight.w800, color: VigiaColors.ink),
      titleLarge: const TextStyle(fontSize: 20, fontWeight: FontWeight.w700, color: VigiaColors.ink),
      bodyLarge: const TextStyle(fontSize: 16, color: VigiaColors.ink),
      bodyMedium: const TextStyle(fontSize: 16, color: VigiaColors.ink),
      labelLarge: const TextStyle(fontSize: 15, fontWeight: FontWeight.w700),
    ),
    appBarTheme: const AppBarTheme(
      backgroundColor: VigiaColors.background,
      foregroundColor: VigiaColors.ink,
      elevation: 0,
      titleTextStyle: TextStyle(fontFamily: 'Nunito', fontSize: 22, fontWeight: FontWeight.w800, color: VigiaColors.ink),
    ),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(minimumSize: const Size.fromHeight(52), shape: buttonShape, textStyle: buttonText),
    ),
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(
        minimumSize: const Size.fromHeight(52),
        shape: buttonShape,
        textStyle: buttonText,
        side: const BorderSide(color: VigiaColors.primary, width: 2),
      ),
    ),
    textButtonTheme: TextButtonThemeData(
      style: TextButton.styleFrom(minimumSize: const Size(48, 48), textStyle: buttonText.copyWith(fontSize: 15)),
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: VigiaColors.surface,
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
      border: OutlineInputBorder(borderRadius: BorderRadius.circular(14)),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(14),
        borderSide: const BorderSide(color: VigiaColors.outline, width: 1.5),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(14),
        borderSide: const BorderSide(color: VigiaColors.primary, width: 2),
      ),
      labelStyle: const TextStyle(color: VigiaColors.inkMuted),
    ),
    navigationBarTheme: NavigationBarThemeData(
      backgroundColor: VigiaColors.surface,
      indicatorColor: VigiaColors.primarySoft,
      labelTextStyle: WidgetStateProperty.resolveWith(
        (states) => TextStyle(
          fontFamily: 'Nunito',
          fontSize: 13,
          fontWeight: states.contains(WidgetState.selected) ? FontWeight.w800 : FontWeight.w700,
          color: states.contains(WidgetState.selected) ? VigiaColors.primary : VigiaColors.inkMuted,
        ),
      ),
      iconTheme: WidgetStateProperty.resolveWith(
        (states) => IconThemeData(
          color: states.contains(WidgetState.selected) ? VigiaColors.primary : VigiaColors.inkMuted,
        ),
      ),
    ),
  );
}
