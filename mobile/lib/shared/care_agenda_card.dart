import 'package:flutter/material.dart';

import 'care_widgets.dart';
import 'vigia_design.dart';

class CareAgendaCard extends StatelessWidget {
  final Map<String, dynamic> item;
  final bool busy;
  final VoidCallback onDone, onOmit;
  const CareAgendaCard({
    super.key,
    required this.item,
    required this.busy,
    required this.onDone,
    required this.onOmit,
  });
  @override
  Widget build(BuildContext context) {
    final done = item['status'] == 'done';
    final omitted = item['status'] == 'omitted';
    final overdue = item['overdue'] == true && !done && !omitted;
    final tone = done
        ? const Color(0xffdfeee7)
        : overdue
        ? const Color(0xfffae8e6)
        : const Color(0xffeeebf8);
    final ink = done
        ? const Color(0xff376853)
        : overdue
        ? const Color(0xff9b4137)
        : VigiaColors.brand;
    final due = DateTime.tryParse(item['due']?.toString() ?? '')?.toLocal();
    final clock = due == null
        ? '—'
        : '${due.hour.toString().padLeft(2, '0')}:${due.minute.toString().padLeft(2, '0')}';
    return Card(
      margin: const EdgeInsets.only(bottom: 16),
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  width: 65,
                  padding: const EdgeInsets.symmetric(vertical: 12),
                  decoration: BoxDecoration(
                    color: tone,
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: Column(
                    children: [
                      Text(
                        clock,
                        style: TextStyle(
                          fontSize: 15,
                          fontWeight: FontWeight.w800,
                          color: ink,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Icon(
                        item['kind'] == 'medication'
                            ? Icons.medication_outlined
                            : Icons.volunteer_activism_outlined,
                        size: 17,
                        color: ink,
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        item['label'],
                        style: const TextStyle(
                          fontSize: 17,
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                      if (item['dose'] != null && item['dose'] != '')
                        Padding(
                          padding: const EdgeInsets.only(top: 5),
                          child: Text(
                            item['dose'],
                            style: const TextStyle(
                              color: VigiaColors.muted,
                              fontSize: 12,
                            ),
                          ),
                        ),
                      const SizedBox(height: 8),
                      Text(
                        item['patient'],
                        style: const TextStyle(
                          color: VigiaColors.muted,
                          fontSize: 12,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 14),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              crossAxisAlignment: WrapCrossAlignment.center,
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 10,
                    vertical: 6,
                  ),
                  decoration: BoxDecoration(
                    color: tone,
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Text(
                    done
                        ? 'Administrado / realizado'
                        : omitted
                        ? 'Omitido con motivo'
                        : overdue
                        ? 'Atrasado'
                        : 'Pendiente',
                    style: TextStyle(
                      color: ink,
                      fontSize: 11,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ),
                Text(
                  when(item['due']),
                  style: const TextStyle(
                    color: VigiaColors.muted,
                    fontSize: 11,
                  ),
                ),
              ],
            ),
            if (!done && !omitted) ...[
              const SizedBox(height: 14),
              Wrap(
                spacing: 8,
                runSpacing: 6,
                children: [
                  FilledButton(
                    onPressed: busy ? null : onDone,
                    child: Text(
                      item['kind'] == 'medication'
                          ? 'Marcar administrado'
                          : 'Marcar realizado',
                    ),
                  ),
                  TextButton(
                    onPressed: busy ? null : onOmit,
                    child: const Text('Omitir con motivo'),
                  ),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }
}
