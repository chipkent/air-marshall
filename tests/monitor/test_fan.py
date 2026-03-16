"""Tests for air_marshall.monitor.fan."""

from datetime import UTC
from unittest.mock import MagicMock, patch

import pytest

from air_marshall.monitor.fan import AutomationHatFanReader


def _make_mock(read_value: object) -> MagicMock:
    """Build a minimal mock automationhat module."""
    mock = MagicMock()
    mock.input.__getitem__.return_value.read.return_value = read_value
    return mock


class TestAutomationHatFanReaderInit:
    """Tests for AutomationHatFanReader.__init__."""

    def test_rejects_input_number_zero(self) -> None:
        """input_number=0 raises ValueError."""
        with pytest.raises(ValueError):
            AutomationHatFanReader(input_number=0)

    def test_rejects_input_number_four(self) -> None:
        """input_number=4 raises ValueError."""
        with pytest.raises(ValueError):
            AutomationHatFanReader(input_number=4)

    def test_accepts_boundary_values(self) -> None:
        """input_number=1 and input_number=3 do not raise."""
        AutomationHatFanReader(input_number=1)
        AutomationHatFanReader(input_number=3)


class TestAutomationHatFanReaderRead:
    """Tests for AutomationHatFanReader.read."""

    def test_is_on_true_when_truthy(self) -> None:
        """read() returns is_on=True when digital input returns a truthy value."""
        with patch("air_marshall.monitor.fan.automationhat", _make_mock(1)):
            assert AutomationHatFanReader(input_number=1).read().is_on is True

    def test_is_on_false_when_falsy(self) -> None:
        """read() returns is_on=False when digital input returns a falsy value."""
        with patch("air_marshall.monitor.fan.automationhat", _make_mock(0)):
            assert AutomationHatFanReader(input_number=1).read().is_on is False

    def test_timestamp_is_timezone_aware_utc(self) -> None:
        """read() sets timestamp to a timezone-aware UTC datetime."""
        with patch("air_marshall.monitor.fan.automationhat", _make_mock(0)):
            record = AutomationHatFanReader(input_number=1).read()
        assert record.timestamp.tzinfo == UTC

    def test_input_number_selects_correct_index(self) -> None:
        """input_number=2 causes __getitem__ to be called with index 1."""
        mock = _make_mock(0)
        with patch("air_marshall.monitor.fan.automationhat", mock):
            AutomationHatFanReader(input_number=2).read()
        mock.input.__getitem__.assert_called_once_with(1)

    def test_raises_when_automationhat_unavailable(self) -> None:
        """read() raises ImportError when automationhat is not installed."""
        with patch("air_marshall.monitor.fan.automationhat", None):
            with pytest.raises(ImportError):
                AutomationHatFanReader(input_number=1).read()
