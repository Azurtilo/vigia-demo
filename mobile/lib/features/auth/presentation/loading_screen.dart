import 'package:flutter/material.dart';

import '../../../core/widgets/vigia_logo.dart';

class LoadingScreen extends StatelessWidget {
  const LoadingScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      body: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            VigiaLogo(size: 112),
            SizedBox(height: 24),
            CircularProgressIndicator(semanticsLabel: 'Cargando'),
          ],
        ),
      ),
    );
  }
}
