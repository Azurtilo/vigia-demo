import 'dart:async';
import 'dart:convert';

import '../notifications/local_reminders.dart';

import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;

class ApiError implements Exception {
  final String message;
  final int status;
  final Map<String, dynamic> response;
  ApiError(this.message, this.status, [this.response = const {}]);
  @override
  String toString() => message;
}

class VigiaApi {
  String baseUrl;
  final http.Client client;
  final FlutterSecureStorage storage;
  String? token;
  final reminders = LocalReminders();
  int _reminderEpoch = 0;
  bool remindersEnabled = false;
  VigiaApi({
    String? baseUrl,
    http.Client? client,
    FlutterSecureStorage? storage,
  }) : baseUrl =
           (baseUrl ??
                   const String.fromEnvironment(
                     'API_URL',
                     defaultValue: 'http://127.0.0.1:8000',
                   ))
               .replaceAll(RegExp(r'/$'), ''),
       client = client ?? http.Client(),
       storage = storage ?? const FlutterSecureStorage();
  Future<void> restore() async {
    if (kDebugMode) {
      final saved = await storage.read(key: 'vigia_server');
      if (saved != null) baseUrl = saved;
    }
    token = await storage.read(key: 'vigia_session');
    remindersEnabled =
        await storage.read(key: 'vigia_local_reminders') == 'true';
    if (token == null && reminders.supported) await reminders.clear();
  }

  Future<void> setServer(String url) async {
    final uri = Uri.tryParse(url.trim());
    if (!kDebugMode ||
        uri == null ||
        !['http', 'https'].contains(uri.scheme) ||
        uri.host.isEmpty ||
        uri.userInfo.isNotEmpty ||
        uri.hasQuery ||
        uri.hasFragment ||
        (uri.path.isNotEmpty && uri.path != '/')) {
      throw ApiError(
        'Usa una dirección de servidor http(s) sin ruta ni credenciales.',
        0,
      );
    }
    await forget();
    baseUrl = url.trim().replaceAll(RegExp(r'/$'), '');
    await storage.write(key: 'vigia_server', value: baseUrl);
  }

  Future<void> forget() async {
    ++_reminderEpoch;
    token = null;
    remindersEnabled = false;
    await storage.delete(key: 'vigia_local_reminders');
    await storage.delete(key: 'vigia_session');
    await storage.delete(key: 'vigia_installation');
    if (reminders.supported) await reminders.clear();
  }

  Future<void> enableLocalReminders() async {
    if (!await reminders.requestPermission()) return;
    final id = await storage.read(key: 'vigia_installation');
    if (id != null) {
      await post('devices/reminder-mode', {
        'installation_id': id,
        'local_posture_reminders': true,
      });
    }
    remindersEnabled = true;
    await storage.write(key: 'vigia_local_reminders', value: 'true');
    await syncReminders();
  }

  Future<void> disableLocalReminders() async {
    ++_reminderEpoch;
    remindersEnabled = false;
    await storage.delete(key: 'vigia_local_reminders');
    await reminders.clear();
    // Keep posture push suppressed on this installation: disabling means no clock alerts.
  }

  Future<void> syncReminders() async {
    if (!remindersEnabled || !reminders.supported || token == null) return;
    final epoch = ++_reminderEpoch;
    final session = token;
    try {
      final result = await get('timer-schedule');
      if (epoch != _reminderEpoch || token != session || !remindersEnabled) {
        return;
      }
      await reminders.reconcile(result['items'] as List);
    } catch (e) {
      if (e is ApiError && (e.status == 401 || e.status == 403)) {
        await disableLocalReminders();
      }
      reminders.status.value = 'No se pudo actualizar los avisos. Revisa la conexión y vuelve a intentarlo.';
    }
  }

  Future<Map<String, dynamic>> request(
    String path, {
    Map<String, dynamic>? data,
    String? method,
  }) async {
    final uri = Uri.parse('$baseUrl$path');
    if (!kDebugMode && uri.scheme != 'https') {
      throw ApiError('La conexión de esta versión requiere HTTPS.', 0);
    }
    final req = http.Request(method ?? (data == null ? 'GET' : 'POST'), uri);
    req.headers['Content-Type'] = 'application/json';
    if (token != null) req.headers['X-Session-Token'] = token!;
    if (data != null) req.body = jsonEncode(data);
    try {
      final response = await http.Response.fromStream(
        await client.send(req).timeout(const Duration(seconds: 20)),
      );
      final decoded = jsonDecode(response.body);
      if (decoded is! Map<String, dynamic>) throw const FormatException();
      final next = decoded['meta']?['session_token'];
      if (next is String) {
        token = next;
        await storage.write(key: 'vigia_session', value: token);
      }
      if (response.statusCode >= 400) {
        final errors = decoded['errors'] as List?;
        final message =
            decoded['error'] ?? (errors?.map((e) => e['message']).join('\n'));
        throw ApiError(
          message?.toString() ??
              (response.statusCode == 401
                  ? 'Completa el acceso a tu cuenta.'
                  : 'No se pudo completar la operación.'),
          response.statusCode,
          decoded,
        );
      }
      return decoded;
    } on ApiError {
      rethrow;
    } on TimeoutException {
      throw ApiError(
        'La conexión tardó demasiado. Revisa el estado antes de repetir una acción.',
        0,
      );
    } on FormatException {
      throw ApiError('El servidor no devolvió una respuesta válida.', 0);
    } catch (_) {
      throw ApiError(
        'Sin conexión. No se confirmó ningún cambio. Revisa la agenda al reconectar.',
        0,
      );
    }
  }

  Future<Map<String, dynamic>> get(String path) => request('/api/v1/$path');
  Future<Map<String, dynamic>> post(String path, Map<String, dynamic> data) =>
      request('/api/v1/$path', data: data);
  Future<Map<String, dynamic>> auth(String path, Map<String, dynamic> data) =>
      request('/_allauth/app/v1/$path', data: data);
  Future<void> logout() async {
    try {
      await request('/_allauth/app/v1/auth/session', method: 'DELETE');
    } on ApiError catch (e) {
      if (e.status != 401 && e.status != 410) rethrow;
    } finally {
      await forget();
    }
  }
}
