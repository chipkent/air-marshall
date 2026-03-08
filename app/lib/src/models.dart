/// Data transfer objects for the air-marshall API.
///
/// Each model mirrors a corresponding Python model on the backend and
/// supports JSON serialization / deserialization using snake_case field names.
library;

import 'package:meta/meta.dart';

bool _listEquals<T>(List<T> a, List<T> b) {
  if (identical(a, b)) return true;
  if (a.length != b.length) return false;
  for (var i = 0; i < a.length; i++) {
    if (a[i] != b[i]) return false;
  }
  return true;
}

/// A single humidity and temperature measurement from a sensor.
@immutable
class HumidityRecord {
  /// Unique identifier for the sensor that produced this reading.
  final String sensorId;

  /// Hardware serial number of the sensor.
  final String sensorSerialNumber;

  /// UTC time at which the reading was captured.
  final DateTime timestamp;

  /// Ambient temperature in degrees Celsius.
  final double temperature;

  /// Relative humidity as a percentage (0–100).
  final double humidity;

  /// Whether the sensor's touch surface was active at the time of reading.
  final bool isTouched;

  const HumidityRecord({
    required this.sensorId,
    required this.sensorSerialNumber,
    required this.timestamp,
    required this.temperature,
    required this.humidity,
    required this.isTouched,
  });

  /// Deserializes a [HumidityRecord] from a JSON map with snake_case keys.
  factory HumidityRecord.fromJson(Map<String, dynamic> json) => HumidityRecord(
    sensorId: json['sensor_id'] as String,
    sensorSerialNumber: json['sensor_serial_number'] as String,
    timestamp: DateTime.parse(json['timestamp'] as String),
    temperature: (json['temperature'] as num).toDouble(),
    humidity: (json['humidity'] as num).toDouble(),
    isTouched: json['is_touched'] as bool,
  );

  /// Serializes this record to a JSON map with snake_case keys and ISO 8601 timestamps.
  Map<String, dynamic> toJson() => {
    'sensor_id': sensorId,
    'sensor_serial_number': sensorSerialNumber,
    'timestamp': timestamp.toIso8601String(),
    'temperature': temperature,
    'humidity': humidity,
    'is_touched': isTouched,
  };

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is HumidityRecord &&
          runtimeType == other.runtimeType &&
          sensorId == other.sensorId &&
          sensorSerialNumber == other.sensorSerialNumber &&
          timestamp == other.timestamp &&
          temperature == other.temperature &&
          humidity == other.humidity &&
          isTouched == other.isTouched;

  @override
  int get hashCode => Object.hash(
    sensorId,
    sensorSerialNumber,
    timestamp,
    temperature,
    humidity,
    isTouched,
  );

  @override
  String toString() =>
      'HumidityRecord(sensorId: $sensorId, sensorSerialNumber: $sensorSerialNumber, '
      'timestamp: $timestamp, temperature: $temperature, humidity: $humidity, '
      'isTouched: $isTouched)';
}

/// A single fan state record.
@immutable
class FanRecord {
  /// UTC time at which the fan state was recorded.
  final DateTime timestamp;

  /// Whether the fan was on at the time of recording.
  final bool isOn;

  const FanRecord({required this.timestamp, required this.isOn});

  /// Deserializes a [FanRecord] from a JSON map with snake_case keys.
  factory FanRecord.fromJson(Map<String, dynamic> json) => FanRecord(
    timestamp: DateTime.parse(json['timestamp'] as String),
    isOn: json['is_on'] as bool,
  );

  /// Serializes this record to a JSON map with snake_case keys and ISO 8601 timestamps.
  Map<String, dynamic> toJson() => {
    'timestamp': timestamp.toIso8601String(),
    'is_on': isOn,
  };

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is FanRecord &&
          runtimeType == other.runtimeType &&
          timestamp == other.timestamp &&
          isOn == other.isOn;

  @override
  int get hashCode => Object.hash(timestamp, isOn);

  @override
  String toString() => 'FanRecord(timestamp: $timestamp, isOn: $isOn)';
}

/// A single HVAC control state record.
@immutable
class ControlRecord {
  /// UTC time at which the control state was recorded.
  final DateTime timestamp;

  /// Whether the humidifier was on at the time of recording.
  final bool humidifierOn;

  /// Whether the fan was on at the time of recording.
  final bool fanOn;

  const ControlRecord({
    required this.timestamp,
    required this.humidifierOn,
    required this.fanOn,
  });

  /// Deserializes a [ControlRecord] from a JSON map with snake_case keys.
  factory ControlRecord.fromJson(Map<String, dynamic> json) => ControlRecord(
    timestamp: DateTime.parse(json['timestamp'] as String),
    humidifierOn: json['humidifier_on'] as bool,
    fanOn: json['fan_on'] as bool,
  );

  /// Serializes this record to a JSON map with snake_case keys and ISO 8601 timestamps.
  Map<String, dynamic> toJson() => {
    'timestamp': timestamp.toIso8601String(),
    'humidifier_on': humidifierOn,
    'fan_on': fanOn,
  };

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is ControlRecord &&
          runtimeType == other.runtimeType &&
          timestamp == other.timestamp &&
          humidifierOn == other.humidifierOn &&
          fanOn == other.fanOn;

  @override
  int get hashCode => Object.hash(timestamp, humidifierOn, fanOn);

  @override
  String toString() =>
      'ControlRecord(timestamp: $timestamp, humidifierOn: $humidifierOn, fanOn: $fanOn)';
}

/// The response payload from the `/data/latest` endpoint.
///
/// [humidity] contains the most recent reading from each known sensor (one
/// entry per sensor). [fan] and [control] are `null` when no record exists yet.
@immutable
class LatestResponse {
  /// Most recent humidity reading from each sensor; empty when no data exists.
  final List<HumidityRecord> humidity;

  /// Most recent fan state, or `null` if none has been recorded yet.
  final FanRecord? fan;

  /// Most recent HVAC control state, or `null` if none has been recorded yet.
  final ControlRecord? control;

  const LatestResponse({this.humidity = const [], this.fan, this.control});

  /// Deserializes a [LatestResponse] from a JSON map with snake_case keys.
  factory LatestResponse.fromJson(Map<String, dynamic> json) => LatestResponse(
    humidity:
        (json['humidity'] as List<dynamic>?)
            ?.map((e) => HumidityRecord.fromJson(e as Map<String, dynamic>))
            .toList() ??
        [],
    fan: json['fan'] != null
        ? FanRecord.fromJson(json['fan'] as Map<String, dynamic>)
        : null,
    control: json['control'] != null
        ? ControlRecord.fromJson(json['control'] as Map<String, dynamic>)
        : null,
  );

  /// Serializes this response to a JSON map with snake_case keys.
  Map<String, dynamic> toJson() => {
    'humidity': humidity.map((e) => e.toJson()).toList(),
    'fan': fan?.toJson(),
    'control': control?.toJson(),
  };

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is LatestResponse &&
          runtimeType == other.runtimeType &&
          _listEquals(humidity, other.humidity) &&
          fan == other.fan &&
          control == other.control;

  @override
  int get hashCode => Object.hash(Object.hashAll(humidity), fan, control);

  @override
  String toString() =>
      'LatestResponse(humidity: $humidity, fan: $fan, control: $control)';
}

/// The response payload from the `/data/history` endpoint.
///
/// Each list is ordered oldest-first.
@immutable
class HistoryResponse {
  /// Humidity records in ascending timestamp order.
  final List<HumidityRecord> humidity;

  /// Fan state records in ascending timestamp order.
  final List<FanRecord> fan;

  /// HVAC control state records in ascending timestamp order.
  final List<ControlRecord> control;

  const HistoryResponse({
    this.humidity = const [],
    this.fan = const [],
    this.control = const [],
  });

  /// Deserializes a [HistoryResponse] from a JSON map with snake_case keys.
  factory HistoryResponse.fromJson(Map<String, dynamic> json) =>
      HistoryResponse(
        humidity:
            (json['humidity'] as List<dynamic>?)
                ?.map((e) => HumidityRecord.fromJson(e as Map<String, dynamic>))
                .toList() ??
            [],
        fan:
            (json['fan'] as List<dynamic>?)
                ?.map((e) => FanRecord.fromJson(e as Map<String, dynamic>))
                .toList() ??
            [],
        control:
            (json['control'] as List<dynamic>?)
                ?.map((e) => ControlRecord.fromJson(e as Map<String, dynamic>))
                .toList() ??
            [],
      );

  /// Serializes this response to a JSON map with snake_case keys.
  Map<String, dynamic> toJson() => {
    'humidity': humidity.map((e) => e.toJson()).toList(),
    'fan': fan.map((e) => e.toJson()).toList(),
    'control': control.map((e) => e.toJson()).toList(),
  };

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is HistoryResponse &&
          runtimeType == other.runtimeType &&
          _listEquals(humidity, other.humidity) &&
          _listEquals(fan, other.fan) &&
          _listEquals(control, other.control);

  @override
  int get hashCode => Object.hash(
    Object.hashAll(humidity),
    Object.hashAll(fan),
    Object.hashAll(control),
  );

  @override
  String toString() =>
      'HistoryResponse(humidity: $humidity, fan: $fan, control: $control)';
}
