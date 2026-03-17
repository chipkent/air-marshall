"""Hardware tests for SHT45Reader — requires SHT45 Trinkey attached via USB serial."""

import os

import pytest

from air_marshall.monitor.humidity import SHT45Reader


@pytest.mark.hardware
def test_sht45_reader_returns_valid_record() -> None:
    port = os.environ.get("HARDWARE_SERIAL_PORT", "/dev/ttyACM0")
    with SHT45Reader(port=port, sensor_id="hw-test") as reader:
        record = reader.read()
    assert record.sensor_id == "hw-test"
    assert isinstance(record.sensor_serial_number, str)
    assert -40.0 <= record.temperature <= 85.0
    assert 0.0 <= record.humidity <= 100.0
    assert isinstance(record.is_touched, bool)
