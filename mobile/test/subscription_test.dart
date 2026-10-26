import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:vigia_mobile/features/subscription/subscription_panel.dart';
import 'package:vigia_mobile/shared/vigia_design.dart';

void main() {
  final caps = <String, dynamic>{
    'plan': 'plus',
    'name': 'VIGIA Plus',
    'plans': [
      {
        'code': 'free',
        'name': 'VIGIA Free',
        'price_clp': 0,
        'description': 'Un paciente',
        'max_active_patients': 1,
        'benefits': ['Agenda'],
      },
      {
        'code': 'plus',
        'name': 'VIGIA Plus',
        'price_clp': 4990,
        'description': 'Tres pacientes',
        'max_active_patients': 3,
        'benefits': ['Agenda'],
      },
      {
        'code': 'pro',
        'name': 'VIGIA Premium',
        'price_clp': 9990,
        'description': 'Sin límite',
        'max_active_patients': null,
        'benefits': ['Cámara'],
      },
    ],
  };
  testWidgets(
    'Web catalog prices are shown and change only opens external portal',
    (tester) async {
      tester.view.physicalSize = const Size(390, 844);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      final opened = <Uri>[];
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ListView(
              children: [
                SubscriptionPanel(
                  caps: caps,
                  baseUrl: 'https://vigia.example',
                  enableNotifications: () {},
                  openPortal: (uri) async {
                    opened.add(uri);
                    return true;
                  },
                ),
              ],
            ),
          ),
        ),
      );
      expect(find.text('VIGIA Free'), findsOneWidget);
      expect(find.text('VIGIA Plus'), findsOneWidget);
      expect(find.text('VIGIA Premium'), findsOneWidget);
      expect(find.text('\$4.990'), findsOneWidget);
      expect(find.text('\$9.990'), findsOneWidget);
      await tester.tap(find.text('Cambiar plan'));
      await tester.pumpAndSettle();
      final change = find.text('Cambiar plan en la web');
      await tester.drag(find.byType(ListView), const Offset(0, -1800));
      await tester.pumpAndSettle();
      await tester.ensureVisible(change);
      await tester.pumpAndSettle();
      await tester.tap(change);
      await tester.pumpAndSettle();
      expect(opened, [
        Uri.parse('https://vigia.example/planes/'),
        Uri.parse('https://vigia.example/planes/'),
      ]);
      expect(opened.every((uri) => !uri.hasQuery), isTrue);
      expect(caps['plan'], 'plus');
      expect(tester.takeException(), isNull);
    },
  );
  testWidgets(
    'All six destinations fit 320px without horizontal navigation scrolling',
    (tester) async {
      tester.view.physicalSize = const Size(320, 700);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      var selected = -1;
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            bottomNavigationBar: CareBottomBar(
              selected: 0,
              onSelected: (i) => selected = i,
              patients: 2,
              medicines: 3,
            ),
          ),
        ),
      );
      await tester.tap(find.text('Perfil'));
      expect(selected, 5);
      expect(find.text('Planes'), findsOneWidget);
      expect(tester.takeException(), isNull);
    },
  );
}
