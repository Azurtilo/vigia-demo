import 'dart:async';

import '../medications/medicine_filters.dart';
import '../subscription/subscription_panel.dart';
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
import '../posture/posture_hub.dart';

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
      if (mounted) setState(() => failure = e.toString());
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  Future<void> newPatient() async {
    final data = await editForm(context, 'Agregar paciente', patientFields);
    if (data == null) return;
    try {
      await widget.api.post('patients', data);
      await reload();
    } catch (e) {
      if (mounted) notice(context, e);
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
      appBar: AppBar(
        title: const Text(
          'VIGIA',
          style: TextStyle(fontWeight: FontWeight.w800),
        ),
        actions: [
          IconButton(
            onPressed: busy ? null : reload,
            tooltip: 'Actualizar',
            icon: const Icon(Icons.refresh),
          ),
          IconButton(
            onPressed: logout,
            tooltip: 'Cerrar sesión',
            icon: const Icon(Icons.logout),
          ),
        ],
      ),
      bottomNavigationBar: SafeArea(
        top: false,
        child: SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: SizedBox(
            width: MediaQuery.sizeOf(context).width < 420
                ? 420
                : MediaQuery.sizeOf(context).width,
            child: NavigationBar(
              selectedIndex: selected,
              onDestinationSelected: (i) => setState(() => selected = i),
              destinations: const [
                NavigationDestination(
                  icon: Icon(Icons.home_outlined),
                  label: 'Inicio',
                ),
                NavigationDestination(
                  icon: Icon(Icons.people_outline),
                  label: 'Pacientes',
                ),
                NavigationDestination(
                  icon: Icon(Icons.medication_outlined),
                  label: 'Medicinas',
                ),
                NavigationDestination(
                  icon: Icon(Icons.accessibility_new),
                  label: 'Posturas',
                ),
                NavigationDestination(
                  icon: Icon(Icons.auto_awesome_outlined),
                  label: 'Plan',
                ),
                NavigationDestination(
                  icon: Icon(Icons.person_outline),
                  label: 'Perfil',
                ),
              ],
            ),
          ),
        ),
      ),
      floatingActionButton: selected == 1
          ? FloatingActionButton.extended(
              onPressed: busy ? null : newPatient,
              label: const Text('Agregar paciente'),
              icon: const Icon(Icons.add),
            )
          : null,
      body: RefreshIndicator(
        onRefresh: reload,
        child: ListView(
          padding: const EdgeInsets.fromLTRB(20, 12, 20, 100),
          children: [
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
            if (selected == 0) ...overview(),
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
                selected == 2 ? 'Medicamentos y horarios' : 'Próximos cuidados',
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
                OutlinedButton.icon(
                  onPressed: () => choosePatient(0),
                  icon: const Icon(Icons.add),
                  label: const Text('Gestionar medicamentos'),
                ),
                MedicineFilters(
                  value: medicineFilter,
                  onChanged: (value) => setState(() => medicineFilter = value),
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
                    title: const Text('Selecciona tus pacientes activos'),
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
                Card(
                  margin: const EdgeInsets.only(bottom: 12),
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Icon(
                              item['kind'] == 'medication'
                                  ? Icons.medication_outlined
                                  : Icons.volunteer_activism_outlined,
                              color: const Color(0xff5057a0),
                            ),
                            const SizedBox(width: 10),
                            Expanded(
                              child: Text(
                                item['patient'],
                                style: const TextStyle(
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                            ),
                            Text(when(item['due'])),
                          ],
                        ),
                        const SizedBox(height: 12),
                        Text(
                          item['label'],
                          style: const TextStyle(
                            fontSize: 20,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        if (item['dose'] != '') Text(item['dose']),
                        if (item['status'] == 'pending') ...[
                          if (item['overdue'] == true)
                            const Padding(
                              padding: EdgeInsets.only(top: 6),
                              child: Text(
                                'Horario cumplido · Revisa el cuidado',
                                style: TextStyle(color: Color(0xff854d0e)),
                              ),
                            ),
                          const SizedBox(height: 12),
                          Wrap(
                            spacing: 12,
                            children: [
                              FilledButton(
                                onPressed: busy
                                    ? null
                                    : () => event(item, 'done'),
                                child: const Text('Marcar realizado'),
                              ),
                              TextButton(
                                onPressed: busy
                                    ? null
                                    : () => event(item, 'omitted'),
                                child: const Text('Omitir con motivo'),
                              ),
                            ],
                          ),
                        ] else
                          Padding(
                            padding: const EdgeInsets.only(top: 10),
                            child: Text(
                              item['status'] == 'done'
                                  ? '✓ Realizado'
                                  : 'Omitido con motivo',
                            ),
                          ),
                      ],
                    ),
                  ),
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
              if ((patients?['patients'] as List? ?? []).isEmpty && !busy)
                empty(
                  'Empieza por una persona',
                  'Su ficha, sus horarios y su historial permanecerán juntos.',
                  Icons.person_add_alt,
                ),
              TextField(
                decoration: const InputDecoration(
                  labelText: 'Buscar paciente',
                  prefixIcon: Icon(Icons.search),
                ),
                onChanged: (value) =>
                    setState(() => patientQuery = value.trim().toLowerCase()),
              ),
              const SizedBox(height: 12),
              for (final p in (patients?['patients'] as List? ?? []).where(
                (p) =>
                    p['name'].toString().toLowerCase().contains(patientQuery),
              ))
                Card(
                  child: ListTile(
                    contentPadding: const EdgeInsets.all(16),
                    leading: CircleAvatar(
                      child: Text(p['name'].toString().substring(0, 1)),
                    ),
                    title: Text(
                      p['name'],
                      style: const TextStyle(
                        fontSize: 19,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    subtitle: Text(
                      '${p['active'] == true ? 'Paciente activo' : 'Archivado · Historial disponible'}'
                      '${p['role'] == null || p['role'] == 'titular' ? '' : ' · ${roleLabel(p['role'])}'}',
                    ),
                    trailing: const Icon(Icons.chevron_right),
                    onTap: () async {
                      await Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (_) =>
                              PatientScreen(api: widget.api, id: p['id']),
                        ),
                      );
                      await reload();
                    },
                  ),
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

  List<Widget> overview() => [
    Row(
      children: [
        Expanded(
          child: Text(
            'Hola, ${me?['name'] ?? ''}',
            style: Theme.of(context).textTheme.headlineLarge,
          ),
        ),
        IconButton(
          onPressed: () => setState(() => selected = 5),
          tooltip: 'Mi perfil',
          icon: const Icon(Icons.account_circle_outlined),
        ),
      ],
    ),
    const Text('¿Cómo podemos ayudarte hoy con el cuidado?'),
    Align(
      alignment: Alignment.centerLeft,
      child: Chip(label: Text(me?['capabilities']?['name'] ?? 'Cargando plan')),
    ),
    for (final p
        in (patients?['patients'] as List? ?? [])
            .where((p) => p['active'] == true)
            .take(1))
      Card(
        child: ListTile(
          contentPadding: const EdgeInsets.all(20),
          leading: CircleAvatar(
            child: Text(p['name'].toString().substring(0, 1)),
          ),
          title: Text(
            p['name'],
            style: const TextStyle(fontSize: 21, fontWeight: FontWeight.bold),
          ),
          subtitle: const Text('Ficha, horarios y contacto de emergencia'),
          trailing: const Icon(Icons.chevron_right),
          onTap: () => openPatient(Map<String, dynamic>.from(p), 0),
        ),
      ),
    const SizedBox(height: 18),
    const Text(
      'Acciones rápidas',
      style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700),
    ),
    const SizedBox(height: 10),
    Wrap(
      spacing: 10,
      runSpacing: 10,
      children: [
        quickAction(
          'Medicamentos',
          Icons.medication_outlined,
          () => choosePatient(0),
        ),
        quickAction('Registrar paciente', Icons.person_add_alt, newPatient),
        quickAction('Unirme con un código', Icons.key_outlined, () async {
          if (await joinWithCode(context, widget.api)) await reload();
        }),
        quickAction(
          'Ver posturas',
          Icons.visibility_outlined,
          () => setState(() => selected = 3),
        ),
        quickAction(
          'Analizar postura',
          Icons.auto_awesome_outlined,
          () => choosePatient(3),
        ),
      ],
    ),
    const SizedBox(height: 28),
  ];

  Widget quickAction(String label, IconData icon, VoidCallback action) =>
      SizedBox(
        width: (MediaQuery.sizeOf(context).width - 54) / 2,
        child: OutlinedButton(
          onPressed: busy ? null : action,
          style: OutlinedButton.styleFrom(
            backgroundColor: Colors.white,
            padding: const EdgeInsets.all(18),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(18),
            ),
          ),
          child: Column(
            children: [
              Icon(icon, size: 28),
              const SizedBox(height: 8),
              Text(label, textAlign: TextAlign.center),
            ],
          ),
        ),
      );

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
