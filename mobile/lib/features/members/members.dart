import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/network/api_client.dart';

/// Permisos por paciente con su descripción para mostrar. El orden es el de docs/roles-permisos.md.
const permissionLabels = {
  'patient.view': 'Ver la ficha',
  'patient.edit': 'Editar la ficha',
  'meds.manage': 'Agregar y modificar medicamentos',
  'meds.administer': 'Registrar tomas de medicamentos',
  'care.manage': 'Agregar y modificar tareas de cuidado',
  'care.record': 'Registrar tareas y cambios de posición',
  'history.view': 'Ver el historial',
  'alerts.handle': 'Atender alertas',
};

String relationLabel(String relation) => switch (relation) {
      'owner' => 'Responsable',
      'family' => 'Familiar',
      _ => 'Cuidador/a',
    };

class Member {
  const Member({required this.uid, required this.displayName, required this.relation, required this.permissions});

  factory Member.fromJson(Map<String, dynamic> json) => Member(
        uid: json['uid'] as String,
        displayName: json['displayName'] as String,
        relation: json['relation'] as String,
        permissions: (json['permissions'] as List).cast<String>().toSet(),
      );

  final String uid;
  final String displayName;
  final String relation;
  final Set<String> permissions;
}

class Invitation {
  const Invitation({
    required this.id,
    required this.email,
    required this.relation,
    required this.status,
    required this.expiresAt,
    required this.permissions,
  });

  factory Invitation.fromJson(Map<String, dynamic> json) => Invitation(
        id: json['id'] as String,
        email: json['email'] as String,
        relation: json['relation'] as String,
        status: json['status'] as String,
        expiresAt: DateTime.parse(json['expiresAt'] as String),
        permissions: (json['permissions'] as List).cast<String>(),
      );

  final String id;
  final String email;
  final String relation;
  final String status; // pending | accepted | revoked | expired
  final DateTime expiresAt;
  final List<String> permissions;

  String get statusLabel => switch (status) {
        'pending' => 'Pendiente',
        'accepted' => 'Aceptada',
        'revoked' => 'Anulada',
        _ => 'Vencida',
      };
}

/// Invitación recién creada: el código se muestra SOLO esta vez (en el servidor queda su huella).
class CreatedInvitation {
  const CreatedInvitation(this.invitation, this.code);
  final Invitation invitation;
  final String code;
}

class MembersApi {
  MembersApi(this._client);
  final ApiClient _client;

  Future<List<Member>> members(String patientId) async => (await _client.get('/patients/$patientId/members') as List)
      .map((m) => Member.fromJson(m as Map<String, dynamic>))
      .toList();

  Future<List<Invitation>> invitations(String patientId) async =>
      (await _client.get('/patients/$patientId/invitations') as List)
          .map((i) => Invitation.fromJson(i as Map<String, dynamic>))
          .toList();

  /// Sin `permissions`: el backend aplica los permisos por defecto de la relación.
  Future<CreatedInvitation> invite(String patientId, {required String email, required String relation}) async {
    final data = await _client.post('/patients/$patientId/invitations', body: {'email': email.trim(), 'relation': relation})
        as Map<String, dynamic>;
    return CreatedInvitation(Invitation.fromJson(data['invitation'] as Map<String, dynamic>), data['code'] as String);
  }

  Future<void> revoke(String patientId, String invitationId) =>
      _client.delete('/patients/$patientId/invitations/$invitationId');

  Future<Member> updatePermissions(String patientId, String uid, Set<String> permissions) async => Member.fromJson(
        await _client.patch('/patients/$patientId/members/$uid', body: {'permissions': permissions.toList()})
            as Map<String, dynamic>,
      );

  /// Quitar a alguien (responsable) o retirarse (uno mismo).
  Future<void> remove(String patientId, String uid) => _client.delete('/patients/$patientId/members/$uid');
}

final membersApiProvider = Provider<MembersApi>((ref) => MembersApi(ref.watch(apiClientProvider)));

final membersProvider = FutureProvider.autoDispose.family<List<Member>, String>(
  (ref, patientId) => ref.watch(membersApiProvider).members(patientId),
);

final invitationsProvider = FutureProvider.autoDispose.family<List<Invitation>, String>(
  (ref, patientId) => ref.watch(membersApiProvider).invitations(patientId),
);
