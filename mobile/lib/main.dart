import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'app.dart';
import 'core/config/app_config.dart';
import 'core/firebase/firebase_setup.dart';
import 'core/network/api_client.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final config = AppConfig.fromEnvironment();
  await initFirebase(config);
  runApp(
    ProviderScope(
      overrides: [appConfigProvider.overrideWithValue(config)],
      retry: retryOnlyConnectivity,
      child: const VigiaApp(),
    ),
  );
}
