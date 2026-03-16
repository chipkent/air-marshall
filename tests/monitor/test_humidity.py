"""Tests for air_marshall.monitor.humidity."""

from datetime import UTC
from unittest.mock import MagicMock

import pytest

from air_marshall.monitor.humidity import BAUD_RATE, SHT45Reader


def _make_serial(line: str) -> MagicMock:
    mock = MagicMock()
    mock.readline.return_value = line.encode()
    return mock


class TestBaudRate:
    """Tests for the BAUD_RATE module constant."""

    def test_baud_rate_value(self) -> None:
        """BAUD_RATE is 9600."""
        assert BAUD_RATE == 9600


class TestSHT45ReaderRead:
    """Tests for SHT45Reader.read."""

    def test_parses_temperature(self) -> None:
        """read() returns temperature parsed from the first CSV field."""
        serial = _make_serial("22.5,45.0,0,ABCD1234\n")
        reader = SHT45Reader(port="/dev/ttyACM0", sensor_id="s1", serial_port=serial)
        record = reader.read()
        assert record.temperature == 22.5

    def test_parses_humidity(self) -> None:
        """read() returns humidity parsed from the second CSV field."""
        serial = _make_serial("22.5,45.0,0,ABCD1234\n")
        reader = SHT45Reader(port="/dev/ttyACM0", sensor_id="s1", serial_port=serial)
        record = reader.read()
        assert record.humidity == 45.0

    def test_sensor_id_from_constructor(self) -> None:
        """read() populates sensor_id from the constructor argument."""
        serial = _make_serial("22.5,45.0,0,ABCD1234\n")
        reader = SHT45Reader(
            port="/dev/ttyACM0", sensor_id="living-room", serial_port=serial
        )
        record = reader.read()
        assert record.sensor_id == "living-room"

    def test_sensor_serial_number_from_csv(self) -> None:
        """read() populates sensor_serial_number from the fourth CSV field."""
        serial = _make_serial("22.5,45.0,0,DEADBEEF\n")
        reader = SHT45Reader(port="/dev/ttyACM0", sensor_id="s1", serial_port=serial)
        record = reader.read()
        assert record.sensor_serial_number == "DEADBEEF"

    def test_is_touched_false_when_zero(self) -> None:
        """read() converts CSV '0' in the third field to is_touched=False."""
        serial = _make_serial("22.5,45.0,0,ABCD1234\n")
        reader = SHT45Reader(port="/dev/ttyACM0", sensor_id="s1", serial_port=serial)
        record = reader.read()
        assert record.is_touched is False

    def test_is_touched_true_when_one(self) -> None:
        """read() converts CSV '1' in the third field to is_touched=True."""
        serial = _make_serial("22.5,45.0,1,ABCD1234\n")
        reader = SHT45Reader(port="/dev/ttyACM0", sensor_id="s1", serial_port=serial)
        record = reader.read()
        assert record.is_touched is True

    def test_raises_value_error_on_short_csv(self) -> None:
        """read() raises ValueError when the CSV line has fewer than 4 fields."""
        serial = _make_serial("22.5,45.0\n")
        reader = SHT45Reader(port="/dev/ttyACM0", sensor_id="s1", serial_port=serial)
        with pytest.raises(ValueError, match="Cannot parse CSV line"):
            reader.read()

    def test_raises_value_error_on_non_numeric_field(self) -> None:
        """read() raises ValueError when a numeric field cannot be parsed."""
        serial = _make_serial("bad,45.0,0,ABCD1234\n")
        reader = SHT45Reader(port="/dev/ttyACM0", sensor_id="s1", serial_port=serial)
        with pytest.raises(ValueError, match="Cannot parse CSV line"):
            reader.read()

    def test_timestamp_is_utc(self) -> None:
        """read() sets timestamp to a timezone-aware UTC datetime."""
        serial = _make_serial("22.5,45.0,0,ABCD1234\n")
        reader = SHT45Reader(port="/dev/ttyACM0", sensor_id="s1", serial_port=serial)
        record = reader.read()
        assert record.timestamp.tzinfo is not None
        assert record.timestamp.tzinfo == UTC


class TestSHT45ReaderClose:
    """Tests for SHT45Reader.close."""

    def test_close_calls_serial_close(self) -> None:
        """close() closes the underlying serial port."""
        serial = _make_serial("22.5,45.0,0,ABCD1234\n")
        reader = SHT45Reader(port="/dev/ttyACM0", sensor_id="s1", serial_port=serial)
        reader.close()
        serial.close.assert_called_once()


class TestSHT45ReaderContextManager:
    """Tests for SHT45Reader context manager protocol."""

    def test_context_manager_closes_port(self) -> None:
        """Exiting the context manager closes the serial port."""
        serial = _make_serial("22.5,45.0,0,ABCD1234\n")
        reader = SHT45Reader(port="/dev/ttyACM0", sensor_id="s1", serial_port=serial)
        with reader:
            pass
        serial.close.assert_called_once()

    def test_context_manager_returns_reader(self) -> None:
        """The context manager yields the SHT45Reader itself."""
        serial = _make_serial("22.5,45.0,0,ABCD1234\n")
        reader = SHT45Reader(port="/dev/ttyACM0", sensor_id="s1", serial_port=serial)
        with reader as r:
            assert r is reader

    def test_context_manager_closes_on_exception(self) -> None:
        """The serial port is closed even when the body raises."""
        serial = _make_serial("22.5,45.0,0,ABCD1234\n")
        reader = SHT45Reader(port="/dev/ttyACM0", sensor_id="s1", serial_port=serial)
        with pytest.raises(RuntimeError):
            with reader:
                raise RuntimeError("test")
        serial.close.assert_called_once()


class TestSHT45ReaderInit:
    """Tests for SHT45Reader.__init__."""

    def test_opens_serial_port_when_not_injected(self) -> None:
        """Constructor opens a serial port when none is injected."""
        mock_serial_cls = MagicMock()
        mock_instance = MagicMock()
        mock_serial_cls.return_value = mock_instance

        import serial

        original = serial.Serial
        serial.Serial = mock_serial_cls  # type: ignore[assignment]
        try:
            reader = SHT45Reader(port="/dev/ttyACM0", sensor_id="s1")
            assert reader._serial is mock_instance
            mock_serial_cls.assert_called_once_with("/dev/ttyACM0", BAUD_RATE)
        finally:
            serial.Serial = original  # type: ignore[assignment]
