import 'dart:async';
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:vigia_mobile/core/api.dart';
import 'package:vigia_mobile/notifications/local_reminders.dart';
import 'package:vigia_mobile/features/posture/clock_panel.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  const channel = MethodChannel('dexterous.com/flutter/local_notifications');
  final calls = <MethodCall>[];
  setUp(() {
    AndroidFlutterLocalNotificationsPlugin.registerWith();
    FlutterSecureStorage.setMockInitialValues({});
    calls.clear();
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(channel, (call) async {
          calls.add(call);
          if (call.method == 'pendingNotificationRequests') {
            return [
              {'id': 99, 'title': '', 'body': '', 'payload': 'old-account'},
            ];
          }
          if ([
            'initialize',
            'areNotificationsEnabled',
            'canScheduleExactNotifications',
            'requestNotificationsPermission',
          ].contains(call.method)) {
            return true;
          }
          return null;
        });
  });

  test('Only future instants are queued with timezone offset preserved', () {
    final result = upcomingReminders([
      {'id': 1, 'generation': 2, 'due': '2026-10-22T13:00:00-03:00'},
      {'id': 2, 'generation': 1, 'due': '2026-10-22T14:00:00Z'},
    ], DateTime.utc(2026, 10, 22, 15));
    expect(result.map((x) => x.id), [1]);
    expect(result.single.due.toUtc(), DateTime.utc(2026, 10, 22, 16));
  });
  test(
    'Reconcile cancels obsolete alarm and schedules a generic next reminder',
    () async {
      final reminders = LocalReminders();
      await reminders.reconcile([
        {
          'id': 2,
          'generation': 4,
          'due': DateTime.now()
              .add(const Duration(hours: 1))
              .toUtc()
              .toIso8601String(),
        },
      ]);
      expect(
        calls.where((c) => c.method == 'cancel').single.arguments['id'],
        99,
      );
      final scheduled = calls
          .where((c) => c.method == 'zonedSchedule')
          .single
          .arguments;
      expect(scheduled['id'], 2);
      expect(
        scheduled['body'],
        'Es momento de revisar un cuidado. Abre VIGIA.',
      );
      await reminders.clear();
      expect(calls.last.method, 'cancelAll');
    },
  );
  test('Logout during fetch cannot restore previous account alarms', () async {
    final response = Completer<http.Response>();
    final api = VigiaApi(client: MockClient((_) => response.future));
    api.token = 'old-session';
    api.remindersEnabled = true;
    final sync = api.syncReminders();
    await api.forget();
    response.complete(
      http.Response(
        jsonEncode({
          'items': [
            {
              'id': 2,
              'generation': 1,
              'due': DateTime.now()
                  .add(const Duration(hours: 1))
                  .toIso8601String(),
            },
          ],
        }),
        200,
      ),
    );
    await sync;
    expect(api.token, null);
    expect(calls.where((c) => c.method == 'zonedSchedule'), isEmpty);
  });
  testWidgets('Empty clock offers creation; paused clock offers resume', (
    tester,
  ) async {
    final actions = <String>[];
    final api = VigiaApi();
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: ClockPanel(
            api: api,
            timer: null,
            busy: false,
            onAction: actions.add,
          ),
        ),
      ),
    );
    await tester.tap(find.text('Crear recordatorio'));
    expect(actions, ['start']);
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: ClockPanel(
            api: api,
            timer: {'paused': true, 'interval': 90},
            busy: false,
            onAction: actions.add,
          ),
        ),
      ),
    );
    await tester.tap(find.text('Reanudar'));
    expect(actions, ['start', 'resume']);
    await tester.pumpWidget(const SizedBox());
  });
}
