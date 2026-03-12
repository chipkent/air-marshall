import 'dart:convert';

import 'package:http/http.dart' as http;

import 'models.dart';

/// A typed HTTP client for communicating with the air-marshall backend.
///
/// All requests include an `X-API-Key` header for authentication.
/// Non-2xx responses raise an [http.ClientException].
///
/// Example:
/// ```dart
/// final client = ApiClient(
///   baseUrl: 'http://rpi-controller.local:8000',
///   apiKey: 'secret',
/// );
/// final latest = await client.getLatest();
/// client.close();
/// ```
class ApiClient {
  /// The base URL of the air-marshall backend, e.g. `http://rpi.local:8000`.
  ///
  /// Any trailing slash supplied at construction time is stripped.
  final String baseUrl;

  /// The API key sent in every request via the `X-API-Key` header.
  final String apiKey;

  final http.Client _client;

  /// HTTP headers sent with every request, including the `X-API-Key` and
  /// `Content-Type` values derived from construction-time parameters.
  final Map<String, String> _headers;

  /// Supply [client] to inject a test double; a default [http.Client] is used
  /// when omitted.
  ApiClient({
    required String baseUrl,
    required this.apiKey,
    http.Client? client,
  }) : baseUrl = baseUrl.endsWith('/')
           ? baseUrl.substring(0, baseUrl.length - 1)
           : baseUrl,
       _client = client ?? http.Client(),
       _headers = {'Content-Type': 'application/json', 'X-API-Key': apiKey};

  /// Throws [http.ClientException] when [response] has a non-2xx status code.
  void _checkResponse(http.Response response) {
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw http.ClientException(
        'Request failed with status ${response.statusCode}: ${response.body}',
      );
    }
  }

  /// POSTs [body] as JSON to [path] relative to [baseUrl].
  ///
  /// Throws [http.ClientException] on a non-2xx response.
  Future<void> _post(String path, Map<String, dynamic> body) async {
    final response = await _client.post(
      Uri.parse('$baseUrl$path'),
      headers: _headers,
      body: jsonEncode(body),
    );
    _checkResponse(response);
  }

  /// Posts a [HumidityRecord] to `/data/humidity`.
  ///
  /// Throws [http.ClientException] on a non-2xx response.
  Future<void> postHumidity(HumidityRecord record) =>
      _post('/data/humidity', record.toJson());

  /// Posts a [FanRecord] to `/data/fan`.
  ///
  /// Throws [http.ClientException] on a non-2xx response.
  Future<void> postFan(FanRecord record) => _post('/data/fan', record.toJson());

  /// Posts a [ControlRecord] to `/data/control`.
  ///
  /// Throws [http.ClientException] on a non-2xx response.
  Future<void> postControl(ControlRecord record) =>
      _post('/data/control', record.toJson());

  /// Posts a [ConfigRecord] to `/data/config`.
  ///
  /// Throws [http.ClientException] on a non-2xx response.
  Future<void> postConfig(ConfigRecord record) =>
      _post('/data/config', record.toJson());

  /// Fetches the most recent record for each data category from `/data/latest`.
  ///
  /// If [sensorId] is provided it is forwarded as the `sensor_id` query
  /// parameter so the backend can filter humidity records by sensor.
  ///
  /// Throws [http.ClientException] on a non-2xx response.
  Future<LatestResponse> getLatest({String? sensorId}) async {
    final uri = Uri.parse('$baseUrl/data/latest').replace(
      queryParameters: sensorId != null ? {'sensor_id': sensorId} : null,
    );
    final response = await _client.get(uri, headers: _headers);
    _checkResponse(response);
    return LatestResponse.fromJson(
      jsonDecode(response.body) as Map<String, dynamic>,
    );
  }

  /// Fetches historical records for all data categories from `/data/history`.
  ///
  /// Throws [http.ClientException] on a non-2xx response.
  Future<HistoryResponse> getHistory() async {
    final response = await _client.get(
      Uri.parse('$baseUrl/data/history'),
      headers: _headers,
    );
    _checkResponse(response);
    return HistoryResponse.fromJson(
      jsonDecode(response.body) as Map<String, dynamic>,
    );
  }

  /// Releases resources held by the underlying [http.Client].
  ///
  /// After calling [close] this instance must not be used again.
  void close() => _client.close();
}
