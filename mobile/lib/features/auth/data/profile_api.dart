import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_client.dart';
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
}

final profileApiProvider = Provider<ProfileApi>((ref) => ProfileApi(ref.watch(apiClientProvider)));
