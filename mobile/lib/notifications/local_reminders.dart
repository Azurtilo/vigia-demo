import 'package:flutter/foundation.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:timezone/timezone.dart' as tz;

/// Absolute instants from Django; no clinical text leaves the app UI.
class ReminderEntry {
  final int id, generation;
  final DateTime due;
  ReminderEntry(this.id, this.generation, this.due);
  String get payload => '$id:$generation:${due.toUtc().toIso8601String()}';
}

List<ReminderEntry> upcomingReminders(List<dynamic> rows, DateTime now) {
  final result = <ReminderEntry>[];
  for (final row in rows) {
    final due = DateTime.tryParse(row['due']?.toString() ?? '');
    if (due != null && due.isAfter(now) && row['id'] is int) {
      result.add(ReminderEntry(row['id'], row['generation'], due));
    }
  }
  result.sort((a, b) => a.due.compareTo(b.due));
  return result;
}

class LocalReminders {
  final FlutterLocalNotificationsPlugin plugin;
  LocalReminders({FlutterLocalNotificationsPlugin? plugin})
    : plugin = plugin ?? FlutterLocalNotificationsPlugin();
  final status = ValueNotifier<String>('Activa los avisos en este teléfono.');
  bool _ready = false;
  Future<void> _queue = Future.value();
  bool get supported =>
      !kIsWeb &&
      (defaultTargetPlatform == TargetPlatform.android ||
          defaultTargetPlatform == TargetPlatform.iOS);

  Future<void> _init() async {
    if (_ready || !supported) return;
    await plugin.initialize(
      settings: const InitializationSettings(
        android: AndroidInitializationSettings('ic_notification'),
        iOS: DarwinInitializationSettings(
          requestAlertPermission: false,
          requestBadgePermission: false,
          requestSoundPermission: false,
        ),
      ),
    );
    _ready = true;
  }

  Future<bool> requestPermission() async {
    if (!supported) {
      status.value =
          'Los avisos locales se activan en la app Android o iPhone.';
      return false;
    }
    await _init();
    final android = plugin
        .resolvePlatformSpecificImplementation<
          AndroidFlutterLocalNotificationsPlugin
        >();
    final ios = plugin
        .resolvePlatformSpecificImplementation<
          IOSFlutterLocalNotificationsPlugin
        >();
    final allowed = android != null
        ? await android.requestNotificationsPermission()
        : await ios?.requestPermissions(alert: true, sound: true, badge: false);
    if (allowed != true) {
      status.value = 'Permiso denegado. Puedes habilitar notificaciones en los ajustes del teléfono.';
      return false;
    }
    if (android != null &&
        await android.canScheduleExactNotifications() != true) {
      await android.requestExactAlarmsPermission();
    }
    return true;
  }

  Future<void> _serial(Future<void> Function() action) {
    final next = _queue.then((_) => action());
    _queue = next.catchError((Object _) {});
    return next;
  }

  Future<void> clear() => _serial(() async {
    if (!supported) return;
    await _init();
    await plugin.cancelAll();
    status.value = 'Avisos locales desactivados en este teléfono.';
  });

  Future<void> reconcile(List<dynamic> rows) => _serial(() async {
    if (!supported) return;
    await _init();
    final android = plugin
        .resolvePlatformSpecificImplementation<
          AndroidFlutterLocalNotificationsPlugin
        >();
    final ios = plugin
        .resolvePlatformSpecificImplementation<
          IOSFlutterLocalNotificationsPlugin
        >();
    final allowed = android != null
        ? await android.areNotificationsEnabled()
        : (await ios?.checkPermissions())?.isEnabled;
    if (allowed != true) {
      await plugin.cancelAll();
      status.value =
          'Notificaciones bloqueadas por el teléfono. Revisa sus ajustes.';
      return;
    }
    final all = upcomingReminders(rows, DateTime.now());
    final wanted = all
        .take(60)
        .toList(); // Leave headroom under the iOS pending limit.
    final exact =
        android == null ||
        await android.canScheduleExactNotifications() == true;
    final pending = await plugin.pendingNotificationRequests();
    for (final old in pending) {
      if (!wanted.any(
        (entry) => entry.id == old.id && entry.payload == old.payload,
      )) {
        await plugin.cancel(id: old.id);
      }
    }
    for (final entry in wanted) {
      // Reschedule when permissions change too; using same ID replaces atomically.
      await plugin.zonedSchedule(
        id: entry.id,
        title: 'VIGIA · Reloj de cuidados',
        body: 'Es momento de revisar un cuidado. Abre VIGIA.',
        scheduledDate: tz.TZDateTime.from(entry.due, tz.UTC),
        notificationDetails: const NotificationDetails(
          android: AndroidNotificationDetails(
            'posture_clock',
            'Reloj de cuidados',
            channelDescription: 'Próximos cambios de postura',
            importance: Importance.high,
            priority: Priority.high,
          ),
          iOS: DarwinNotificationDetails(
            presentAlert: true,
            presentSound: true,
          ),
        ),
        androidScheduleMode: exact
            ? AndroidScheduleMode.exactAllowWhileIdle
            : AndroidScheduleMode.inexactAllowWhileIdle,
        payload: entry.payload,
      );
    }
    status.value = wanted.isEmpty
        ? 'Sin avisos futuros: crea o reanuda un reloj.'
        : '${wanted.length} aviso(s) programado(s) en este teléfono.${exact ? '' : ' Horario aproximado: falta permiso de alarmas exactas.'}${all.length > 60 ? ' Se programan los 60 más próximos; abre la app para actualizar.' : ''}';
  });
}
