import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'core/router/app_router.dart';
import 'core/theme/vigia_theme.dart';

class VigiaApp extends ConsumerWidget {
  const VigiaApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return MaterialApp.router(
      title: 'VIGIA',
      debugShowCheckedModeBanner: false,
      theme: buildVigiaTheme(),
      routerConfig: ref.watch(routerProvider),
      locale: const Locale('es', 'CL'),
      supportedLocales: const [Locale('es', 'CL'), Locale('es')],
      localizationsDelegates: GlobalMaterialLocalizations.delegates,
    );
  }
}
