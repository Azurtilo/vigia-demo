import 'package:url_launcher/url_launcher.dart';

import '../posture/clock_panel.dart';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../core/api.dart';
import '../../shared/care_widgets.dart';
import '../detection/phone_pose.dart';

class PatientScreen extends StatefulWidget {
  final VigiaApi api;
  final int id, initialTab;
  const PatientScreen({
    super.key,
    required this.api,
    required this.id,
    this.initialTab = 0,
  });
  @override
  State<PatientScreen> createState() => _PatientScreenState();
}

class _PatientScreenState extends State<PatientScreen> {
  Map<String, dynamic>? patient, caps;
  List<dynamic> meds = [],
      tasks = [],
      guides = [],
      history = [],
      nodes = [],
      observations = [];
  bool busy = false;
  String? failure;
  int tab = 0;
  int? nextHistoryPage;
  Future<void> load({bool quiet = false}) async {
    if (busy) return;
    setState(() {
      busy = true;
      failure = null;
    });
    try {
      await widget.api.syncReminders();
      final r = await Future.wait([
        widget.api.get('patients/${widget.id}'),
        widget.api.get('patients/${widget.id}/daily/medications'),
        widget.api.get('patients/${widget.id}/daily/tasks'),
        widget.api.get('guides'),
        widget.api.get('patients/${widget.id}/history'),
        widget.api.get('patients/${widget.id}/nodes'),
        widget.api.get('patients/${widget.id}/observations'),
        widget.api.get('capabilities'),
      ]);
      if (mounted) {
        setState(() {
          patient = r[0];
          meds = r[1]['items'];
          tasks = r[2]['items'];
          guides = r[3]['items'];
          history = r[4]['items'];
          nextHistoryPage = r[4]['next_page'];
          nodes = r[5]['items'];
          observations = r[6]['items'];
          caps = r[7];
        });
      }
    } catch (e) {
      if (mounted) setState(() => failure = e.toString());
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  @override
  void initState() {
    super.initState();
    tab = widget.initialTab;
    load();
  }

  Future<void> mutate(String path, Map<String, dynamic> data) async {
    if (busy) return;
    setState(() => busy = true);
    try {
      await widget.api.post(path, data);
      if (mounted) notice(context, 'Cambio guardado.');
    } catch (e) {
      if (mounted) notice(context, e);
    } finally {
      if (mounted) {
        setState(() => busy = false);
        await load();
      }
    }
  }

  Future<void> editPatient() async {
    final d = await editForm(
      context,
      'Editar ficha',
      patientFields,
      initial: patient!,
    );
    if (d != null) await mutate('patients/${widget.id}', d);
  }

  Future<void> editDaily(bool task, [Map<String, dynamic>? current]) async {
    final fields = <FormFieldSpec>[
      const FormFieldSpec('name', 'Nombre', required: true),
      if (!task) const FormFieldSpec('dose', 'Dosis indicada', required: true),
      FormFieldSpec(
        task ? 'time' : 'hours',
        task ? 'Horario opcional (HH:MM)' : 'Horarios (08:00, 14:00)',
        required: !task,
      ),
      const FormFieldSpec('notes', 'Indicaciones', multiline: true),
      const FormFieldSpec('start_date', 'Desde (AAAA-MM-DD)'),
      const FormFieldSpec('end_date', 'Hasta (AAAA-MM-DD)'),
    ];
    final d = await editForm(
      context,
      task ? 'Programar cuidado' : 'Medicamento y horarios',
      fields,
      initial: current ?? {},
      active: current?['active'] ?? true,
    );
    if (d != null) {
      await mutate(
        'patients/${widget.id}/daily/${task ? 'tasks' : 'medications'}${current == null ? '' : '/${current['id']}'}',
        d,
      );
    }
  }

  Future<void> recordPosture(Map<String, dynamic> guide) async {
    int interval = patient?['timer']?['interval'] ?? 120;
    final agreed = await showDialog<bool>(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, update) => AlertDialog(
          title: const Text('Registrar cambio realizado'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(guide['title']),
              const SizedBox(height: 20),
              DropdownButtonFormField<int>(
                initialValue: interval,
                decoration: const InputDecoration(
                  labelText: 'Próximo recordatorio',
                ),
                items: [60, 90, 120]
                    .map(
                      (v) =>
                          DropdownMenuItem(value: v, child: Text('$v minutos')),
                    )
                    .toList(),
                onChanged: (v) => update(() => interval = v!),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx, false),
              child: const Text('Volver'),
            ),
            FilledButton(
              onPressed: () => Navigator.pop(ctx, true),
              child: const Text('Ya realicé el cambio'),
            ),
          ],
        ),
      ),
    );
    if (agreed == true) {
      await mutate('patients/${widget.id}/posture', {
        'token': patient!['tokens']['posture'],
        'guide': guide['id'],
        'interval': interval,
        'note': '',
      });
    }
  }

  Future<void> timer(String action) async {
    int interval = patient?['timer']?['interval'] ?? 120;
    if (action == 'interval' || action == 'start') {
      final chosen = await showDialog<int>(
        context: context,
        builder: (ctx) => SimpleDialog(
          title: const Text('Intervalo de recordatorios'),
          children: [
            for (final v in [60, 90, 120])
              SimpleDialogOption(
                onPressed: () => Navigator.pop(ctx, v),
                child: Padding(
                  padding: const EdgeInsets.all(8),
                  child: Text('$v minutos'),
                ),
              ),
          ],
        ),
      );
      if (chosen == null) return;
      interval = chosen;
    }
    await mutate('patients/${widget.id}/timer', {
      'token': patient!['tokens']['timer'],
      'action': action,
      'interval': interval,
    });
  }

  Future<void> archive() async {
    final active = patient!['active'] == true;
    if (!await confirm(
      context,
      active ? '¿Archivar paciente?' : '¿Reactivar paciente?',
      active
          ? 'Su historial se conserva. Los recordatorios se pausarán.'
          : 'Se comprobará el cupo de tu plan.',
    )) {
      return;
    }
    final kind = active ? 'archive' : 'reactivate';
    await mutate('patients/${widget.id}/$kind/active', {
      'token': patient!['tokens'][kind],
    });
  }

  Future<void> addNode() async {
    final d = await editForm(context, 'Vincular cámara local', const [
      FormFieldSpec('name', 'Nombre del nodo', required: true),
    ]);
    if (d == null) return;
    try {
      final result = await widget.api.post('patients/${widget.id}/nodes', d);
      if (!mounted) return;
      await showDialog<void>(
        context: context,
        builder: (ctx) => AlertDialog(
          title: const Text('Credencial del nodo'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Configúrala en tu nodo local. Solo se muestra una vez; no la compartas.',
              ),
              const SizedBox(height: 16),
              SelectableText(result['credential']),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () =>
                  Clipboard.setData(ClipboardData(text: result['credential'])),
              child: const Text('Copiar'),
            ),
            FilledButton(
              onPressed: () => Navigator.pop(ctx),
              child: const Text('Listo'),
            ),
          ],
        ),
      );
      await load();
    } catch (e) {
      if (mounted) notice(context, e);
    }
  }

  Future<void> moreHistory() async {
    try {
      final r = await widget.api.get(
        'patients/${widget.id}/history?page=$nextHistoryPage',
      );
      if (mounted) {
        setState(() {
          history.addAll(r['items']);
          nextHistoryPage = r['next_page'];
        });
      }
    } catch (e) {
      if (mounted) notice(context, e);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(
      title: Text(patient?['name'] ?? 'Paciente'),
      actions: [
        IconButton(
          onPressed: busy ? null : load,
          tooltip: 'Actualizar ficha',
          icon: const Icon(Icons.refresh),
        ),
      ],
    ),
    body: ListView(
      padding: const EdgeInsets.all(20),
      children: [
        if (busy) const LinearProgressIndicator(),
        if (failure != null)
          Padding(padding: const EdgeInsets.all(16), child: Text(failure!)),
        if (patient != null) ...[
          Text(
            patient!['active'] ? 'Cuidado activo' : 'Paciente archivado',
            style: const TextStyle(
              color: Color(0xff5057a0),
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 16),
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: SegmentedButton<int>(
              segments: const [
                ButtonSegment(value: 0, label: Text('Cuidados')),
                ButtonSegment(value: 1, label: Text('Guías')),
                ButtonSegment(value: 4, label: Text('Reloj')),
                ButtonSegment(value: 2, label: Text('Historial')),
                ButtonSegment(value: 3, label: Text('Monitoreo')),
              ],
              selected: {tab},
              onSelectionChanged: (s) => setState(() => tab = s.first),
            ),
          ),
          const SizedBox(height: 24),
          if (tab == 0) ...[
            Row(
              children: [
                const Expanded(
                  child: Text(
                    'Ficha personal',
                    style: TextStyle(fontSize: 22, fontWeight: FontWeight.w700),
                  ),
                ),
                IconButton(
                  onPressed: busy ? null : editPatient,
                  tooltip: 'Editar ficha',
                  icon: const Icon(Icons.edit_outlined),
                ),
              ],
            ),
            if (patient!['notes'] != '') Text(patient!['notes']),
            if (patient!['contact_name'] != '')
              ListTile(
                contentPadding: EdgeInsets.zero,
                leading: const Icon(Icons.contact_phone_outlined),
                title: Text(patient!['contact_name']),
                subtitle: Text(
                  '${patient!['contact_relation']} · ${patient!['contact_phone']}',
                ),
              ),
            const SizedBox(height: 24),
            heading('Medicamentos', () => editDaily(false)),
            if (meds.isEmpty)
              const Text(
                'Agrega el medicamento y los horarios indicados para este paciente.',
              ),
            for (final m in meds)
              Card(
                child: ListTile(
                  leading: const Icon(Icons.medication_outlined),
                  title: Text(m['name']),
                  subtitle: Text(
                    '${m['dose']} · ${m['hours']}${m['active'] ? '' : ' · Inactivo'}',
                  ),
                  trailing: const Icon(Icons.edit_outlined),
                  onTap: busy
                      ? null
                      : () => editDaily(false, Map<String, dynamic>.from(m)),
                ),
              ),
            const SizedBox(height: 24),
            heading('Otros cuidados', () => editDaily(true)),
            if (tasks.isEmpty)
              const Text(
                'Organiza higiene, alimentación y otros cuidados del día.',
              ),
            for (final t in tasks)
              Card(
                child: ListTile(
                  leading: const Icon(Icons.volunteer_activism_outlined),
                  title: Text(t['name']),
                  subtitle: Text(
                    '${t['time'] == '' ? 'Sin horario' : t['time']}${t['active'] ? '' : ' · Inactivo'}',
                  ),
                  onTap: busy
                      ? null
                      : () => editDaily(true, Map<String, dynamic>.from(t)),
                ),
              ),
            const SizedBox(height: 24),
            TextButton.icon(
              onPressed: busy ? null : archive,
              icon: Icon(
                patient!['active']
                    ? Icons.archive_outlined
                    : Icons.unarchive_outlined,
              ),
              label: Text(
                patient!['active'] ? 'Archivar paciente' : 'Reactivar paciente',
              ),
            ),
          ],
          if (tab == 1 || tab == 4) ...[
            Text(
              tab == 4 ? 'Reloj de cuidados' : 'Guías de postura',
              style: const TextStyle(fontSize: 25, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 12),
            if (tab == 4)
              ClockPanel(
                api: widget.api,
                timer: patient!['timer'],
                busy: busy,
                onAction: timer,
              ),
            for (final g in (tab == 1 ? guides : []))
              Card(
                margin: const EdgeInsets.only(bottom: 20),
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      ClipRRect(
                        borderRadius: BorderRadius.circular(16),
                        child: Image.asset(
                          'assets/guides/${g['code']}-v2.png',
                          height: 200,
                          width: double.infinity,
                          fit: BoxFit.contain,
                          semanticLabel: g['image_alt'],
                          errorBuilder: (_, error, stack) => const SizedBox(
                            height: 60,
                            child: Center(
                              child: Icon(Icons.accessibility_new, size: 48),
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(height: 12),
                      Text(
                        g['title'],
                        style: const TextStyle(
                          fontSize: 23,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                      for (final step in g['instructions'])
                        Padding(
                          padding: const EdgeInsets.only(top: 10),
                          child: Text(step.toString()),
                        ),
                      const SizedBox(height: 12),
                      Text(
                        g['precautions'],
                        style: const TextStyle(color: Color(0xff854d0e)),
                      ),
                      TextButton(
                        onPressed: () => launchUrl(
                          Uri.parse(g['source_url']),
                          mode: LaunchMode.externalApplication,
                        ),
                        child: Text(g['source_title']),
                      ),
                      if (g['category'] == 'posture')
                        FilledButton(
                          onPressed: busy || !patient!['active']
                              ? null
                              : () =>
                                    recordPosture(Map<String, dynamic>.from(g)),
                          child: const Text('Registrar cambio realizado'),
                        ),
                    ],
                  ),
                ),
              ),
          ],
          if (tab == 2) ...[
            const Text(
              'Cada cuidado cuenta',
              style: TextStyle(fontSize: 25, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 12),
            if (history.isEmpty)
              const Text(
                'Aquí aparecerán los cuidados registrados y sus correcciones.',
              ),
            for (final h in history)
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        h['label'],
                        style: const TextStyle(
                          fontSize: 19,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      Text('${when(h['occurred_at'])} · ${h['author']}'),
                      Text(
                        {
                              'done': 'Realizado',
                              'omitted': 'Omitido',
                              'corrected': 'Corrección',
                            }[h['status']] ??
                            h['status'],
                      ),
                      if (h['note'] != '') Text(h['note']),
                      TextButton(
                        onPressed: busy
                            ? null
                            : () async {
                                final d = await editForm(
                                  context,
                                  'Añadir corrección',
                                  const [
                                    FormFieldSpec(
                                      'note',
                                      'Describe la corrección',
                                      required: true,
                                      multiline: true,
                                    ),
                                  ],
                                );
                                if (d != null) {
                                  await mutate(
                                    'patients/${widget.id}/history/${h['id']}/correction',
                                    {...d, 'token': h['token']},
                                  );
                                }
                              },
                        child: const Text('Añadir corrección'),
                      ),
                    ],
                  ),
                ),
              ),
            if (nextHistoryPage != null)
              OutlinedButton(
                onPressed: moreHistory,
                child: const Text('Ver más registros'),
              ),
          ],
          if (tab == 3) ...[
            const Text(
              'Posición y monitoreo',
              style: TextStyle(fontSize: 25, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 12),
            Text(
              caps?['features']?['posture_detection'] == true
                  ? 'Analiza con este teléfono o vincula una cámara fija. Las observaciones automáticas no confirman cuidados realizados.'
                  : 'La detección de posición está incluida en Premium. Tu historial se conserva.',
            ),
            const SizedBox(height: 16),
            if (caps?['features']?['posture_detection'] == true)
              FilledButton.icon(
                icon: const Icon(Icons.camera_alt_outlined),
                label: const Text('Usar cámara del teléfono'),
                onPressed: busy
                    ? null
                    : () async {
                        await Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (_) => PhonePoseScreen(
                              api: widget.api,
                              patientId: widget.id,
                            ),
                          ),
                        );
                        await load();
                      },
              ),
            const SizedBox(height: 20),
            const Text(
              'Cámara fija',
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
            ),
            for (final n in nodes)
              Card(
                child: ListTile(
                  leading: Icon(
                    n['connected'] == true &&
                            caps?['features']?['posture_detection'] == true
                        ? Icons.sensors
                        : Icons.sensors_off,
                  ),
                  title: Text(n['name']),
                  subtitle: Text(
                    n['active'] != true
                        ? 'Revocado'
                        : caps?['features']?['posture_detection'] != true
                        ? 'No activo por plan'
                        : n['connected'] == true
                        ? 'Conectado · Última señal ${when(n['last_seen_at'])}'
                        : 'Sin señal reciente · No hay monitoreo confirmado',
                  ),
                  trailing: n['active'] == true
                      ? IconButton(
                          tooltip: 'Revocar nodo',
                          icon: const Icon(Icons.link_off),
                          onPressed: busy
                              ? null
                              : () async {
                                  if (await confirm(
                                    context,
                                    '¿Revocar nodo?',
                                    'Dejará de enviar observaciones para este paciente.',
                                  )) {
                                    await mutate('nodes/${n['id']}/revoke', {});
                                  }
                                },
                        )
                      : null,
                ),
              ),
            if (caps?['features']?['posture_detection'] == true)
              OutlinedButton.icon(
                onPressed: busy || !patient!['active'] ? null : addNode,
                icon: const Icon(Icons.add_link),
                label: const Text('Vincular nodo local'),
              ),
            const SizedBox(height: 20),
            const Text(
              'Observaciones automáticas',
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.w600),
            ),
            if (observations.isEmpty)
              const Padding(
                padding: EdgeInsets.only(top: 12),
                child: Text(
                  'Aún no hay observaciones. Analiza y guarda una postura con el teléfono, o vincula y calibra una cámara fija.',
                ),
              ),
            for (final o in observations)
              Card(
                child: ListTile(
                  leading: const Icon(Icons.accessibility_new),
                  title: Text(postureName(o['posture'])),
                  subtitle: Text(
                    '${when(o['observed_at'])} · ${o['source']}\n${o['risk'] == 'immobility' ? 'Aviso de inmovilidad · Revisa al paciente' : 'Estimación automática'}',
                  ),
                ),
              ),
          ],
        ],
      ],
    ),
  );
  Widget heading(String title, VoidCallback action) => Row(
    children: [
      Expanded(
        child: Text(
          title,
          style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w700),
        ),
      ),
      IconButton(
        onPressed: busy || patient?['active'] != true ? null : action,
        tooltip: 'Agregar $title',
        icon: const Icon(Icons.add_circle_outline),
      ),
    ],
  );
}
