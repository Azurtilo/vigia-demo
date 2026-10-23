import 'package:flutter/material.dart';

class MedicineFilters extends StatelessWidget {
  final String value;
  final ValueChanged<String> onChanged;
  const MedicineFilters({
    super.key,
    required this.value,
    required this.onChanged,
  });
  @override
  Widget build(BuildContext context) => Wrap(
    spacing: 8,
    children: [
      for (final entry in const {
        'all': 'Todos',
        'pending': 'Pendientes',
        'done': 'Administrados',
        'overdue': 'Atrasados',
        'omitted': 'Omitidos',
      }.entries)
        ChoiceChip(
          label: Text(entry.value),
          selected: value == entry.key,
          onSelected: (_) => onChanged(entry.key),
        ),
    ],
  );
}
