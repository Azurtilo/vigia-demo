import 'dart:async';

import 'package:flutter/material.dart';

import '../../core/api.dart';
import '../../shared/care_widgets.dart';

class ClockPanel extends StatefulWidget {
  final VigiaApi api;
  final Map<String, dynamic>? timer;
  final bool busy;
  final void Function(String) onAction;
  const ClockPanel({
    super.key,
    required this.api,
    required this.timer,
    required this.busy,
    required this.onAction,
  });
  @override
  State<ClockPanel> createState() => _ClockPanelState();
}

class _ClockPanelState extends State<ClockPanel> {
  Timer? ticker;
  @override
  void initState() {
    super.initState();
    ticker = Timer.periodic(const Duration(seconds: 1), (_) {
      if (mounted) setState(() {});
    });
  }

  @override
  void dispose() {
    ticker?.cancel();
    super.dispose();
  }

  Future<void> permission(bool enable) async {
    try {
      if (enable) {
        await widget.api.enableLocalReminders();
      } else {
        await widget.api.disableLocalReminders();
      }
    } catch (e) {
      if (mounted) notice(context, e);
    }
  }

  @override
  Widget build(BuildContext context) {
    final timer = widget.timer;
    final due = DateTime.tryParse(timer?['next_due_at']?.toString() ?? '');
    final seconds = due?.difference(DateTime.now()).inSeconds;
    final remaining = seconds == null
        ? ''
        : seconds <= 0
        ? 'Cuidado pendiente'
        : '${(seconds ~/ 3600).toString().padLeft(2, '0')}:${((seconds % 3600) ~/ 60).toString().padLeft(2, '0')}:${(seconds % 60).toString().padLeft(2, '0')}';
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        const Text(
          'Programa el próximo cuidado sin registrarlo como realizado.',
        ),
        Card(
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                if (timer == null) ...[
                  const Text('Aún no tienes un reloj para este paciente.'),
                  const SizedBox(height: 16),
                  FilledButton.icon(
                    onPressed: widget.busy
                        ? null
                        : () => widget.onAction('start'),
                    icon: const Icon(Icons.alarm_add),
                    label: const Text('Crear recordatorio'),
                  ),
                ] else ...[
                  Text(
                    timer['paused'] == true
                        ? 'Recordatorios pausados'
                        : remaining,
                    style: Theme.of(context).textTheme.headlineMedium,
                  ),
                  const SizedBox(height: 8),
                  Text('Intervalo: ${timer['interval']} minutos'),
                  if (timer['paused'] != true)
                    Text('Próximo cambio: ${when(timer['next_due_at'])}'),
                  Wrap(
                    spacing: 12,
                    children: [
                      TextButton(
                        onPressed: widget.busy
                            ? null
                            : () => widget.onAction(
                                timer['paused'] == true ? 'resume' : 'pause',
                              ),
                        child: Text(
                          timer['paused'] == true ? 'Reanudar' : 'Pausar',
                        ),
                      ),
                      TextButton(
                        onPressed: widget.busy
                            ? null
                            : () => widget.onAction('interval'),
                        child: const Text('Cambiar intervalo'),
                      ),
                    ],
                  ),
                ],
              ],
            ),
          ),
        ),
        ValueListenableBuilder<String>(
          valueListenable: widget.api.reminders.status,
          builder: (_, value, child) => Text(value),
        ),
        Wrap(
          spacing: 12,
          children: [
            TextButton.icon(
              onPressed: () => permission(true),
              icon: const Icon(Icons.notifications_active_outlined),
              label: const Text('Activar avisos en este teléfono'),
            ),
            TextButton(
              onPressed: () => permission(false),
              child: const Text('Desactivar avisos locales'),
            ),
          ],
        ),
        const Text(
          'El sonido depende de los ajustes del teléfono. Si cambias el reloj desde la web, abre la app con conexión para actualizar sus avisos.',
        ),
      ],
    );
  }
}
