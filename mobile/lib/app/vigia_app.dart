import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';

import '../core/api.dart';
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
      colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xff5057a0)),
      scaffoldBackgroundColor: const Color(0xfff6f7fc),
      appBarTheme: const AppBarTheme(
        backgroundColor: Color(0xfff6f7fc),
        foregroundColor: Color(0xff252a38),
      ),
      cardTheme: CardThemeData(
        color: Colors.white,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(22),
          side: const BorderSide(color: Color(0xffe3e5ef)),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: Colors.white,
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(14)),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(minimumSize: const Size(48, 52)),
      ),
      textTheme: const TextTheme(
        headlineLarge: TextStyle(
          fontSize: 32,
          fontWeight: FontWeight.w700,
          color: Color(0xff252a38),
        ),
      ),
    ),
    home: SessionGate(api: api),
  );
}
