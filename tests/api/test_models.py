"""Tests for air_marshall.api.models."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from air_marshall.api.models import (
    ControlRecord,
    FanRecord,
    HistoryResponse,
    HumidityRecord,
    LatestResponse,
)

_TS = datetime(2024, 6, 1, 12, 0, 0, tzinfo=UTC)


class TestHumidityRecord:
    """Tests for HumidityRecord."""

    def test_valid_construction(self) -> None:
        """HumidityRecord accepts all valid fields."""
        r = HumidityRecord(
            sensor_id="s1",
            sensor_serial_number="SN001",
            timestamp=_TS,
            temperature=22.5,
            humidity=45.0,
            is_touched=False,
        )
        assert r.sensor_id == "s1"
        assert r.humidity == 45.0
        assert r.is_touched is False

    def test_accepts_string_timestamp(self) -> None:
        """HumidityRecord accepts an ISO 8601 string for timestamp (JSON ingestion)."""
        r = HumidityRecord(
            sensor_id="s1",
            sensor_serial_number="SN001",
            timestamp="2024-06-01T12:00:00+00:00",  # type: ignore[arg-type]
            temperature=22.5,
            humidity=45.0,
            is_touched=False,
        )
        assert r.timestamp == _TS

    def test_strict_bool_rejects_string(self) -> None:
        """StrictBool rejects a string where bool is expected."""
        with pytest.raises(ValidationError):
            HumidityRecord(
                sensor_id="s1",
                sensor_serial_number="SN001",
                timestamp=_TS,
                temperature=22.5,
                humidity=45.0,
                is_touched="true",  # type: ignore[arg-type]
            )

    def test_strict_bool_rejects_int(self) -> None:
        """StrictBool rejects an integer where bool is expected."""
        with pytest.raises(ValidationError):
            HumidityRecord(
                sensor_id="s1",
                sensor_serial_number="SN001",
                timestamp=_TS,
                temperature=22.5,
                humidity=45.0,
                is_touched=1,  # type: ignore[arg-type]
            )

    def test_strict_float_rejects_string(self) -> None:
        """StrictFloat rejects a string where float is expected."""
        with pytest.raises(ValidationError):
            HumidityRecord(
                sensor_id="s1",
                sensor_serial_number="SN001",
                timestamp=_TS,
                temperature="22.5",  # type: ignore[arg-type]
                humidity=45.0,
                is_touched=False,
            )


class TestFanRecord:
    """Tests for FanRecord."""

    def test_valid_construction(self) -> None:
        """FanRecord accepts all valid fields."""
        r = FanRecord(timestamp=_TS, is_on=True)
        assert r.is_on is True

    def test_strict_bool_rejects_int(self) -> None:
        """StrictBool rejects an integer where bool is expected."""
        with pytest.raises(ValidationError):
            FanRecord(timestamp=_TS, is_on=1)  # type: ignore[arg-type]

    def test_strict_bool_rejects_string(self) -> None:
        """StrictBool rejects a string where bool is expected."""
        with pytest.raises(ValidationError):
            FanRecord(timestamp=_TS, is_on="yes")  # type: ignore[arg-type]


class TestControlRecord:
    """Tests for ControlRecord."""

    def test_valid_construction(self) -> None:
        """ControlRecord accepts all valid fields."""
        r = ControlRecord(timestamp=_TS, humidifier_on=False, fan_on=True)
        assert r.humidifier_on is False
        assert r.fan_on is True

    def test_strict_bool_rejects_int(self) -> None:
        """StrictBool rejects integers for both bool fields."""
        with pytest.raises(ValidationError):
            ControlRecord(timestamp=_TS, humidifier_on=0, fan_on=1)  # type: ignore[arg-type]


class TestLatestResponse:
    """Tests for LatestResponse."""

    def test_defaults(self) -> None:
        """LatestResponse humidity defaults to empty list; fan and control default to None."""
        r = LatestResponse()
        assert r.humidity == []
        assert r.fan is None
        assert r.control is None

    def test_accepts_records(self) -> None:
        """LatestResponse accepts populated record fields."""
        fan = FanRecord(timestamp=_TS, is_on=False)
        humidity = [
            HumidityRecord(
                sensor_id="s1",
                sensor_serial_number="SN001",
                timestamp=_TS,
                temperature=22.5,
                humidity=45.0,
                is_touched=False,
            )
        ]
        r = LatestResponse(humidity=humidity, fan=fan)
        assert r.fan is fan
        assert len(r.humidity) == 1
        assert r.humidity[0].sensor_id == "s1"


class TestHistoryResponse:
    """Tests for HistoryResponse."""

    def test_defaults_to_empty_lists(self) -> None:
        """HistoryResponse fields default to empty lists."""
        r = HistoryResponse()
        assert r.humidity == []
        assert r.fan == []
        assert r.control == []

    def test_accepts_lists(self) -> None:
        """HistoryResponse accepts non-empty record lists."""
        fans = [FanRecord(timestamp=_TS, is_on=True)]
        r = HistoryResponse(fan=fans)
        assert len(r.fan) == 1
        assert r.humidity == []
