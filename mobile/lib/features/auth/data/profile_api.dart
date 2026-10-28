import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_client.dart';
import '../../privacy/privacy.dart';
import '../domain/user_profile.dart';

/// Perfil VIGIA en el backend.
class ProfileApi {
  ProfileApi(this._client);
  final ApiClient _client;

  Future<UserProfile> me() async => UserProfile.fromJson(await _client.get('/me') as Map<String, dynamic>);

  /// El backend siempre asigna el rol `client`: el rol no se envía.
  Future<UserProfile> register(String displayName) async => UserProfile.fromJson(
        await _client.post('/auth/register', body: {'displayName': displayName.trim()}) as Map<String, dynamic>,
      );

  /// Estado de la política vigente para esta cuenta (D-101).
  Future<PolicyStatus> policy() async => PolicyStatus.fromJson(await _client.get('/privacy') as Map<String, dynamic>);

  Future<PolicyStatus> acceptPolicy() async =>
      PolicyStatus.fromJson(await _client.post('/privacy/accept') as Map<String, dynamic>);

  /// Mis datos en JSON: cuenta, consentimientos y lo que registré en pacientes ajenos (RF-019-25).
  Future<Map<String, dynamic>> exportAccount() async => await _client.get('/me/export') as Map<String, dynamic>;

  /// Elimina la cuenta (RF-019-27). El backend exige un inicio de sesión de hace 5 minutos o menos.
  Future<void> deleteAccount() => _client.delete('/me');
}

final profileApiProvider = Provider<ProfileApi>((ref) => ProfileApi(ref.watch(apiClientProvider)));
