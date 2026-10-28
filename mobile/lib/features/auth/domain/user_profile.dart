/// Perfil VIGIA de la persona (GET /v1/me).
class UserProfile {
  const UserProfile({
    required this.uid,
    required this.displayName,
    required this.role,
    required this.status,
    this.email,
  });

  factory UserProfile.fromJson(Map<String, dynamic> json) => UserProfile(
        uid: json['uid'] as String,
        email: json['email'] as String?,
        displayName: json['displayName'] as String,
        role: json['role'] as String,
        status: json['status'] as String,
      );

  final String uid;
  final String? email;
  final String displayName;
  final String role; // client | admin
  final String status; // active | suspended

  bool get isAdmin => role == 'admin';
}
