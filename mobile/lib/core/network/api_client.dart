import 'package:dio/dio.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../config/app_config.dart';
import 'api_exception.dart';

/// Entrega el ID token de Firebase de la sesión actual (o null si no hay sesión).
/// Firebase lo renueva solo cuando está por vencer.
typedef IdTokenGetter = Future<String?> Function();

final idTokenGetterProvider = Provider<IdTokenGetter>(
  (ref) => () async => FirebaseAuth.instance.currentUser?.getIdToken(),
);

/// Cliente HTTP del backend. Todas las llamadas:
/// - llevan el token de Firebase en `Authorization` (un solo lugar: el interceptor);
/// - fallan con [ApiException], nunca con errores de dio;
/// - tienen tiempos máximos: sin conexión no quedan esperando para siempre.
class ApiClient {
  ApiClient(this._dio);

  factory ApiClient.create({required String baseUrl, required IdTokenGetter tokenGetter, HttpClientAdapter? adapter}) {
    final dio = Dio(
      BaseOptions(
        baseUrl: '$baseUrl/v1',
        connectTimeout: const Duration(seconds: 10),
        receiveTimeout: const Duration(seconds: 20),
        sendTimeout: const Duration(seconds: 20),
        contentType: 'application/json',
        responseType: ResponseType.json,
      ),
    );
    if (adapter != null) dio.httpClientAdapter = adapter;
    dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) async {
          final token = await tokenGetter();
          if (token != null) options.headers['Authorization'] = 'Bearer $token';
          handler.next(options);
        },
      ),
    );
    return ApiClient(dio);
  }

  final Dio _dio;

  Future<dynamic> get(String path, {Map<String, dynamic>? query}) =>
      _send(() => _dio.get<dynamic>(path, queryParameters: query));

  Future<dynamic> post(String path, {Object? body}) => _send(() => _dio.post<dynamic>(path, data: body));

  Future<dynamic> patch(String path, {Object? body}) => _send(() => _dio.patch<dynamic>(path, data: body));

  Future<dynamic> delete(String path) => _send(() => _dio.delete<dynamic>(path));

  Future<dynamic> _send(Future<Response<dynamic>> Function() request) async {
    try {
      return (await request()).data;
    } on DioException catch (e) {
      throw mapDioError(e);
    }
  }
}

/// Traduce cualquier fallo de red o del backend a [ApiException].
ApiException mapDioError(DioException e) {
  switch (e.type) {
    case DioExceptionType.connectionTimeout:
    case DioExceptionType.sendTimeout:
    case DioExceptionType.receiveTimeout:
    case DioExceptionType.transformTimeout:
      return ApiException.timeout;
    case DioExceptionType.connectionError:
      return ApiException.offline;
    case DioExceptionType.badResponse:
      final status = e.response?.statusCode;
      final data = e.response?.data;
      if (data is Map && data['error'] is Map) {
        final error = data['error'] as Map;
        return ApiException(
          kind: ApiErrorKind.api,
          statusCode: status,
          code: error['code'] as String?,
          message: (error['message'] as String?) ?? 'Ocurrió un error. Inténtalo de nuevo.',
        );
      }
      return ApiException(
        kind: ApiErrorKind.unexpected,
        statusCode: status,
        message: 'Ocurrió un problema en VIGIA (código $status). Inténtalo más tarde.',
      );
    case DioExceptionType.cancel:
    case DioExceptionType.badCertificate:
    case DioExceptionType.unknown:
      // "unknown" suele ser sin red (SocketException) cuando no hay más información.
      return e.error != null ? ApiException.offline : const ApiException(
        kind: ApiErrorKind.unexpected,
        message: 'Ocurrió un error inesperado. Inténtalo de nuevo.',
      );
  }
}

final apiClientProvider = Provider<ApiClient>((ref) {
  final config = ref.watch(appConfigProvider);
  return ApiClient.create(baseUrl: config.apiBaseUrl, tokenGetter: ref.watch(idTokenGetterProvider));
});

/// Reintentos automáticos de Riverpod: SOLO para problemas de conexión (hasta 2 veces).
/// Un error de negocio (sin permiso, límite del plan) nunca se reintenta solo.
Duration? retryOnlyConnectivity(int retryCount, Object error) {
  if (error is ApiException && error.isConnectivity && retryCount < 2) {
    return Duration(seconds: 2 * (retryCount + 1));
  }
  return null;
}
