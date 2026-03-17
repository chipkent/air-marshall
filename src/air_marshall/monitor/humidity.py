"""SHT45 Trinkey USB serial humidity/temperature reader."""

from datetime import UTC, datetime

import serial

from air_marshall.api.models import HumidityRecord

BAUD_RATE: int = 9600
"""Serial baud rate for the SHT45 Trinkey."""

READ_TIMEOUT: float = 5.0
"""Seconds to wait for a line from the Trinkey before raising TimeoutError."""


class SHT45Reader:
    """Reads humidity and temperature from an SHT45 Trinkey over USB serial.

    The SHT45 Trinkey CircuitPython firmware emits one CSV line per reading:
    ``<temperature_c>,<humidity_pct>,<is_touched_0_or_1>,<serial_number_hex>``.

    Args:
        port: Serial device path (e.g. ``/dev/ttyACM0``).
        sensor_id: Logical sensor identifier stored in each returned record.
        serial_port: Pre-opened serial connection; when omitted the port is
            opened by the constructor.
    """

    def __init__(
        self,
        port: str,
        sensor_id: str,
        serial_port: serial.Serial | None = None,
    ) -> None:
        self._sensor_id = sensor_id
        if serial_port is None:
            self._serial: serial.Serial = serial.Serial(
                port, BAUD_RATE, timeout=READ_TIMEOUT
            )
        else:
            self._serial = serial_port

    def read(self) -> HumidityRecord:
        """Read one CSV line and return a HumidityRecord.

        Returns:
            A record with ``timestamp`` set to the current UTC time and
            ``sensor_serial_number`` taken from the sensor's CSV output.

        Raises:
            TimeoutError: If no data is received within ``READ_TIMEOUT`` seconds.
            ValueError: If the CSV line cannot be parsed or has fewer than 4 fields.
        """
        line = self._serial.readline().decode().strip()
        if not line:
            raise TimeoutError("No data received from SHT45 Trinkey within timeout")
        parts = line.split(",")
        try:
            temperature = float(parts[0])
            humidity = float(parts[1])
            is_touched = bool(int(parts[2]))
            sensor_serial_number = parts[3]
        except (IndexError, ValueError) as exc:
            raise ValueError(f"Cannot parse CSV line: {line!r}") from exc
        return HumidityRecord(
            sensor_id=self._sensor_id,
            sensor_serial_number=sensor_serial_number,
            timestamp=datetime.now(UTC),
            temperature=temperature,
            humidity=humidity,
            is_touched=is_touched,
        )

    def close(self) -> None:
        """Close the underlying serial port."""
        self._serial.close()

    def __enter__(self) -> "SHT45Reader":
        """Enter the context manager."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Exit the context manager, closing the serial port."""
        self.close()
