import 'package:flutter/material.dart';

import '../../shared/vigia_design.dart';
import 'access.dart';

class PatientSummaryCard extends StatelessWidget {
  final Map<String, dynamic> patient;
  final VoidCallback onOpen;
  const PatientSummaryCard({
    super.key,
    required this.patient,
    required this.onOpen,
  });
  @override
  Widget build(BuildContext context) {
    final active = patient['active'] == true;
    final role = patient['role'];
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(24),
        border: Border.all(
          color: active ? VigiaColors.brand : VigiaColors.line,
        ),
      ),
      child: InkWell(
        borderRadius: BorderRadius.circular(24),
        onTap: onOpen,
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Container(
                    width: 58,
                    height: 66,
                    decoration: BoxDecoration(
                      color: const Color(0xffe8edf6),
                      borderRadius: BorderRadius.circular(18),
                    ),
                    child: const Icon(
                      Icons.person_outline,
                      color: VigiaColors.brand,
                      size: 34,
                    ),
                  ),
                  const SizedBox(width: 14),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          patient['name'],
                          style: const TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.w800,
                          ),
                        ),
                        if (patient['birth_date'] != null &&
                            patient['birth_date'] != '')
                          Padding(
                            padding: const EdgeInsets.only(top: 6),
                            child: Text(
                              'Nacimiento: ${patient['birth_date']}',
                              style: const TextStyle(
                                fontSize: 12,
                                color: VigiaColors.muted,
                              ),
                            ),
                          ),
                      ],
                    ),
                  ),
                  const Icon(
                    Icons.chevron_right,
                    color: VigiaColors.muted,
                    size: 20,
                  ),
                ],
              ),
              const SizedBox(height: 16),
              Align(
                alignment: Alignment.centerLeft,
                child: Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 10,
                    vertical: 5,
                  ),
                  decoration: BoxDecoration(
                    color: active
                        ? const Color(0xffe5f1ec)
                        : VigiaColors.lavender,
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Text(
                    // Spec 013: shared patients show how the account accesses them.
                    '${active ? 'Paciente activo' : 'Archivado · Historial disponible'}'
                    '${role == null || role == 'titular' ? '' : ' · ${roleLabel(role)}'}',
                    style: const TextStyle(
                      fontSize: 11,
                      color: Color(0xff466456),
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
              ),
              if (patient['notes'] != null && patient['notes'] != '')
                Padding(
                  padding: const EdgeInsets.only(top: 12),
                  child: Text(
                    patient['notes'],
                    maxLines: 3,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                      fontSize: 12,
                      color: VigiaColors.muted,
                      height: 1.5,
                    ),
                  ),
                ),
              const SizedBox(height: 14),
              const Text(
                'Ficha completa →',
                style: TextStyle(
                  color: VigiaColors.brand,
                  fontWeight: FontWeight.w700,
                  fontSize: 12,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
