import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:air_marshall/src/client.dart';
import 'package:air_marshall/src/models.dart';

const baseUrl = 'http://localhost:8000';
const apiKey = 'test-key';

http.Response okResponse([Map<String, dynamic>? body]) => http.Response(
  jsonEncode(body ?? {'status': 'ok'}),
  201,
  headers: {'content-type': 'application/json'},
);

http.Response jsonResponse(Map<String, dynamic> body, [int status = 200]) =>
    http.Response(
      jsonEncode(body),
      status,
      headers: {'content-type': 'application/json'},
    );

void main() {
  late List<http.Request> captured;

  ApiClient makeClient(http.Response Function(http.Request) handler) {
    captured = [];
    final mock = MockClient((req) async {
      captured.add(req);
      return handler(req);
    });
    return ApiClient(baseUrl: baseUrl, apiKey: apiKey, client: mock);
  }

  final sampleHumidity = HumidityRecord(
    sensorId: 's1',
    sensorSerialNumber: 'SN001',
    timestamp: DateTime.utc(2024, 1, 1),
    temperature: 22.5,
    humidity: 45.0,
    isTouched: false,
  );

  final sampleFan = FanRecord(timestamp: DateTime.utc(2024, 1, 1), isOn: true);

  final sampleControl = ControlRecord(
    timestamp: DateTime.utc(2024, 1, 1),
    humidifierOn: true,
    fanOn: false,
  );

  // ---------------------------------------------------------------------------
  // postHumidity
  // ---------------------------------------------------------------------------

  group('postHumidity', () {
    test(
      'sends POST to /data/humidity with correct headers and body',
      () async {
        final client = makeClient((_) => okResponse());
        await client.postHumidity(sampleHumidity);
        expect(captured.length, 1);
        expect(captured[0].method, 'POST');
        expect(captured[0].url.path, '/data/humidity');
        expect(captured[0].headers['X-API-Key'], apiKey);
        expect(
          captured[0].headers['Content-Type'],
          contains('application/json'),
        );
        final body = jsonDecode(captured[0].body) as Map<String, dynamic>;
        expect(body['sensor_id'], 's1');
        client.close();
      },
    );

    test('throws on non-2xx response', () async {
      final client = makeClient((_) => http.Response('error', 401));
      expect(
        () => client.postHumidity(sampleHumidity),
        throwsA(isA<http.ClientException>()),
      );
      client.close();
    });
  });

  // ---------------------------------------------------------------------------
  // postFan
  // ---------------------------------------------------------------------------

  group('postFan', () {
    test('sends POST to /data/fan with correct headers and body', () async {
      final client = makeClient((_) => okResponse());
      await client.postFan(sampleFan);
      expect(captured.length, 1);
      expect(captured[0].method, 'POST');
      expect(captured[0].url.path, '/data/fan');
      expect(captured[0].headers['X-API-Key'], apiKey);
      final body = jsonDecode(captured[0].body) as Map<String, dynamic>;
      expect(body['is_on'], true);
      client.close();
    });

    test('throws on non-2xx response', () async {
      final client = makeClient((_) => http.Response('error', 500));
      expect(
        () => client.postFan(sampleFan),
        throwsA(isA<http.ClientException>()),
      );
      client.close();
    });
  });

  // ---------------------------------------------------------------------------
  // postControl
  // ---------------------------------------------------------------------------

  group('postControl', () {
    test('sends POST to /data/control with correct headers and body', () async {
      final client = makeClient((_) => okResponse());
      await client.postControl(sampleControl);
      expect(captured.length, 1);
      expect(captured[0].method, 'POST');
      expect(captured[0].url.path, '/data/control');
      expect(captured[0].headers['X-API-Key'], apiKey);
      final body = jsonDecode(captured[0].body) as Map<String, dynamic>;
      expect(body['humidifier_on'], true);
      expect(body['fan_on'], false);
      client.close();
    });

    test('throws on non-2xx response', () async {
      final client = makeClient((_) => http.Response('error', 403));
      expect(
        () => client.postControl(sampleControl),
        throwsA(isA<http.ClientException>()),
      );
      client.close();
    });
  });

  // ---------------------------------------------------------------------------
  // getLatest
  // ---------------------------------------------------------------------------

  group('getLatest', () {
    test(
      'sends GET to /data/latest and returns empty-humidity response',
      () async {
        final responseBody = {'humidity': [], 'fan': null, 'control': null};
        final client = makeClient((_) => jsonResponse(responseBody));
        final result = await client.getLatest();
        expect(result.humidity, isEmpty);
        expect(result.fan, isNull);
        expect(captured[0].method, 'GET');
        expect(captured[0].url.path, '/data/latest');
        client.close();
      },
    );

    test('parses populated LatestResponse', () async {
      final responseBody = {
        'humidity': [sampleHumidity.toJson()],
        'fan': sampleFan.toJson(),
        'control': sampleControl.toJson(),
      };
      final client = makeClient((_) => jsonResponse(responseBody));
      final result = await client.getLatest();
      expect(result.humidity.length, 1);
      expect(result.humidity[0].sensorId, 's1');
      expect(result.fan, isNotNull);
      expect(result.fan!.isOn, true);
      expect(result.control, isNotNull);
      expect(result.control!.humidifierOn, true);
      client.close();
    });

    test('includes sensor_id query parameter when provided', () async {
      final responseBody = {'humidity': [], 'fan': null, 'control': null};
      final client = makeClient((_) => jsonResponse(responseBody));
      await client.getLatest(sensorId: 'sensor1');
      expect(captured[0].url.queryParameters['sensor_id'], 'sensor1');
      client.close();
    });

    test('throws on non-2xx response', () async {
      final client = makeClient((_) => http.Response('error', 503));
      expect(() => client.getLatest(), throwsA(isA<http.ClientException>()));
      client.close();
    });
  });

  // ---------------------------------------------------------------------------
  // getHistory
  // ---------------------------------------------------------------------------

  group('getHistory', () {
    test('sends GET to /data/history and returns empty lists', () async {
      final responseBody = {'humidity': [], 'fan': [], 'control': []};
      final client = makeClient((_) => jsonResponse(responseBody));
      final result = await client.getHistory();
      expect(result.humidity, isEmpty);
      expect(result.fan, isEmpty);
      expect(result.control, isEmpty);
      expect(captured[0].url.path, '/data/history');
      client.close();
    });

    test('parses populated HistoryResponse', () async {
      final responseBody = {
        'humidity': [sampleHumidity.toJson()],
        'fan': [sampleFan.toJson()],
        'control': [sampleControl.toJson()],
      };
      final client = makeClient((_) => jsonResponse(responseBody));
      final result = await client.getHistory();
      expect(result.humidity.length, 1);
      expect(result.humidity[0].sensorId, 's1');
      expect(result.fan.length, 1);
      expect(result.fan[0].isOn, true);
      expect(result.control.length, 1);
      expect(result.control[0].fanOn, false);
      client.close();
    });

    test('throws on non-2xx response', () async {
      final client = makeClient((_) => http.Response('error', 500));
      expect(() => client.getHistory(), throwsA(isA<http.ClientException>()));
      client.close();
    });
  });

  // ---------------------------------------------------------------------------
  // close
  // ---------------------------------------------------------------------------

  group('close', () {
    test('closes the underlying client without throwing', () {
      final client = makeClient((_) => okResponse());
      client.close();
    });
  });
}
