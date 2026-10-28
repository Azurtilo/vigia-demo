import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/agenda_api.dart';
import '../domain/agenda.dart';

/// Día elegido en "Hoy". Null = hoy según la zona horaria del paciente (lo decide el backend).
class SelectedDayController extends Notifier<DateTime?> {
  @override
  DateTime? build() => null;

  void set(DateTime? day) => state = day;
}

final selectedDayProvider = NotifierProvider<SelectedDayController, DateTime?>(SelectedDayController.new);

typedef AgendaKey = ({String patientId, DateTime? day});

final agendaProvider = FutureProvider.autoDispose.family<Agenda, AgendaKey>(
  (ref, key) => ref.watch(agendaApiProvider).agenda(key.patientId, day: key.day),
);

final memberNamesProvider = FutureProvider.autoDispose.family<Map<String, String>, String>(
  (ref, patientId) => ref.watch(agendaApiProvider).memberNames(patientId),
);
