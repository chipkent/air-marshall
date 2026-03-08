import 'package:flutter_test/flutter_test.dart';
import 'package:air_marshall/src/models.dart';

void main() {
  // ---------------------------------------------------------------------------
  // Shared fixtures
  // ---------------------------------------------------------------------------

  final humidityJson = {
    'sensor_id': 'sensor1',
    'sensor_serial_number': 'SN001',
    'timestamp': '2024-01-01T00:00:00.000Z',
    'temperature': 22.5,
    'humidity': 45.0,
    'is_touched': false,
  };

  final humidityRecord = HumidityRecord(
    sensorId: 'sensor1',
    sensorSerialNumber: 'SN001',
    timestamp: DateTime.utc(2024, 1, 1),
    temperature: 22.5,
    humidity: 45.0,
    isTouched: false,
  );

  final fanJson = {'timestamp': '2024-01-01T00:00:00.000Z', 'is_on': true};
  final fanRecord = FanRecord(timestamp: DateTime.utc(2024, 1, 1), isOn: true);

  final controlJson = {
    'timestamp': '2024-01-01T00:00:00.000Z',
    'humidifier_on': true,
    'fan_on': false,
  };
  final controlRecord = ControlRecord(
    timestamp: DateTime.utc(2024, 1, 1),
    humidifierOn: true,
    fanOn: false,
  );

  // ---------------------------------------------------------------------------
  // HumidityRecord
  // ---------------------------------------------------------------------------

  group('HumidityRecord', () {
    test('fromJson/toJson round-trip', () {
      final record = HumidityRecord.fromJson(humidityJson);
      expect(record.sensorId, 'sensor1');
      expect(record.sensorSerialNumber, 'SN001');
      expect(record.temperature, 22.5);
      expect(record.humidity, 45.0);
      expect(record.isTouched, false);
      final roundTripped = HumidityRecord.fromJson(record.toJson());
      expect(roundTripped.sensorId, record.sensorId);
      expect(roundTripped.temperature, record.temperature);
    });

    test('== and hashCode are value-equal for identical data', () {
      final a = HumidityRecord.fromJson(humidityJson);
      final b = HumidityRecord.fromJson(humidityJson);
      expect(a, equals(b));
      expect(a.hashCode, equals(b.hashCode));
    });

    test('== returns false for different sensorId', () {
      final a = HumidityRecord.fromJson(humidityJson);
      final b = HumidityRecord.fromJson({
        ...humidityJson,
        'sensor_id': 'other',
      });
      expect(a, isNot(equals(b)));
    });

    test('toString contains field values', () {
      expect(humidityRecord.toString(), contains('sensor1'));
      expect(humidityRecord.toString(), contains('22.5'));
    });
  });

  // ---------------------------------------------------------------------------
  // FanRecord
  // ---------------------------------------------------------------------------

  group('FanRecord', () {
    test('fromJson/toJson round-trip', () {
      final record = FanRecord.fromJson(fanJson);
      expect(record.isOn, true);
      final rt = FanRecord.fromJson(record.toJson());
      expect(rt.isOn, record.isOn);
      expect(rt.timestamp, record.timestamp);
    });

    test('== and hashCode are value-equal for identical data', () {
      final a = FanRecord.fromJson(fanJson);
      final b = FanRecord.fromJson(fanJson);
      expect(a, equals(b));
      expect(a.hashCode, equals(b.hashCode));
    });

    test('== returns false for different isOn', () {
      final a = FanRecord.fromJson(fanJson);
      final b = FanRecord.fromJson({...fanJson, 'is_on': false});
      expect(a, isNot(equals(b)));
    });

    test('toString contains field values', () {
      expect(fanRecord.toString(), contains('true'));
    });
  });

  // ---------------------------------------------------------------------------
  // ControlRecord
  // ---------------------------------------------------------------------------

  group('ControlRecord', () {
    test('fromJson/toJson round-trip', () {
      final record = ControlRecord.fromJson(controlJson);
      expect(record.humidifierOn, true);
      expect(record.fanOn, false);
      final rt = ControlRecord.fromJson(record.toJson());
      expect(rt.humidifierOn, record.humidifierOn);
      expect(rt.fanOn, record.fanOn);
      expect(rt.timestamp, record.timestamp);
    });

    test('== and hashCode are value-equal for identical data', () {
      final a = ControlRecord.fromJson(controlJson);
      final b = ControlRecord.fromJson(controlJson);
      expect(a, equals(b));
      expect(a.hashCode, equals(b.hashCode));
    });

    test('== returns false for different fanOn', () {
      final a = ControlRecord.fromJson(controlJson);
      final b = ControlRecord.fromJson({...controlJson, 'fan_on': true});
      expect(a, isNot(equals(b)));
    });

    test('toString contains field values', () {
      expect(controlRecord.toString(), contains('true'));
      expect(controlRecord.toString(), contains('false'));
    });
  });

  // ---------------------------------------------------------------------------
  // LatestResponse
  // ---------------------------------------------------------------------------

  group('LatestResponse', () {
    test('empty humidity list and null fan/control when fields absent', () {
      final r = LatestResponse.fromJson({});
      expect(r.humidity, isEmpty);
      expect(r.fan, isNull);
      expect(r.control, isNull);
    });

    test('empty humidity list when humidity is empty array', () {
      final r = LatestResponse.fromJson({
        'humidity': [],
        'fan': null,
        'control': null,
      });
      expect(r.humidity, isEmpty);
      expect(r.fan, isNull);
      expect(r.control, isNull);
    });

    test('parses populated humidity list, fan, and control', () {
      final r = LatestResponse.fromJson({
        'humidity': [humidityJson],
        'fan': fanJson,
        'control': controlJson,
      });
      expect(r.humidity.length, 1);
      expect(r.humidity[0].sensorId, 'sensor1');
      expect(r.fan, isNotNull);
      expect(r.fan!.isOn, true);
      expect(r.control, isNotNull);
      expect(r.control!.humidifierOn, true);
    });

    test('toJson round-trip preserves all fields', () {
      final original = LatestResponse(
        humidity: [humidityRecord],
        fan: fanRecord,
        control: controlRecord,
      );
      final decoded = LatestResponse.fromJson(original.toJson());
      expect(decoded, equals(original));
    });

    test('toJson with empty/null fields produces correct keys', () {
      final r = const LatestResponse();
      final j = r.toJson();
      expect(j['humidity'], isEmpty);
      expect(j['fan'], isNull);
      expect(j['control'], isNull);
    });

    test('== and hashCode are value-equal for identical data', () {
      final a = LatestResponse(humidity: [humidityRecord], fan: fanRecord);
      final b = LatestResponse(humidity: [humidityRecord], fan: fanRecord);
      expect(a, equals(b));
      expect(a.hashCode, equals(b.hashCode));
    });

    test('toString contains class name', () {
      expect(const LatestResponse().toString(), contains('LatestResponse'));
    });
  });

  // ---------------------------------------------------------------------------
  // HistoryResponse
  // ---------------------------------------------------------------------------

  group('HistoryResponse', () {
    test('all lists empty by default', () {
      final r = HistoryResponse.fromJson({});
      expect(r.humidity, isEmpty);
      expect(r.fan, isEmpty);
      expect(r.control, isEmpty);
    });

    test('parses non-empty lists', () {
      final json = {
        'humidity': [humidityJson],
        'fan': [fanJson],
        'control': [controlJson],
      };
      final r = HistoryResponse.fromJson(json);
      expect(r.humidity.length, 1);
      expect(r.humidity[0].sensorId, 'sensor1');
      expect(r.fan.length, 1);
      expect(r.fan[0].isOn, true);
      expect(r.control.length, 1);
      expect(r.control[0].humidifierOn, true);
    });

    test('toJson round-trip preserves all lists', () {
      final original = HistoryResponse(
        humidity: [humidityRecord],
        fan: [fanRecord],
        control: [controlRecord],
      );
      final decoded = HistoryResponse.fromJson(original.toJson());
      expect(decoded, equals(original));
    });

    test('== and hashCode are value-equal for identical data', () {
      final a = HistoryResponse(humidity: [humidityRecord], fan: [fanRecord]);
      final b = HistoryResponse(humidity: [humidityRecord], fan: [fanRecord]);
      expect(a, equals(b));
      expect(a.hashCode, equals(b.hashCode));
    });

    test('toString contains class name', () {
      expect(const HistoryResponse().toString(), contains('HistoryResponse'));
    });
  });
}
