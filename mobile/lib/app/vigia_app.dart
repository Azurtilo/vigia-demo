import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';

import '../core/api.dart';
import '../shared/vigia_design.dart';
import '../features/auth/session_gate.dart';

class VigiaApp extends StatelessWidget {
  final VigiaApi api;
  const VigiaApp({super.key, required this.api});
  @override
  Widget build(BuildContext context) => MaterialApp(
    title: 'VIGIA',
    debugShowCheckedModeBanner: false,
    locale: const Locale('es', 'CL'),
    supportedLocales: const [Locale('es', 'CL')],
    localizationsDelegates: GlobalMaterialLocalizations.delegates,
    theme: ThemeData(
      useMaterial3: true,
      colorScheme: ColorScheme.fromSeed(seedColor: VigiaColors.brand).copyWith(
        primary: VigiaColors.brand,
        surface: Colors.white,
        onSurface: VigiaColors.ink,
        outline: VigiaColors.line,
      ),
      scaffoldBackgroundColor: VigiaColors.page,
      appBarTheme: const AppBarTheme(
        backgroundColor: Color(0xfff6f7fc),
        foregroundColor: Color(0xff252a38),
      ),
      cardTheme: CardThemeData(
        color: Colors.white,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(22),
          side: const BorderSide(color: VigiaColors.line),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: Colors.white,
        contentPadding: const EdgeInsets.symmetric(
          horizontal: 16,
          vertical: 14,
        ),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(18),
          borderSide: const BorderSide(color: VigiaColors.line),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(18),
          borderSide: const BorderSide(color: VigiaColors.line),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(18),
          borderSide: const BorderSide(color: VigiaColors.brand),
        ),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          minimumSize: const Size(48, 44),
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 13),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(24),
          ),
          textStyle: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          side: const BorderSide(color: VigiaColors.line),
          foregroundColor: VigiaColors.brand,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(24),
          ),
        ),
      ),
      chipTheme: ChipThemeData(
        side: BorderSide.none,
        backgroundColor: Colors.white,
        selectedColor: VigiaColors.lavender,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
      ),
      textTheme: const TextTheme(
        headlineLarge: TextStyle(
          fontSize: 26,
          fontWeight: FontWeight.w800,
          color: Color(0xff252a38),
        ),
      ),
    ),
    home: SessionGate(api: api),
  );
}
