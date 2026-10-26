import 'package:flutter/material.dart';

abstract final class VigiaColors {
  static const brand = Color(0xff5057a0);
  static const page = Color(0xfff7f8fd);
  static const ink = Color(0xff293139);
  static const muted = Color(0xff657183);
  static const line = Color(0xffe6e9f1);
  static const lavender = Color(0xffeee9f7);
}

class PlanPill extends StatelessWidget {
  final String label;
  const PlanPill(this.label, {super.key});
  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
    decoration: BoxDecoration(
      color: VigiaColors.lavender,
      borderRadius: BorderRadius.circular(20),
    ),
    child: Text(
      label,
      style: const TextStyle(
        fontSize: 10,
        fontWeight: FontWeight.w800,
        letterSpacing: .6,
        color: Color(0xff665183),
      ),
    ),
  );
}

class CareBottomBar extends StatelessWidget {
  final int selected, patients, medicines;
  final ValueChanged<int> onSelected;
  const CareBottomBar({
    super.key,
    required this.selected,
    required this.onSelected,
    this.patients = 0,
    this.medicines = 0,
  });
  @override
  Widget build(BuildContext context) => Container(
    decoration: const BoxDecoration(
      color: Colors.white,
      border: Border(top: BorderSide(color: VigiaColors.line)),
    ),
    child: SafeArea(
      top: false,
      child: Row(
        children: [
          for (var i = 0; i < 6; i++)
            Expanded(
              child: Semantics(
                selected: selected == i,
                child: InkWell(
                  onTap: () => onSelected(i),
                  child: Padding(
                    padding: const EdgeInsets.symmetric(vertical: 11),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Badge(
                          isLabelVisible:
                              (i == 1 && patients > 0) ||
                              (i == 2 && medicines > 0),
                          backgroundColor: VigiaColors.brand,
                          label: Text(
                            '${i == 1 ? patients : medicines}',
                            style: const TextStyle(fontSize: 8),
                          ),
                          child: Icon(
                            const [
                              Icons.home_outlined,
                              Icons.people_outline,
                              Icons.medication_outlined,
                              Icons.monitor_heart_outlined,
                              Icons.auto_awesome_outlined,
                              Icons.person_outline,
                            ][i],
                            size: 23,
                            color: selected == i
                                ? VigiaColors.brand
                                : VigiaColors.muted,
                          ),
                        ),
                        const SizedBox(height: 5),
                        Text(
                          const [
                            'Inicio',
                            'Pacientes',
                            'Medicinas',
                            'Posturas',
                            'Planes',
                            'Perfil',
                          ][i],
                          maxLines: 1,
                          style: TextStyle(
                            fontSize: 10,
                            fontWeight: selected == i
                                ? FontWeight.w700
                                : FontWeight.w500,
                            color: selected == i
                                ? VigiaColors.brand
                                : VigiaColors.muted,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Container(
                          width: 4,
                          height: 4,
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            color: selected == i
                                ? VigiaColors.brand
                                : Colors.transparent,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
        ],
      ),
    ),
  );
}
