"""Automation HAT digital input fan state reader."""

from datetime import UTC, datetime

from air_marshall.api.models import FanRecord

# automationhat requires RPi-specific hardware libraries (spidev) that cannot be
# installed in dev or CI environments. The standard Python pattern for an optional
# hardware dependency is to attempt the import at module load time and fall back to
# None. AutomationHatFanReader.read() raises ImportError fast if called without
# the library present, rather than failing silently.
try:
    import automationhat
except ImportError:
    automationhat = None

_MIN_INPUT_NUMBER: int = 1
"""Minimum valid board-labeled digital input number."""

_MAX_INPUT_NUMBER: int = 3
"""Maximum valid board-labeled digital input number."""


class AutomationHatFanReader:
    """Reads fan on/off state from an Automation HAT digital input.

    Args:
        input_number: Digital input number as labelled on the board (1–3).

    Raises:
        ValueError: If ``input_number`` is not in the range 1–3.
    """

    def __init__(self, input_number: int) -> None:
        if not (_MIN_INPUT_NUMBER <= input_number <= _MAX_INPUT_NUMBER):
            raise ValueError(
                f"input_number must be between {_MIN_INPUT_NUMBER} and {_MAX_INPUT_NUMBER}, got {input_number}"
            )
        self._input_number = input_number

    def read(self) -> FanRecord:
        """Read the current fan state from the configured digital input.

        Returns:
            A FanRecord with ``timestamp`` set to the current UTC time.

        Raises:
            ImportError: If automationhat is not installed.
        """
        if automationhat is None:
            raise ImportError(
                "automationhat is not installed; run on the monitor Raspberry Pi."
            )
        value = automationhat.input[self._input_number - 1].read()
        return FanRecord(
            timestamp=datetime.now(UTC),
            is_on=bool(value),
        )
