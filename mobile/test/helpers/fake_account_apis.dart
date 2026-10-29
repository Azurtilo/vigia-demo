import 'package:vigia_mobile/core/network/api_exception.dart';
import 'package:vigia_mobile/features/account/subscription.dart';
import 'package:vigia_mobile/features/history/history.dart';
import 'package:vigia_mobile/features/members/members.dart';

/// Historial falso: devuelve páginas de 2 entradas y registra los filtros pedidos.
class FakeHistoryApi implements HistoryApi {
  List<Map<String, dynamic>> entries = [];
  bool hiddenOlder = false;
  final List<String?> categoriesRequested = [];

  @override
  Future<HistoryPage> page(String patientId, {String? category, String? cursor, int limit = 20}) async {
    categoriesRequested.add(category);
    final filtered = entries.where((e) => category == null || e['category'] == category).toList();
    final start = cursor == null ? 0 : int.parse(cursor);
    final slice = filtered.skip(start).take(2).toList();
    final next = start + 2 < filtered.length ? '${start + 2}' : null;
    return HistoryPage.fromJson({
      'items': slice,
      'nextCursor': next,
      'visibleSince': hiddenOlder ? '2026-09-26T00:00:00Z' : null,
      'hiddenOlderEntries': hiddenOlder,
    });
  }

  static Map<String, dynamic> entry(String id, String type, String category, Map<String, dynamic> data, {String actor = 'carla', String name = 'Carla'}) => {
        'id': id, 'type': type, 'category': category, 'occurredAt': '2026-10-26T15:00:00Z',
        'recordedAt': '2026-10-26T15:00:00Z', 'actorUid': actor, 'actorName': name, 'data': data,
      };
}

/// Personas falsas: aplica las mismas reglas básicas que el backend.
class FakeMembersApi implements MembersApi {
  final Map<String, List<Map<String, dynamic>>> memberStore = {};
  final List<Map<String, dynamic>> invitationStore = [];
  final List<Map<String, dynamic>> calls = [];

  @override
  Future<List<Member>> members(String patientId) async => (memberStore[patientId] ?? []).map(Member.fromJson).toList();

  @override
  Future<List<Invitation>> invitations(String patientId) async => invitationStore.map(Invitation.fromJson).toList();

  @override
  Future<CreatedInvitation> invite(String patientId, {required String email, required String relation}) async {
    calls.add({'op': 'invite', 'email': email, 'relation': relation});
    final json = {
      'id': 'inv${invitationStore.length + 1}', 'email': email, 'relation': relation, 'status': 'pending',
      'expiresAt': '2026-11-02T15:00:00Z', 'permissions': ['patient.view'],
    };
    invitationStore.add(json);
    return CreatedInvitation(Invitation.fromJson(json), '59XB-SV6S-B7RC-V4K4-PU6N');
  }

  @override
  Future<void> revoke(String patientId, String invitationId) async {
    calls.add({'op': 'revoke', 'id': invitationId});
    invitationStore.firstWhere((i) => i['id'] == invitationId)['status'] = 'revoked';
  }

  @override
  Future<Member> updatePermissions(String patientId, String uid, Set<String> permissions) async {
    calls.add({'op': 'permissions', 'uid': uid, 'permissions': permissions.toList()..sort()});
    final m = memberStore[patientId]!.firstWhere((m) => m['uid'] == uid)..['permissions'] = permissions.toList();
    return Member.fromJson(m);
  }

  @override
  Future<void> remove(String patientId, String uid) async {
    calls.add({'op': 'remove', 'uid': uid});
    memberStore[patientId]!.removeWhere((m) => m['uid'] == uid);
  }
}

/// Suscripción falsa con los planes por defecto.
class FakeSubscriptionApi implements SubscriptionApi {
  String planId = 'free';
  int activePatients = 1;
  final List<Map<String, dynamic>> changes = [];

  static const _plans = {
    'free': {'name': 'Gratis', 'priceClp': 0, 'maxPatients': 1, 'features': {'extendedCareTracking': false, 'positionChanges': false, 'historyDays': 30}},
    'plus': {'name': 'Plus', 'priceClp': 4990, 'maxPatients': 3, 'features': {'extendedCareTracking': true, 'positionChanges': true, 'historyDays': 365}},
    'premium': {'name': 'Premium', 'priceClp': 9990, 'maxPatients': null, 'features': {'extendedCareTracking': true, 'positionChanges': true, 'historyDays': null, 'cameras': true}},
  };

  Map<String, dynamic> _plan(String id) => {'id': id, 'priceIsTest': true, ..._plans[id]!};

  @override
  Future<List<PlanInfo>> plans() async => _plans.keys.map((id) => PlanInfo.fromJson(_plan(id))).toList();

  @override
  Future<SubscriptionInfo> subscription() async => SubscriptionInfo.fromJson({
        'planId': planId,
        'planName': _plans[planId]!['name'],
        'usage': {'activePatients': activePatients, 'maxPatients': _plans[planId]!['maxPatients']},
        'recentChanges': changes,
      });

  @override
  Future<PlanPreview> preview(String target) async {
    final max = _plans[target]!['maxPatients'] as int?;
    final over = max != null && activePatients > max;
    return PlanPreview.fromJson({
      'target': _plan(target),
      'overLimit': over,
      'requiresConfirmation': over,
      'lostFeatures': target == 'free' ? ['registro de cambios de posición'] : <String>[],
      'message': over ? 'Tienes $activePatients pacientes activos y el plan permite $max. No se borrará nada.' : 'Puedes cambiarte a este plan sin restricciones.',
    });
  }

  @override
  Future<void> change(String target, {bool confirmOverLimit = false}) async {
    final max = _plans[target]!['maxPatients'] as int?;
    if (max != null && activePatients > max && !confirmOverLimit) {
      throw const ApiException(kind: ApiErrorKind.api, statusCode: 409, code: 'downgrade_over_limit', message: 'Falta confirmar.');
    }
    changes.insert(0, {'fromPlan': planId, 'toPlan': target, 'confirm': confirmOverLimit});
    planId = target;
  }
}
