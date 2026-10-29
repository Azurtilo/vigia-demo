import 'dart:convert';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:vigia_mobile/core/network/api_client.dart';
import 'package:vigia_mobile/core/network/api_exception.dart';

/// Reemplaza la red: responde lo que la prueba indica y guarda la última solicitud.
class FakeAdapter implements HttpClientAdapter {
  FakeAdapter(this.respond);
  final ResponseBody Function(RequestOptions options) respond;
  RequestOptions? last;

  @override
  Future<ResponseBody> fetch(RequestOptions options, Stream<Uint8List>? requestStream, Future<void>? cancelFuture) async {
    last = options;
    return respond(options);
  }

  @override
  void close({bool force = false}) {}
}

ResponseBody jsonBody(Object body, int status) => ResponseBody.fromString(
      jsonEncode(body),
      status,
      headers: {Headers.contentTypeHeader: ['application/json; charset=utf-8']},
    );

void main() {
  ApiClient client(FakeAdapter adapter, {String? token = 'token-123'}) =>
      ApiClient.create(baseUrl: 'http://api', tokenGetter: () async => token, adapter: adapter);

  test('agrega el token de Firebase y el prefijo /v1', () async {
    final adapter = FakeAdapter((_) => jsonBody({'ok': true}, 200));

    final data = await client(adapter).get('/me');

    expect(data, {'ok': true});
    expect(adapter.last!.uri.toString(), 'http://api/v1/me');
    expect(adapter.last!.headers['Authorization'], 'Bearer token-123');
  });

  test('sin sesión no envía encabezado de autorización', () async {
    final adapter = FakeAdapter((_) => jsonBody({}, 200));

    await client(adapter, token: null).get('/plans');

    expect(adapter.last!.headers.containsKey('Authorization'), isFalse);
  });

  test('traduce el formato de error del backend', () async {
    final adapter = FakeAdapter(
      (_) => jsonBody({'error': {'code': 'plan_limit_reached', 'message': 'Tu plan Gratis permite hasta 1 paciente(s).'}}, 403),
    );

    final error = await client(adapter).post('/patients', body: {}).then<Object?>((_) => null, onError: (e) => e);

    expect(error, isA<ApiException>());
    final e = error as ApiException;
    expect(e.kind, ApiErrorKind.api);
    expect(e.statusCode, 403);
    expect(e.code, 'plan_limit_reached');
    expect(e.message, contains('Gratis'));
  });

  test('un 500 sin formato es "inesperado", con mensaje para la persona', () async {
    final adapter = FakeAdapter((_) => ResponseBody.fromString('Internal Server Error', 500));

    final e = await client(adapter).get('/me').then<Object?>((_) => null, onError: (e) => e) as ApiException;

    expect(e.kind, ApiErrorKind.unexpected);
    expect(e.message, contains('500'));
  });

  test('sin conexión se informa como problema de red (reintentable)', () async {
    final adapter = FakeAdapter(
      (options) => throw DioException(requestOptions: options, type: DioExceptionType.connectionError),
    );

    final e = await client(adapter).get('/me').then<Object?>((_) => null, onError: (e) => e) as ApiException;

    expect(e.isConnectivity, isTrue);
    expect(e.message, contains('conexión'));
  });

  test('solo los problemas de conexión se reintentan automáticamente', () {
    expect(retryOnlyConnectivity(0, ApiException.offline), isNotNull);
    expect(retryOnlyConnectivity(2, ApiException.offline), isNull);
    expect(
      retryOnlyConnectivity(0, const ApiException(kind: ApiErrorKind.api, code: 'forbidden', message: 'x')),
      isNull,
    );
  });
}
