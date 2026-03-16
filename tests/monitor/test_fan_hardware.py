"""Hardware tests for AutomationHatFanReader — requires Automation HAT attached."""

import pytest

from air_marshall.monitor.fan import AutomationHatFanReader


@pytest.mark.hardware
def test_fan_reader_returns_valid_record() -> None:
    reader = AutomationHatFanReader(input_number=1)
    record = reader.read()
    assert isinstance(record.is_on, bool)
