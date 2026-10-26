import 'dart:async';

import '../medications/medicine_filters.dart';
import '../subscription/subscription_panel.dart';
import '../profile/privacy.dart';
import '../profile/profile_panel.dart';

import 'package:flutter/material.dart';

import '../../core/api.dart';
import '../../shared/care_widgets.dart';

import 'dart:math';

import 'package:flutter/foundation.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';

import '../patients/access.dart';
import '../patients/patient_screen.dart';
import '../patients/patient_summary_card.dart';
import '../posture/posture_hub.dart';
import '../../shared/care_agenda_card.dart';
import '../../shared/vigia_design.dart';
import 'home_overview.dart';

class CareHome extends StatefulWidget {
  final VigiaApi api;
  final VoidCallback onLogout;
  const CareHome({super.key, required this.api, required this.onLogout});
  @override
  State<CareHome> createState() => _CareHomeState();
}

class _CareHomeState extends State<CareHome> with WidgetsBindingObserver {
  Timer? refreshTimer;
  int selected = 0;
  String patientQuery = '', medicineFilter = 'all';
  bool busy = false;
  Map<String, dynamic>? me, patients, agenda;
  String? failure;
  bool needsConsent = false;
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    reload();
    refreshTimer = Timer.periodic(const Duration(seconds: 60), (_) {
      if (WidgetsBinding.instance.lifecycleState == AppLifecycleState.resumed) {
        reload();
      }
    });
  }

  @override
  void dispose() {
    refreshTimer?.cancel();
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) reload();
  }

  Future<void> reload() async {
    if (busy) return;
    setState(() {
      busy = true;
      failure = null;
      needsConsent = false;
    });
    try {
      await widget.api.syncReminders();
      final results = await Future.wait([
        widget.api.get('me'),
        widget.api.get('patients'),
        widget.api.get('agenda'),
      ]);
      if (mounted) {
        setState(() {
          me = results[0];
          patients = results[1];
          agenda = results[2];
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          failure = e.toString();
          needsConsent = consentRequired(e);
        });
      }
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  Future<void> newPatient() async {
    // T-011-14: say it before the form; the server still enforces the limit.
    final capacity = patients?['capacity'] as Map<String, dynamic>?;
    final limit = capacity?['limit'];
    if (limit is int && (capacity?['count'] ?? 0) >= limit) {
      notice(
        context,
        'Alcanzaste el límite de pacientes activos. Archiva uno o cambia de plan.',
      );
      return;
    }
    Map<String, dynamic> data = {};
    Map<String, dynamic>? consent;
    // A rejected form comes back filled and keeps the consent already given.
    while (true) {
      if (!mounted) return;
      final edited = await editForm(
        context,
        'Agregar paciente',
        patientFields,
        initial: data,
      );
      if (edited == null || !mounted) return;
      data = edited;
      // Spec 014: the health data needs the patient's or a representative's consent.
      consent ??= await askPatientConsent(context);
      if (consent == null) return;
      try {
        await widget.api.post('patients', {...data, ...consent});
        await reload();
        return;
      } catch (e) {
        if (mounted) notice(context, e);
      }
    }
  }

  Future<void> event(Map<String, dynamic> item, String status) async {
    Map<String, dynamic>? note;
    if (status == 'omitted') {
      note = await editForm(context, 'Motivo de omisión', const [
        FormFieldSpec('note', 'Motivo', required: true, multiline: true),
      ]);
      if (note == null) return;
    }
    if (!mounted) return;
    if (!await confirm(
      context,
      status == 'done' ? '¿Cuidado realizado?' : '¿Registrar omisión?',
      '${item['label']} · ${item['patient']}',
    )) {
      return;
    }
    try {
      await widget.api.post('patients/${item['patient_id']}/events', {
        'token': item['token'],
        'status': status,
        'note': note?['note'] ?? '',
      });
      await reload();
    } catch (e) {
      if (mounted) notice(context, e);
    }
  }

  Future<void> logout() async {
    try {
      final id = await widget.api.storage.read(key: 'vigia_installation');
      if (id != null) {
        await widget.api.post('devices', {
          'installation_id': id,
          'enabled': false,
        });
      }
      await widget.api.logout();
    } catch (e) {
      if (mounted) {
        notice(
          context,
          'Se cerró el acceso en este teléfono. Si no hubo red, la sesión remota vence según el servidor.',
        );
      }
      await widget.api.forget();
    }
    widget.onLogout();
  }

  @override
  Widget build(BuildContext context) {
    final caps = me?['capabilities'] as Map<String, dynamic>?;
    final allItems = (agenda?['items'] as List? ?? [])
        .cast<Map<String, dynamic>>();
    final items = allItems.where(
      (i) =>
          selected != 2 ||
          (i['kind'] == 'medication' &&
              (medicineFilter == 'all' ||
                  (medicineFilter == 'overdue'
                      ? i['overdue'] == true && i['status'] == 'pending'
                      : i['status'] == medicineFilter))),
    );
    final pending = items.where((i) => i['status'] == 'pending').length;
    return Scaffold(
      // T-011-12: the six tabs share the width, so they fit a ~360 dp phone.
      bottomNavigationBar: CareBottomBar(
        selected: selected,
        onSelected: (i) => setState(() => selected = i),
        patients: patients?['capacity']?['count'] ?? 0,
        medicines: allItems
            .where(
              (item) =>
                  item['kind'] == 'medication' && item['status'] == 'pending',
            )
            .length,
      ),
      body: SafeArea(
        bottom: false,
        child: RefreshIndicator(
          onRefresh: reload,
          child: ListView(
            // T-015-14: each tab keeps its own scroll offset, so a tab opens
            // at its top instead of where the previous one was left.
            key: PageStorageKey<String>('care-tab-$selected'),
            padding: const EdgeInsets.fromLTRB(24, 22, 24, 32),
            // T-014-12: nothing else loads until the policy is accepted.
            children: needsConsent
                ? [
                    if (busy) const LinearProgressIndicator(),
                    ConsentRequiredCard(
                      baseUrl: widget.api.baseUrl,
                      onRetry: reload,
                    ),
                    // Profile is hidden here, so logout must stay reachable.
                    TextButton.icon(
                      onPressed: logout,
                      icon: const Icon(Icons.logout),
                      label: const Text('Cerrar sesión'),
                    ),
                  ]
                : [
                    if (busy) const LinearProgressIndicator(),
                    if (failure != null)
                      Card(
                        child: Padding(
                          padding: const EdgeInsets.all(16),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(failure!),
                              TextButton(
                                onPressed: reload,
                                child: const Text('Reintentar'),
                              ),
                            ],
                          ),
                        ),
                      ),
                    if (selected == 0)
                      HomeOverview(
                        me: me,
                        patients: patients,
                        agenda: agenda,
                        busy: busy,
                        onProfile: () => setState(() => selected = 5),
                        onNewPatient: newPatient,
                        onJoin: () async {
                          if (await joinWithCode(context, widget.api)) {
                            await reload();
                          }
                        },
                        onMedicines: () => choosePatient(0),
                        onPostures: () => setState(() => selected = 3),
                        onCamera: () => choosePatient(3),
                        onPatient: (p) => openPatient(p, 0),
                      ),
                    if (selected == 3) PostureHub(choosePatient: choosePatient),
                    if (selected == 5)
                      ProfilePanel(
                        me: me,
                        baseUrl: widget.api.baseUrl,
                        onPlan: () => setState(() => selected = 4),
                        enableNotifications: enableNotifications,
                        logout: logout,
                      ),
                    if (selected == 0 || selected == 2) ...[
                      Text(
                        selected == 2
                            ? 'Medicamentos y horarios'
                            : 'Próximos cuidados',
                        style: Theme.of(context).textTheme.headlineLarge,
                      ),
                      const SizedBox(height: 8),
                      Text(
                        pending == 1
                            ? '1 actividad pendiente'
                            : '$pending actividades pendientes',
                      ),
                      const SizedBox(height: 20),
                      if (selected == 2) ...[
                        FilledButton.icon(
                          onPressed: () => choosePatient(0),
                          icon: const Icon(Icons.add),
                          label: const Text('Gestionar medicamentos'),
                        ),
                        MedicineFilters(
                          value: medicineFilter,
                          onChanged: (value) =>
                              setState(() => medicineFilter = value),
                        ),
                        TextButton(
                          onPressed: () => choosePatient(2),
                          child: const Text('Historial de administración'),
                        ),
                      ],
                      if (patients?['capacity']?['pending'] == true)
                        Card(
                          child: ListTile(
                            leading: const Icon(Icons.info_outline),
                            title: const Text(
                              'Selecciona tus pacientes activos',
                            ),
                            subtitle: const Text(
                              'Tu plan cambió. Conservamos el historial.',
                            ),
                            onTap: () => selectCapacity(),
                          ),
                        ),
                      if (items.isEmpty && !busy)
                        empty(
                          'Tu agenda está tranquila',
                          'Agrega un paciente y sus horarios para organizar el día.',
                          Icons.event_available,
                        ),
                      for (final item in items)
                        CareAgendaCard(
                          item: item,
                          busy: busy,
                          onDone: () => event(item, 'done'),
                          onOmit: () => event(item, 'omitted'),
                        ),
                    ],
                    if (selected == 1) ...[
                      Text(
                        'Mis pacientes',
                        style: Theme.of(context).textTheme.headlineLarge,
                      ),
                      const SizedBox(height: 8),
                      Text(
                        '${patients?['capacity']?['count'] ?? 0} activos · ${caps?['name'] ?? '…'}',
                      ),
                      const SizedBox(height: 20),
                      if ((patients?['patients'] as List? ?? []).isEmpty &&
                          !busy)
                        empty(
                          'Empieza por una persona',
                          'Su ficha, sus horarios y su historial permanecerán juntos.',
                          Icons.person_add_alt,
                        ),
                      FilledButton.icon(
                        onPressed: busy ? null : newPatient,
                        icon: const Icon(Icons.add, size: 18),
                        label: const Text('Agregar paciente'),
                      ),
                      const SizedBox(height: 18),
                      TextField(
                        decoration: const InputDecoration(
                          labelText: 'Buscar paciente',
                          prefixIcon: Icon(Icons.search),
                        ),
                        onChanged: (value) => setState(
                          () => patientQuery = value.trim().toLowerCase(),
                        ),
                      ),
                      const SizedBox(height: 12),
                      for (final p
                          in (patients?['patients'] as List? ?? []).where(
                            (p) => p['name'].toString().toLowerCase().contains(
                              patientQuery,
                            ),
                          ))
                        PatientSummaryCard(
                          patient: Map<String, dynamic>.from(p),
                          onOpen: () =>
                              openPatient(Map<String, dynamic>.from(p), 0),
                        ),
                    ],
                    if (selected == 4 && caps != null)
                      SubscriptionPanel(
                        caps: caps,
                        baseUrl: widget.api.baseUrl,
                        enableNotifications: enableNotifications,
                      ),
                  ],
          ),
        ),
      ),
    );
  }

  Future<void> openPatient(Map<String, dynamic> p, int initialTab) async {
    await Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) =>
            PatientScreen(api: widget.api, id: p['id'], initialTab: initialTab),
      ),
    );
    await reload();
  }

  Future<void> choosePatient(int initialTab) async {
    final rows = (patients?['patients'] as List? ?? [])
        .where((p) => p['active'] == true)
        .toList();
    if (rows.isEmpty) {
      notice(context, 'Agrega un paciente activo para continuar.');
      return;
    }
    if (rows.length == 1) {
      await openPatient(Map<String, dynamic>.from(rows.first), initialTab);
      return;
    }
    final p = await showModalBottomSheet<Map<String, dynamic>>(
      context: context,
      builder: (ctx) => SafeArea(
        child: ListView(
          shrinkWrap: true,
          children: [
            const ListTile(title: Text('Selecciona al paciente')),
            for (final row in rows)
              ListTile(
                title: Text(row['name']),
                trailing: const Icon(Icons.chevron_right),
                onTap: () => Navigator.pop(ctx, Map<String, dynamic>.from(row)),
              ),
          ],
        ),
      ),
    );
    if (p != null && mounted) await openPatient(p, initialTab);
  }

  Widget empty(String title, String body, IconData icon) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 40),
    child: Column(
      children: [
        Icon(icon, size: 48, color: const Color(0xff5057a0)),
        const SizedBox(height: 16),
        Text(
          title,
          style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w600),
        ),
        const SizedBox(height: 8),
        Text(body, textAlign: TextAlign.center),
      ],
    ),
  );
  Future<void> selectCapacity() async {
    final chosen = <int>{};
    final limit = patients!['capacity']['limit'] as int;
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, update) => AlertDialog(
          title: Text('Elige $limit pacientes activos'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                for (final p in patients!['patients'])
                  // Capacity counts only the account's own patients (D-050 a).
                  if (p['active'] == true &&
                      (p['role'] == null || p['role'] == 'titular'))
                    CheckboxListTile(
                      value: chosen.contains(p['id']),
                      title: Text(p['name']),
                      onChanged: (v) => update(() {
                        if (v == true) {
                          chosen.add(p['id']);
                        } else {
                          chosen.remove(p['id']);
                        }
                      }),
                    ),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx, false),
              child: const Text('Volver'),
            ),
            FilledButton(
              onPressed: chosen.length == limit
                  ? () => Navigator.pop(ctx, true)
                  : null,
              child: const Text('Guardar selección'),
            ),
          ],
        ),
      ),
    );
    if (ok != true) return;
    try {
      await widget.api.post('capacity', {
        'patients': chosen.toList(),
        'fingerprint': patients!['fingerprint'],
        'version': patients!['subscription_version'],
      });
      await reload();
    } catch (e) {
      if (mounted) notice(context, e);
    }
  }

  Future<void> enableNotifications() async {
    try {
      if (kIsWeb) {
        throw ApiError(
          'Los avisos se configuran en la aplicación iOS o Android.',
          0,
        );
      }
      const project = String.fromEnvironment('FIREBASE_PROJECT_ID');
      const key = String.fromEnvironment('FIREBASE_API_KEY');
      const app = String.fromEnvironment('FIREBASE_APP_ID');
      const sender = String.fromEnvironment('FIREBASE_SENDER_ID');
      if (project.isEmpty || key.isEmpty || app.isEmpty || sender.isEmpty) {
        throw ApiError(
          'Falta configurar Firebase para este entorno. Los avisos aún no están activos.',
          0,
        );
      }
      if (Firebase.apps.isEmpty) {
        await Firebase.initializeApp(
          options: const FirebaseOptions(
            apiKey: key,
            appId: app,
            messagingSenderId: sender,
            projectId: project,
          ),
        );
      }
      final permission = await FirebaseMessaging.instance.requestPermission();
      if (permission.authorizationStatus != AuthorizationStatus.authorized &&
          permission.authorizationStatus != AuthorizationStatus.provisional) {
        throw ApiError(
          'No se concedió permiso para mostrar notificaciones.',
          0,
        );
      }
      final fcm = await FirebaseMessaging.instance.getToken();
      if (fcm == null) {
        throw ApiError(
          'No se pudo registrar el teléfono. Inténtalo otra vez.',
          0,
        );
      }
      String? id = await widget.api.storage.read(key: 'vigia_installation');
      if (id == null) {
        final r = Random.secure();
        final b = List.generate(16, (_) => r.nextInt(256));
        b[6] = (b[6] & 15) | 64;
        b[8] = (b[8] & 63) | 128;
        final h = b.map((v) => v.toRadixString(16).padLeft(2, '0')).join();
        id =
            '${h.substring(0, 8)}-${h.substring(8, 12)}-${h.substring(12, 16)}-${h.substring(16, 20)}-${h.substring(20)}';
        await widget.api.storage.write(key: 'vigia_installation', value: id);
      }
      final result = await widget.api.post('devices', {
        'installation_id': id,
        'token': fcm,
        'platform': defaultTargetPlatform == TargetPlatform.iOS
            ? 'ios'
            : 'android',
        'enabled': true,
        'local_posture_reminders': true,
      });
      if (mounted) {
        notice(
          context,
          result['delivery_configured'] == true
              ? 'Teléfono registrado. Comprueba un aviso de prueba.'
              : 'Teléfono registrado; falta activar el envío en el servidor.',
        );
      }
    } catch (e) {
      if (mounted) notice(context, e);
    }
  }
}
