import 'package:dio/dio.dart';

/// {@template i_http_client}
/// Class for describing the interface of the HTTP request management service
/// {@endtemplate}
abstract interface class IHttpClient {
  static const name = 'IHttpClient';

  Future<Response> get(String path, {Object? data, Map<String, dynamic>? queryParameters, Options? options});

  Future<Response> post(String path, {Object? data, Map<String, dynamic>? queryParameters, Options? options});

  Future<Response> patch(String path, {Object? data, Map<String, dynamic>? queryParameters, Options? options});

  Future<Response> put(String path, {Object? data, Map<String, dynamic>? queryParameters, Options? options});

  Future<Response> delete(String path, {Object? data, Map<String, dynamic>? queryParameters, Options? options});
}
