import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';

/// Logo oficial (assets/branding/07_icono_app.svg).
class VigiaLogo extends StatelessWidget {
  const VigiaLogo({super.key, this.size = 96});
  final double size;

  @override
  Widget build(BuildContext context) => SvgPicture.asset(
        'assets/branding/07_icono_app.svg',
        width: size,
        height: size,
        semanticsLabel: 'Logo de VIGIA',
      );
}
