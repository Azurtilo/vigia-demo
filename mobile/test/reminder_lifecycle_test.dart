import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:vigia_mobile/core/api.dart';
import 'package:vigia_mobile/features/patients/patient_screen.dart';

/// Fake server for one patient whose clock follows the same rules as Django:
/// pause/archive drop it from timer-schedule, resume/posture bump generation.
class FakeServer {
  bool active = true, paused = false;
  int generation = 1;
  DateTime due = DateTime.now().add(const Duration(minutes: 60));
  final posts = <String>[];

  Map<String, dynamic> get timer => {
    'interval': 60,
    'paused': paused,
    'next_due_at': paused ? null : due.toIso8601String(),
    'generation': generation,
  };

  List<Map<String, dynamic>> get schedule => active && !paused
      ? [
          {'id': 1, 'generation': generation, 'due': due.toIso8601String()},
        ]
      : [];

  void advance() {
    generation++;
    due = DateTime.now().add(Duration(minutes: 60 + generation));
  }

  MockClient client() => MockClient((r) async {
    final path = r.url.path;
    Object body = {'items': [], 'next_page': null};
    if (r.method == 'DELETE') {
      return http.Response(jsonEncode({'status': 401}), 401);
    }
    if (r.method == 'POST') {
      posts.add(path);
      if (path.endsWith('/timer')) {
        final action = jsonDecode(r.body)['action'];
        paused = action == 'pause';
        advance();
      } else if (path.endsWith('/posture')) {
        paused = false;
        advance();
      } else if (path.endsWith('/archive/active')) {
        active = false;
        paused = true;
        advance();
      }
      body = {'saved': true};
    } else if (path.endsWith('/timer-schedule')) {
      body = {'items': schedule, 'server_time': DateTime.now().toIso8601String()};
    } else if (path.endsWith('/patients/1')) {
      body = {
        'id': 1,
        'name': 'Paciente ficticio',
        'notes': '',
        'contact_name': '',
        'active': active,
        'tokens': {
          'timer': 't',
          'posture': 'p',
          'archive': 'a',
          'reactivate': 'r',
        },
        'timer': timer,
      };
    } else if (path.endsWith('/capabilities')) {
      body = {};
    }
    return http.Response(
      jsonEncode(body),
      200,
      headers: {'content-type': 'application/json; charset=utf-8'},
    );
  });
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  const channel = MethodChannel('dexterous.com/flutter/local_notifications');
  // Pending notifications on the "device": id -> payload.
  final pending = <int, String>{};
  setUp(() {
    AndroidFlutterLocalNotificationsPlugin.registerWith();
    FlutterSecureStorage.setMockInitialValues({});
    pending.clear();
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(channel, (call) async {
          final args = call.arguments;
          switch (call.method) {
            case 'zonedSchedule':
              pending[args['id']] = args['payload'];
              return null;
            case 'cancel':
              pending.remove(args['id']);
              return null;
            case 'cancelAll':
              pending.clear();
              return null;
            case 'pendingNotificationRequests':
              return [
                for (final e in pending.entries)
                  {'id': e.key, 'title': '', 'body': '', 'payload': e.value},
              ];
            case 'initialize':
            case 'areNotificationsEnabled':
            case 'canScheduleExactNotifications':
            case 'requestNotificationsPermission':
              return true;
          }
          return null;
        });
  });

  VigiaApi signedIn(FakeServer server) {
    final api = VigiaApi(client: server.client());
    api.token = 'session';
    api.remindersEnabled = true;
    return api;
  }

  testWidgets('Pausing from the clock cancels and resuming reschedules', (
    tester,
  ) async {
    final server = FakeServer();
    final api = signedIn(server);
    await tester.pumpWidget(
      MaterialApp(home: PatientScreen(api: api, id: 1, initialTab: 4)),
    );
    await tester.pumpAndSettle();
    expect(pending.keys, [1]);
    await tester.tap(find.text('Pausar'));
    await tester.pumpAndSettle();
    expect(server.posts, ['/api/v1/patients/1/timer']);
    expect(pending, isEmpty);
    await tester.tap(find.text('Reanudar'));
    await tester.pumpAndSettle();
    expect(pending.keys, [1]);
    expect(pending[1], startsWith('1:${server.generation}:'));
    await tester.pumpWidget(const SizedBox());
  });

  testWidgets('Archiving the patient cancels its pending reminder', (
    tester,
  ) async {
    final server = FakeServer();
    final api = signedIn(server);
    await tester.pumpWidget(
      MaterialApp(home: PatientScreen(api: api, id: 1)),
    );
    await tester.pumpAndSettle();
    expect(pending.keys, [1]);
    await tester.scrollUntilVisible(
      find.text('Archivar paciente'),
      300,
      scrollable: find.byType(Scrollable).first,
    );
    await tester.tap(find.text('Archivar paciente'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Confirmar'));
    await tester.pumpAndSettle();
    expect(server.posts, ['/api/v1/patients/1/archive/active']);
    expect(pending, isEmpty);
    await tester.pumpWidget(const SizedBox());
  });

  test('A recorded posture replaces the reminder instead of adding one', () async {
    final server = FakeServer();
    final api = signedIn(server);
    await api.syncReminders();
    final before = pending[1];
    await api.post('patients/1/posture', {'token': 'p'});
    await api.syncReminders();
    expect(pending.keys, [1]);
    expect(pending[1], isNot(before));
    expect(pending[1], startsWith('1:${server.generation}:'));
  });

  test('Signing out removes every pending reminder', () async {
    final server = FakeServer();
    final api = signedIn(server);
    await api.syncReminders();
    expect(pending, isNotEmpty);
    await api.logout();
    expect(pending, isEmpty);
    expect(api.token, isNull);
    // A late sync after logout must not bring them back.
    await api.syncReminders();
    expect(pending, isEmpty);
  });
}
