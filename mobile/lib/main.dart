import 'package:flutter/material.dart';

import 'core/api.dart';
import 'app/vigia_app.dart';
export 'app/vigia_app.dart';
export 'features/auth/login_screen.dart';
export 'features/auth/session_gate.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(VigiaApp(api: VigiaApi()));
}
