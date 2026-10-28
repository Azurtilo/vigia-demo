/// Error de la API ya interpretado. La interfaz solo trabaja con esto, nunca con errores de dio.
enum ApiErrorKind {
  /// Sin conexión o el servidor no responde: se puede reintentar.
  network,

  /// Respuesta del backend con el formato {"error": {"code", "message"}}.
  api,

  /// Respuesta inesperada (p. ej. error 500 sin formato).
  unexpected,
}

class ApiException implements Exception {
  const ApiException({required this.kind, required this.message, this.code, this.statusCode});

  final ApiErrorKind kind;

  /// Código estable del backend (`plan_limit_reached`, `profile_missing`...). Null si no hubo respuesta.
  final String? code;
  final int? statusCode;

  /// Mensaje en español listo para mostrar.
  final String message;

  bool get isConnectivity => kind == ApiErrorKind.network;

  static const offline = ApiException(
    kind: ApiErrorKind.network,
    code: 'offline',
    message: 'No pudimos conectar con VIGIA. Revisa tu conexión a internet e inténtalo de nuevo.',
  );

  static const timeout = ApiException(
    kind: ApiErrorKind.network,
    code: 'timeout',
    message: 'VIGIA está tardando en responder. Inténtalo de nuevo en un momento.',
  );

  @override
  String toString() => 'ApiException($statusCode, $code): $message';
}
