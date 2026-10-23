import 'dart:io';
import 'dart:math';

import 'package:camera/camera.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:vigia_pose/vigia_pose.dart';

import '../../core/api.dart';
import 'pose_classifier.dart';

class PhonePoseScreen extends StatefulWidget {
  final VigiaApi api;
  final int patientId;
  const PhonePoseScreen({
    super.key,
    required this.api,
    required this.patientId,
  });
  @override
  State<PhonePoseScreen> createState() => _PhonePoseState();
}

class _PhonePoseState extends State<PhonePoseScreen>
    with WidgetsBindingObserver {
  CameraController? camera;
  bool busy = false;
  int generation = 0;
  String? message;
  final references = <String, List<double>>{};
  Map<String, dynamic>? pending;
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
  }

  Future<void> stop() async {
    generation++;
    final old = camera;
    camera = null;
    references.clear();
    pending = null;
    await old?.dispose();
    try {
      await VigiaPose.release();
    } catch (_) {
      /* No detector may be loaded. */
    }
    if (mounted) setState(() {});
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state != AppLifecycleState.resumed) stop();
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    generation++;
    camera?.dispose();
    VigiaPose.release().catchError((_) {});
    super.dispose();
  }

  Future<void> authorized() async {
    final caps = await widget.api.get('capabilities');
    if (caps['features']?['posture_detection'] != true) {
      throw ApiError('La cámara requiere Premium vigente.', 403);
    }
    // Server also verifies active capacity and ownership before every capture.
    await widget.api.get('patients/${widget.patientId}/phone-observations');
  }

  Future<void> start() async {
    if (busy) return;
    setState(() {
      busy = true;
      message = null;
    });
    final epoch = ++generation;
    CameraController? next;
    try {
      await authorized();
      final cameras = await availableCameras();
      final rear = cameras
          .where((c) => c.lensDirection == CameraLensDirection.back)
          .toList();
      if (rear.isEmpty) {
        throw ApiError('No se encontró una cámara trasera disponible.', 0);
      }
      next = CameraController(
        rear.first,
        ResolutionPreset.high,
        enableAudio: false,
      );
      await next.initialize();
      await next.lockCaptureOrientation(DeviceOrientation.portraitUp);
      if (!mounted || epoch != generation) {
        await next.dispose();
        return;
      }
      camera = next;
    } on CameraException catch (e) {
      await next?.dispose();
      if (mounted) {
        message =
            'No se pudo abrir la cámara (${e.code}). Revisa el permiso de cámara en Ajustes.';
      }
    } catch (e) {
      await next?.dispose();
      if (mounted) message = e.toString();
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  Future<List<double>?> sample() async {
    final shot = await camera!.takePicture();
    try {
      return poseFeatures(await VigiaPose.detect(shot.path));
    } finally {
      final file = File(shot.path);
      if (await file.exists()) await file.delete();
    }
  }

  Future<void> capture({String? reference}) async {
    if (busy || camera == null) return;
    setState(() {
      busy = true;
      message = null;
      pending = null;
    });
    final epoch = generation;
    try {
      await authorized();
      // Three actual captures; no generated/simulated landmarks.
      final frames = <List<double>>[];
      for (var i = 0; i < 3; i++) {
        if (!mounted || epoch != generation) return;
        final frame = await sample();
        if (frame == null) {
          throw ApiError(
            'No se puede determinar: encuadra una sola persona y el cuerpo completo.',
            0,
          );
        }
        frames.add(frame);
      }
      if (!mounted || epoch != generation) return;
      if (reference != null) {
        references[reference] = List.generate(
          24,
          (i) =>
              frames.map((f) => f[i]).reduce((a, b) => a + b) / frames.length,
        );
        message =
            'Referencia capturada: ${label(reference)}. Mantén fija la cámara.';
      } else {
        final results = frames.map((f) => classifyPose(f, references)).toList();
        final same = results.every((r) => r.posture == results.first.posture);
        final posture = same ? results.first.posture : 'indeterminada';
        final score = posture == 'indeterminada'
            ? 0.0
            : results.map((r) => r.score).reduce(min);
        pending = {
          'event_id': newId(),
          'observed_at': DateTime.now().toUtc().toIso8601String(),
          'posture': posture,
          'confidence': score,
          'platform': Platform.isIOS ? 'ios' : 'android',
          'model_version': 'pose-landmarker-lite-float16',
          'rule_version': 'phone-calibrated-snapshot-v1',
        };
        message =
            '${label(posture)} · Similitud ${(score * 100).round()}%. Observación puntual, sin diagnóstico.';
      }
    } catch (e) {
      if (mounted) message = e.toString();
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  Future<void> save() async {
    if (pending == null || busy) return;
    setState(() => busy = true);
    try {
      await widget.api.post(
        'patients/${widget.patientId}/phone-observations',
        pending!,
      );
      pending = null;
      message = 'Observación guardada. No se ha registrado un cuidado manual.';
    } catch (e) {
      message = e.toString();
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  String label(String p) =>
      const {
        'supina': 'Boca arriba',
        'lateral-izquierda': 'Lateral izquierda',
        'lateral-derecha': 'Lateral derecha',
        'indeterminada': 'No se puede determinar',
      }[p] ??
      p;
  String newId() {
    final random = Random.secure();
    final bytes = List.generate(16, (_) => random.nextInt(256));
    bytes[6] = (bytes[6] & 15) | 64;
    bytes[8] = (bytes[8] & 63) | 128;
    final h = bytes.map((b) => b.toRadixString(16).padLeft(2, '0')).join();
    return '${h.substring(0, 8)}-${h.substring(8, 12)}-${h.substring(12, 16)}-${h.substring(16, 20)}-${h.substring(20)}';
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Cámara del teléfono')),
    body: ListView(
      padding: const EdgeInsets.all(20),
      children: [
        const Text(
          'Análisis postural con MediaPipe',
          style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 12),
        const Text(
          'Usa un soporte fijo y encuadra una sola persona, con su consentimiento. Los fotogramas se procesan aquí y se eliminan; solo se guarda el resultado si lo confirmas. No es monitoreo continuo ni mide presión de contacto.',
        ),
        const SizedBox(height: 16),
        if (busy) const LinearProgressIndicator(),
        if (camera?.value.isInitialized == true) ...[
          AspectRatio(
            aspectRatio: camera!.value.aspectRatio,
            child: CameraPreview(camera!),
          ),
          const SizedBox(height: 16),
          const Text(
            'Calibra las tres posiciones con una persona de referencia. No movilices a un paciente solo para calibrar. Si cambias el soporte o el encuadre, reinicia la cámara y la calibración.',
          ),
          for (final posture in poseLabels)
            OutlinedButton(
              onPressed: busy ? null : () => capture(reference: posture),
              child: Text(
                '${references.containsKey(posture) ? '✓ ' : ''}Calibrar ${label(posture)}',
              ),
            ),
          FilledButton(
            onPressed: busy || references.length != 3 ? null : capture,
            child: const Text('Analizar postura'),
          ),
          if (pending != null)
            OutlinedButton(
              onPressed: busy ? null : save,
              child: const Text('Guardar observación'),
            ),
          TextButton(
            onPressed: busy ? null : stop,
            child: const Text('Detener cámara y borrar calibración'),
          ),
        ] else
          FilledButton(
            onPressed: busy ? null : start,
            child: const Text('Abrir cámara'),
          ),
        if (message != null)
          Padding(
            padding: const EdgeInsets.only(top: 16),
            child: Text(message!),
          ),
      ],
    ),
  );
}
