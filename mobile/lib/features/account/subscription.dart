import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/network/api_client.dart';

/// Plan tal como lo entrega el backend (la colección `plans` es la única fuente de verdad).
class PlanInfo {
  const PlanInfo({
    required this.id,
    required this.name,
    required this.priceClp,
    required this.priceIsTest,
    required this.maxPatients,
    required this.features,
  });

  factory PlanInfo.fromJson(Map<String, dynamic> json) => PlanInfo(
        id: json['id'] as String,
        name: json['name'] as String,
        priceClp: json['priceClp'] as int,
        priceIsTest: json['priceIsTest'] as bool,
        maxPatients: json['maxPatients'] as int?,
        features: (json['features'] as Map).cast<String, dynamic>(),
      );

  final String id;
  final String name;
  final int priceClp;
  final bool priceIsTest;
  final int? maxPatients;
  final Map<String, dynamic> features;

  String get priceLabel => priceClp == 0 ? r'$0' : '\$${_thousands(priceClp)} / mes';
  String get patientsLabel => maxPatients == null ? 'Pacientes sin límite' : 'Hasta $maxPatients paciente${maxPatients == 1 ? '' : 's'}';

  /// Funciones incluidas, en texto (solo las que tiene).
  List<String> get featureLabels => [
        'Medicamentos, agenda y tareas',
        if (features['extendedCareTracking'] == true) 'Seguimiento ampliado de tareas',
        if (features['positionChanges'] == true) 'Registro de cambios de posición',
        features['historyDays'] == null ? 'Historial completo' : 'Historial de ${features['historyDays']} días',
        if (features['pdfReport'] == true) 'Informe PDF (próximamente)',
        if (features['cameras'] == true) 'Cámara y análisis de postura (próximamente)',
      ];

  static String _thousands(int n) => n.toString().replaceAllMapped(RegExp(r'\B(?=(\d{3})+(?!\d))'), (_) => '.');
}

class SubscriptionInfo {
  const SubscriptionInfo({required this.planId, required this.planName, required this.activePatients, required this.maxPatients, required this.changes});

  factory SubscriptionInfo.fromJson(Map<String, dynamic> json) {
    final usage = json['usage'] as Map<String, dynamic>;
    return SubscriptionInfo(
      planId: json['planId'] as String,
      planName: json['planName'] as String,
      activePatients: usage['activePatients'] as int,
      maxPatients: usage['maxPatients'] as int?,
      changes: (json['recentChanges'] as List).cast<Map<String, dynamic>>(),
    );
  }

  final String planId;
  final String planName;
  final int activePatients;
  final int? maxPatients;
  final List<Map<String, dynamic>> changes;
}

class PlanPreview {
  const PlanPreview({required this.target, required this.overLimit, required this.requiresConfirmation, required this.lostFeatures, required this.message});

  factory PlanPreview.fromJson(Map<String, dynamic> json) => PlanPreview(
        target: PlanInfo.fromJson(json['target'] as Map<String, dynamic>),
        overLimit: json['overLimit'] as bool,
        requiresConfirmation: json['requiresConfirmation'] as bool,
        lostFeatures: (json['lostFeatures'] as List).cast<String>(),
        message: json['message'] as String,
      );

  final PlanInfo target;
  final bool overLimit;
  final bool requiresConfirmation;
  final List<String> lostFeatures;
  final String message;
}

class SubscriptionApi {
  SubscriptionApi(this._client);
  final ApiClient _client;

  Future<List<PlanInfo>> plans() async =>
      (await _client.get('/plans') as List).map((p) => PlanInfo.fromJson(p as Map<String, dynamic>)).toList();

  Future<SubscriptionInfo> subscription() async =>
      SubscriptionInfo.fromJson(await _client.get('/me/subscription') as Map<String, dynamic>);

  /// Simula el cambio SIN aplicarlo.
  Future<PlanPreview> preview(String planId) async =>
      PlanPreview.fromJson(await _client.get('/me/subscription/preview', query: {'planId': planId}) as Map<String, dynamic>);

  /// Cambio simulado: no se realiza ningún cobro.
  Future<void> change(String planId, {bool confirmOverLimit = false}) =>
      _client.post('/me/subscription/change', body: {'planId': planId, 'confirmOverLimit': confirmOverLimit});
}

final subscriptionApiProvider = Provider<SubscriptionApi>((ref) => SubscriptionApi(ref.watch(apiClientProvider)));
final plansProvider = FutureProvider.autoDispose<List<PlanInfo>>((ref) => ref.watch(subscriptionApiProvider).plans());
final subscriptionProvider = FutureProvider.autoDispose<SubscriptionInfo>((ref) => ref.watch(subscriptionApiProvider).subscription());
