/// Integration tests for [ApiClient] against a live air-marshall DB server.
///
/// These tests require a running instance of the air-marshall database service.
/// Configure the server address and API key via environment variables:
///
/// ```
/// INTEGRATION_TEST_BASE_URL=http://127.0.0.1:18888
/// INTEGRATION_TEST_API_KEY=test-key
/// ```
///
/// If the server is not reachable, all tests are skipped automatically.
/// Run with: `flutter test --tags integration`
// ignore_for_file: avoid_print
@Tags(['integration'])
library;

import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:air_marshall/src/client.dart';
import 'package:air_marshall/src/models.dart';

void main() {
  final baseUrl =
      Platform.environment['INTEGRATION_TEST_BASE_URL'] ??
      'http://127.0.0.1:18888';
  final apiKey = Platform.environment['INTEGRATION_TEST_API_KEY'] ?? 'test-key';

  final ts = DateTime.now().toUtc();

  var serverReachable = false;

  setUpAll(() async {
    print('[setUpAll] checking server at $baseUrl');
    try {
      final client = http.Client();
      final response = await client
          .get(
            Uri.parse('$baseUrl/data/latest'),
            headers: {'X-API-Key': apiKey},
          )
          .timeout(const Duration(seconds: 5));
      client.close();
      serverReachable = response.statusCode < 500;
      print(
        '[setUpAll] server status: ${response.statusCode}, reachable=$serverReachable',
      );
    } catch (e) {
      print('[setUpAll] server check failed: $e');
      serverReachable = false;
    }
  });

  setUp(() {
    if (!serverReachable) {
      print('[setUp] skipping — server not reachable');
      markTestSkipped('DB server not reachable at $baseUrl');
    } else {
      print('[setUp] server reachable, running test');
    }
  });

  // ---------------------------------------------------------------------------
  // postHumidity → getLatest
  // ---------------------------------------------------------------------------

  test('postHumidity then getLatest contains the record', () async {
    final client = ApiClient(baseUrl: baseUrl, apiKey: apiKey);
    addTearDown(client.close);

    final record = HumidityRecord(
      sensorId: 's_hum_1',
      sensorSerialNumber: 'SN_HUM_1',
      timestamp: ts,
      temperature: 21.0,
      humidity: 48.0,
      isTouched: false,
    );
    await client.postHumidity(record);

    final latest = await client.getLatest(sensorId: 's_hum_1');
    expect(latest.humidity, isNotEmpty);
    expect(latest.humidity.first.sensorId, 's_hum_1');
    expect(latest.humidity.first.humidity, 48.0);
  });

  // ---------------------------------------------------------------------------
  // postFan → getLatest
  // ---------------------------------------------------------------------------

  test('postFan then getLatest has fan populated', () async {
    final client = ApiClient(baseUrl: baseUrl, apiKey: apiKey);
    addTearDown(client.close);

    final record = FanRecord(timestamp: ts, isOn: true);
    await client.postFan(record);

    final latest = await client.getLatest();
    expect(latest.fan, isNotNull);
    expect(latest.fan!.isOn, isTrue);
  });

  // ---------------------------------------------------------------------------
  // postControl → getLatest
  // ---------------------------------------------------------------------------

  test('postControl then getLatest has control populated', () async {
    final client = ApiClient(baseUrl: baseUrl, apiKey: apiKey);
    addTearDown(client.close);

    final record = ControlRecord(
      timestamp: ts,
      humidifierOn: true,
      fanOn: false,
    );
    await client.postControl(record);

    final latest = await client.getLatest();
    expect(latest.control, isNotNull);
    expect(latest.control!.humidifierOn, isTrue);
    expect(latest.control!.fanOn, isFalse);
  });

  // ---------------------------------------------------------------------------
  // postConfig → getLatest
  // ---------------------------------------------------------------------------

  test('postConfig then getLatest has config populated', () async {
    final client = ApiClient(baseUrl: baseUrl, apiKey: apiKey);
    addTearDown(client.close);

    final record = ConfigRecord(
      timestamp: ts,
      humidityLow: 30.0,
      humidityHigh: 50.0,
    );
    await client.postConfig(record);

    final latest = await client.getLatest();
    expect(latest.config, isNotNull);
    expect(latest.config!.humidityLow, 30.0);
    expect(latest.config!.humidityHigh, 50.0);
  });

  // ---------------------------------------------------------------------------
  // Multi-sensor: post s_ms_1 + s_ms_2 → getLatest returns 2 records
  // ---------------------------------------------------------------------------

  test('multi-sensor getLatest returns one record per sensor', () async {
    final client = ApiClient(baseUrl: baseUrl, apiKey: apiKey);
    addTearDown(client.close);

    await client.postHumidity(
      HumidityRecord(
        sensorId: 's_ms_1',
        sensorSerialNumber: 'SN_MS_1',
        timestamp: ts,
        temperature: 20.0,
        humidity: 45.0,
        isTouched: false,
      ),
    );
    await client.postHumidity(
      HumidityRecord(
        sensorId: 's_ms_2',
        sensorSerialNumber: 'SN_MS_2',
        timestamp: ts,
        temperature: 22.0,
        humidity: 55.0,
        isTouched: false,
      ),
    );

    final latest = await client.getLatest();
    final sensorIds = latest.humidity.map((r) => r.sensorId).toSet();
    expect(sensorIds, containsAll(['s_ms_1', 's_ms_2']));
  });

  // ---------------------------------------------------------------------------
  // getHistory after post
  // ---------------------------------------------------------------------------

  test('getHistory contains recently posted humidity record', () async {
    final client = ApiClient(baseUrl: baseUrl, apiKey: apiKey);
    addTearDown(client.close);

    await client.postHumidity(
      HumidityRecord(
        sensorId: 's_hist_1',
        sensorSerialNumber: 'SN_HIST_1',
        timestamp: ts,
        temperature: 23.0,
        humidity: 60.0,
        isTouched: false,
      ),
    );

    final history = await client.getHistory();
    expect(history.humidity.any((r) => r.sensorId == 's_hist_1'), isTrue);
  });

  // ---------------------------------------------------------------------------
  // Wrong API key throws ClientException
  // ---------------------------------------------------------------------------

  test('wrong API key throws ClientException', () async {
    final client = ApiClient(baseUrl: baseUrl, apiKey: 'wrong-key');
    addTearDown(client.close);

    await expectLater(client.getLatest(), throwsA(isA<http.ClientException>()));
  });

  // ---------------------------------------------------------------------------
  // getLatest with sensorId filter
  // ---------------------------------------------------------------------------

  test('getLatest with sensorId filter returns only matching sensor', () async {
    final client = ApiClient(baseUrl: baseUrl, apiKey: apiKey);
    addTearDown(client.close);

    await client.postHumidity(
      HumidityRecord(
        sensorId: 's_filt_1',
        sensorSerialNumber: 'SN_FILT_1',
        timestamp: ts,
        temperature: 21.5,
        humidity: 47.0,
        isTouched: false,
      ),
    );
    await client.postHumidity(
      HumidityRecord(
        sensorId: 's_filt_2',
        sensorSerialNumber: 'SN_FILT_2',
        timestamp: ts,
        temperature: 21.5,
        humidity: 47.0,
        isTouched: false,
      ),
    );

    final latest = await client.getLatest(sensorId: 's_filt_1');
    expect(latest.humidity.length, 1);
    expect(latest.humidity.first.sensorId, 's_filt_1');
  });
}
