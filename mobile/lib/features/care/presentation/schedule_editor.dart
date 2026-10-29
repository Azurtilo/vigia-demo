import 'package:flutter/material.dart';

import '../../../core/theme/vigia_colors.dart';

/// Horas fijas (hora local del paciente) y días de la semana. Sin días marcados = todos los días.
/// La app no propone frecuencias: las define el responsable del tratamiento o del cuidado.
class ScheduleEditor extends StatelessWidget {
  const ScheduleEditor({
    super.key,
    required this.times,
    required this.days,
    required this.onTimesChanged,
    required this.onDaysChanged,
    this.errorText,
  });

  final List<String> times;
  final List<int> days;
  final ValueChanged<List<String>> onTimesChanged;
  final ValueChanged<List<int>> onDaysChanged;
  final String? errorText;

  static const _dayLetters = ['L', 'M', 'X', 'J', 'V', 'S', 'D'];
  static const _dayNames = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo'];

  Future<void> _addTime(BuildContext context) async {
    // Siempre 24 horas, como la agenda: con el teléfono en 12 horas el modo teclado rechazaba «20» (T-019-20).
    final picked = await showTimePicker(
      context: context,
      initialTime: const TimeOfDay(hour: 8, minute: 0),
      helpText: 'Agregar hora',
      builder: (context, child) => MediaQuery(
        data: MediaQuery.of(context).copyWith(alwaysUse24HourFormat: true),
        child: child!,
      ),
    );
    if (picked == null) return;
    final value = '${picked.hour.toString().padLeft(2, '0')}:${picked.minute.toString().padLeft(2, '0')}';
    if (times.contains(value) || times.length >= 12) return;
    onTimesChanged([...times, value]..sort());
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        const Text('Horas', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
        const SizedBox(height: 8),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
            for (final t in times)
              InputChip(
                label: Text(t, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
                deleteButtonTooltipMessage: 'Quitar $t',
                onDeleted: () => onTimesChanged([...times]..remove(t)),
              ),
            ActionChip(
              key: const Key('add-time'),
              avatar: const Icon(Icons.add, size: 18),
              label: const Text('Agregar hora'),
              onPressed: () => _addTime(context),
            ),
          ],
        ),
        if (errorText != null)
          Padding(
            padding: const EdgeInsets.only(top: 6),
            child: Text(errorText!, style: const TextStyle(color: VigiaColors.risk, fontWeight: FontWeight.w600)),
          ),
        const SizedBox(height: 16),
        const Text('Días', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
        const SizedBox(height: 8),
        Wrap(
          spacing: 6,
          runSpacing: 6,
          children: [
            for (var i = 1; i <= 7; i++)
              Semantics(
                label: _dayNames[i - 1],
                child: FilterChip(
                  label: Text(_dayLetters[i - 1]),
                  selected: days.contains(i),
                  showCheckmark: false,
                  materialTapTargetSize: MaterialTapTargetSize.padded,
                  onSelected: (on) => onDaysChanged(on ? ([...days, i]..sort()) : ([...days]..remove(i))),
                ),
              ),
          ],
        ),
        const SizedBox(height: 6),
        Text(
          days.isEmpty || days.length == 7 ? 'Todos los días' : 'Solo los días marcados',
          style: const TextStyle(fontSize: 14, color: VigiaColors.inkMuted),
        ),
      ],
    );
  }
}

/// Selector de fecha en un botón (inicio / término de un tratamiento o tarea).
class DateButton extends StatelessWidget {
  const DateButton({super.key, required this.label, required this.value, required this.onChanged, this.allowClear = false});
  final String label;
  final DateTime? value;
  final ValueChanged<DateTime?> onChanged;
  final bool allowClear;

  @override
  Widget build(BuildContext context) {
    final text = value == null
        ? label
        : '$label: ${value!.day.toString().padLeft(2, '0')}-${value!.month.toString().padLeft(2, '0')}-${value!.year}';
    return Row(
      children: [
        Expanded(
          child: OutlinedButton.icon(
            onPressed: () async {
              final now = DateTime.now();
              final picked = await showDatePicker(
                context: context,
                initialDate: value ?? now,
                firstDate: DateTime(now.year - 5),
                lastDate: DateTime(now.year + 5),
                helpText: label,
              );
              if (picked != null) onChanged(picked);
            },
            icon: const Icon(Icons.event_outlined),
            label: Text(text),
          ),
        ),
        if (allowClear && value != null)
          IconButton(tooltip: 'Quitar $label', onPressed: () => onChanged(null), icon: const Icon(Icons.close)),
      ],
    );
  }
}
